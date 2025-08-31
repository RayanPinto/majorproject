import asyncio
import os
import json
import re
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

from manager.agent import state_manager_agent
from manager.sub_agents.conversational_agent import conversational_agent
from google.adk.runners import Runner
from pymongo import MongoClient
from google.adk.sessions import InMemorySessionService
from mongodb_session_service import MongoDBSessionService

from utils import add_user_query_to_history, call_agent_async
from manager.tools.tools import ingest_from_model_output, ensure_session_structures

# ===== ERROR HANDLING CLASSES =====

class StateManagementError(Exception):
    """Base exception for state management errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(StateManagementError):
    """Exception for validation errors"""
    def __init__(self, message: str, error_code: str = "VAL_001", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)

class JSONProcessingError(StateManagementError):
    """Exception for JSON processing errors"""
    def __init__(self, message: str, error_code: str = "JSON_001", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)

class StateUpdateError(StateManagementError):
    """Exception for state update errors"""
    def __init__(self, message: str, error_code: str = "STATE_001", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)

class DatabaseError(StateManagementError):
    """Exception for database errors"""
    def __init__(self, message: str, error_code: str = "DB_001", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)

class UserInputError(StateManagementError):
    """Exception for user input errors"""
    def __init__(self, message: str, error_code: str = "INPUT_001", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)

# ===== VALIDATION FUNCTIONS =====

def validate_json_structure(json_data: Dict[str, Any], template_keys: List[str]) -> Dict[str, Any]:
    """Validate JSON structure against template keys"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check for missing keys
    missing_keys = [key for key in template_keys if key not in json_data]
    if missing_keys:
        result["warnings"].append(f"Missing keys: {', '.join(missing_keys)}")
    
    # Check for extra keys
    extra_keys = [key for key in json_data.keys() if key not in template_keys]
    if extra_keys:
        result["warnings"].append(f"Extra keys found: {', '.join(extra_keys)}")
    
    # Check data types (all should be strings for this template)
    for key, value in json_data.items():
        if key in template_keys and not isinstance(value, (str, int, float, bool, type(None))):
            result["errors"].append(f"Invalid data type for {key}: expected string, got {type(value).__name__}")
            result["valid"] = False
    
    return result

def validate_user_input(user_input: str) -> Dict[str, Any]:
    """Validate user input for commands"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    if not user_input or not user_input.strip():
        result["valid"] = False
        result["errors"].append("Empty input")
        return result
    
    user_input = user_input.strip()
    
    # Check for JSON processing command
    if user_input.lower().startswith("process this json:"):
        json_part = user_input[len("process this json:"):].strip()
        if not json_part:
            result["valid"] = False
            result["errors"].append("No JSON data provided")
        else:
            try:
                # Try to parse as JSON
                json.loads(json_part)
            except json.JSONDecodeError as e:
                result["valid"] = False
                result["errors"].append(f"Invalid JSON format: {str(e)}")
    
    # Check for state update command
    elif user_input.lower().startswith("update state:"):
        update_part = user_input[len("update state:"):].strip()
        if not update_part:
            result["valid"] = False
            result["errors"].append("No update data provided")
        elif "=" not in update_part:
            result["valid"] = False
            result["errors"].append("Update format should be 'key=value'")
        else:
            # Check for empty key or value
            parts = update_part.split("=", 1)
            if len(parts) != 2:
                result["valid"] = False
                result["errors"].append("Update format should be 'key=value'")
            elif not parts[0].strip():
                result["valid"] = False
                result["errors"].append("Empty key in update command")
            elif not parts[1].strip():
                result["valid"] = False
                result["errors"].append("Empty value in update command")
            else:
                # Check for extra text after the value
                key = parts[0].strip()
                value_part = parts[1].strip()
                # Split by whitespace to check for extra text
                value_parts = value_part.split()
                if len(value_parts) > 1:
                    result["valid"] = False
                    result["errors"].append("Update format should be 'key=value' with no extra text")
    
    return result

def format_error_response(error: Exception, user_friendly: bool = True) -> str:
    """Format error response for user display"""
    if user_friendly:
        if isinstance(error, ValidationError):
            return f"Validation Error: {error.message}"
        elif isinstance(error, JSONProcessingError):
            return f"JSON Processing Error: {error.message}"
        elif isinstance(error, StateUpdateError):
            return f"State Update Error: {error.message}"
        elif isinstance(error, DatabaseError):
            return f"Database Error: {error.message}"
        elif isinstance(error, UserInputError):
            return f"Input Error: {error.message}"
        elif isinstance(error, StateManagementError):
            return f"State Management Error: {error.message}"
        else:
            return "System Error: An unexpected error occurred. Please try again."
    else:
        if isinstance(error, StateManagementError):
            return f"Error: {error.message} | Code: {error.error_code} | Details: {error.details}"
        else:
            return f"Error: {str(error)}"

def log_error(error: Exception, context: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Log error with context for debugging"""
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "additional_context": additional_context or {}
    }
    
    if isinstance(error, StateManagementError):
        error_info["error_code"] = error.error_code
        error_info["details"] = error.details
    
    # In a real implementation, this would be logged to a file or database
    print(f"ERROR LOG: {error_info}")
    
    return error_info

load_dotenv()

# ===== PART 1: Initialize Persistent Session Service (MongoDB-backed) =====
# We'll use an in-memory session service for the ADK runtime and persist state to MongoDB Atlas.

# MongoDB connection (prefer env var, fallback to provided URI)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "adk_app"))
sessions_col = mongo_db.get_collection(os.getenv("MONGODB_COLLECTION", "sessions"))

# MongoDB session service used by the Runner
session_service = MongoDBSessionService(MONGODB_URI)

# For testing: Load a sample JSON file (simulating model output)
SAMPLE_JSON_FILE = "sample_json_output.json"  # Assume this file exists with structured JSON

# ===== PART 2: Define Initial State =====
initial_state = {
    "user_name": "Developer",
    "interaction_history": [],
    "user_queries": [],
    "json_inputs": [],  # Store raw input JSONs for reference
    "current_state": {  # Default template with empty values
        "_id": "",
        "user_id": "",
        "jwt": ""
    },
    "last_update": None,  # Timestamp of last state update
    "last_ingest_at": None,  # Timestamp when a model JSON reached ADK
    "timestamps": [],
    # Real-time structures
    "timeline": [],               # list of fused events with t_start/t_end/features/arrival_ts
    "aggregates": {"last_processed_timeline_index": -1},
    "alerts": [],                 # structured alerts like emotion spans; textualization by conversational agent only
    "question_windows": {},       # question_id -> { t_start, t_end }
}

async def main_async():
    # Setup constants
    APP_NAME = "Stateful JSON Assistant"
    USER_ID = "developer_user"

    # ===== PART 3: Session Management - Load from Mongo or Create =====
    # Try to load the most recent session for this app/user from MongoDB
    existing_doc = sessions_col.find_one(
        {"app_name": APP_NAME, "user_id": USER_ID},
        sort=[("updated_at", -1)],
    )

    if existing_doc and isinstance(existing_doc.get("state"), dict):
        # Use state from Mongo and continue that session
        state_to_use = existing_doc["state"]
        SESSION_ID = existing_doc.get("session_id") or str(uuid4())
        print(f"Continuing existing session (Mongo): {SESSION_ID}")
    else:
        # No prior session found; start fresh
        state_to_use = initial_state
        SESSION_ID = str(uuid4())
        print(f"Created new session (Mongo): {SESSION_ID}")

    # Create the session in MongoDB
    session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=state_to_use,
    )

    # Ensure real-time structures exist
    ensure_session_structures(session_service, APP_NAME, USER_ID, SESSION_ID)

    # ===== PART 4: Agent Runner Setup =====
    # Use conversational agent as root by default to avoid LLM routing loops.
    # Set ROOT_AGENT=manager to use the manager/orchestrator instead.
    ROOT_AGENT = os.getenv("ROOT_AGENT", "conversational").lower().strip()
    root_agent = state_manager_agent if ROOT_AGENT == "manager" else conversational_agent
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Session is already persisted in MongoDB via the session service
    print(f"Session ready: {SESSION_ID}")

    # ===== PART 5: Interactive Loop =====
    print("\nWelcome to Coding Assistant Chat!")
    print("Ask coding doubts or request code generation.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Ending session. Goodbye!")
            break

        # Save to history
        add_user_query_to_history(session_service, APP_NAME, USER_ID, SESSION_ID, user_input)

        # Simulate receiving JSON output for testing (e.g., if user says "simulate json")
        if "simulate json" in user_input.lower():
            try:
                with open(SAMPLE_JSON_FILE, 'r') as f:
                    json_data = json.load(f)
                # Direct real-time ingestion without free-form query
                ingested = ingest_from_model_output(session_service, APP_NAME, USER_ID, SESSION_ID, json_data)
                print(f"Ingested event: {ingested}")
                # Optionally, ask conversational agent to summarize recent behavior
                await call_agent_async(runner, USER_ID, SESSION_ID, "give me a summary of recent behavior")
            except Exception as e:
                print(f"Error loading sample JSON: {e}")
        elif "simulate event" in user_input.lower():
            # Accept a single-line JSON event pasted after the command, e.g.,
            # simulate event {"t_start":0.0,"t_end":2.5, ...}
            try:
                match = re.search(r"simulate\s+event\s+(\{.*\})", user_input, re.IGNORECASE | re.DOTALL)
                if match:
                    payload_str = match.group(1)
                    payload = json.loads(payload_str)
                    ingested = ingest_from_model_output(session_service, APP_NAME, USER_ID, SESSION_ID, payload)
                    print(f"Ingested event: {ingested}")
                    await call_agent_async(runner, USER_ID, SESSION_ID, "summarize recent behavior")
                else:
                    print("No JSON payload found after 'simulate event'.")
            except Exception as e:
                print(f"Error parsing simulate event payload: {e}")
        else:
            # Normal agent call
            await call_agent_async(runner, USER_ID, SESSION_ID, user_input)

        # State is automatically persisted by the MongoDB session service
        pass

    # ===== PART 6: Final State =====
    final_session = session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    print("\nFinal Session State:")
    for key, value in final_session.state.items():
        print(f"{key}: {value}")
    
    print("Ending conversation. Your data has been saved to MongoDB Atlas.")
    
    # Close the session service
    session_service.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
