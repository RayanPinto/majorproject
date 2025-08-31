import asyncio
import os
import json
import re
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

from manager.sub_agents.conversational_agent import conversational_agent
from google.adk.runners import Runner
from pymongo import MongoClient
from google.adk.sessions import InMemorySessionService
from mongodb_session_service import MongoDBSessionService

from utils import add_user_query_to_history, call_agent_async, display_behavioral_analysis, display_emotional_timeline
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
    "candidate_info": {
        "candidate_id": "",
        "session_id": "",
        "interview_start": None
    },
    "behavioral_data": [],
    "current_behavior": {
        "metadata": {
            "candidate_id": "",
            "session_id": "",
            "timestamp": "",
            "duration_sec": 0
        },
        "video_features": {
            "frame_rate": 0,
            "facial_expressions": [],
            "gaze_tracking": [],
            "head_movements": [],
            "body_language": {}
        },
        "audio_features": {
            "speech_segments": [],
            "prosody": {},
            "pauses": [],
            "voice_tone": "",
            "disfluencies": []
        },
        "behavior_profile": {
            "confidence_level": 0.0,
            "engagement_level": 0.0,
            "stress_level": 0.0,
            "emotional_valence": "",
            "notable_observations": []
        }
    },
    "behavior_timeline": [],
    "behavioral_insights": {
        "emotional_pattern": "",
        "confidence_trend": [],
        "stress_indicators": [],
        "engagement_peaks": []
    },
    "last_update": None,
    "last_behavior_ingest": None,
    "question_windows": {},
    "alerts": []
}

async def main_async():
    # Setup constants
    APP_NAME = "Behavioral Analysis System"
    USER_ID = "interviewer_user"

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
    # Direct routing to conversational agent for behavioral analysis
    runner = Runner(
        agent=conversational_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Session is already persisted in MongoDB via the session service
    print(f"Session ready: {SESSION_ID}")

    # ===== PART 5: Interactive Loop =====
    print("\n🤖 Behavioral Analysis Assistant")
    print("═" * 50)
    print("📊 Real-time behavioral analysis during interviews")
    print("💬 Ask about candidate behavior, emotions, and patterns")
    print("📝 Commands: 'simulate json', 'analyze behavior', 'show insights'")
    print("❌ Type 'exit' or 'quit' to end the session\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Ending session. Goodbye!")
            break

        # Save to history
        add_user_query_to_history(session_service, APP_NAME, USER_ID, SESSION_ID, user_input)

        # Behavioral Analysis Commands
        if "simulate json" in user_input.lower():
            try:
                with open(SAMPLE_JSON_FILE, 'r') as f:
                    json_data = json.load(f)
                ingested = ingest_from_model_output(session_service, APP_NAME, USER_ID, SESSION_ID, json_data)
                print(f"📊 Behavioral data ingested: {ingested}")
                await call_agent_async(runner, USER_ID, SESSION_ID, "analyze the candidate's current behavioral state and provide insights")
            except Exception as e:
                print(f"❌ Error loading behavioral data: {e}")

        elif "simulate event" in user_input.lower():
            try:
                match = re.search(r"simulate\s+event\s+(\{.*\})", user_input, re.IGNORECASE | re.DOTALL)
                if match:
                    payload_str = match.group(1)
                    payload = json.loads(payload_str)
                    ingested = ingest_from_model_output(session_service, APP_NAME, USER_ID, SESSION_ID, payload)
                    print(f"📊 Behavioral event ingested: {ingested}")
                    await call_agent_async(runner, USER_ID, SESSION_ID, "analyze this behavioral data and identify key patterns")
                else:
                    print("❌ No behavioral data found after 'simulate event'.")
            except Exception as e:
                print(f"❌ Error parsing behavioral data: {e}")

        elif "analyze behavior" in user_input.lower():
            await call_agent_async(runner, USER_ID, SESSION_ID, "provide a comprehensive behavioral analysis of the candidate including emotional patterns, confidence levels, and stress indicators")

        elif "show insights" in user_input.lower():
            await call_agent_async(runner, USER_ID, SESSION_ID, "show me the key behavioral insights and notable observations from the interview")

        elif "emotional pattern" in user_input.lower():
            await call_agent_async(runner, USER_ID, SESSION_ID, "analyze the candidate's emotional patterns throughout the interview and identify any significant changes")

        elif "confidence level" in user_input.lower():
            await call_agent_async(runner, USER_ID, SESSION_ID, "assess the candidate's confidence level and how it changed during different parts of the interview")

        elif "show dashboard" in user_input.lower() or "behavioral dashboard" in user_input.lower():
            display_behavioral_analysis(session_service, APP_NAME, USER_ID, SESSION_ID)

        elif "emotional timeline" in user_input.lower() or "timeline" in user_input.lower():
            display_emotional_timeline(session_service, APP_NAME, USER_ID, SESSION_ID)

        elif "debug state" in user_input.lower():
            # Debug command to see what's actually in the state
            session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
            if session:
                print("🔍 **DEBUG: Current Session State**")
                print(f"Keys in state: {list(session.state.keys())}")
                if "current_behavior" in session.state:
                    current_behavior = session.state["current_behavior"]
                    print(f"Current behavior keys: {list(current_behavior.keys())}")
                    if "behavior_profile" in current_behavior:
                        profile = current_behavior["behavior_profile"]
                        print(f"Behavior profile: {profile}")
                if "behavioral_data" in session.state:
                    print(f"Behavioral data count: {len(session.state['behavioral_data'])}")
                if "behavioral_insights" in session.state:
                    insights = session.state["behavioral_insights"]
                    print(f"Behavioral insights keys: {list(insights.keys())}")
                    if "pattern_summary" in insights:
                        print(f"Pattern summary: {insights['pattern_summary']}")
                print("🔍 **End Debug**")
            else:
                print("❌ No session found for debugging")
        
        elif "force patterns" in user_input.lower():
            # Force pattern recognition generation
            session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
            if session:
                from manager.tools.tools import _update_behavioral_insights
                _update_behavioral_insights(session.state)
                session_service.update_session(APP_NAME, USER_ID, SESSION_ID, session.state)
                print("✅ **Pattern recognition forced and updated**")
                print("🔍 **New behavioral insights generated**")
                if "behavioral_insights" in session.state:
                    insights = session.state["behavioral_insights"]
                    if "pattern_summary" in insights:
                        print(f"📊 **Pattern Summary**: {insights['pattern_summary']}")
            else:
                print("❌ No session found for pattern generation")
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
    
    print("\n📊 **Final Behavioral Analysis Summary**")
    print("═" * 50)

    behavioral_data_count = len(final_session.state.get("behavioral_data", []))
    current_behavior = final_session.state.get("current_behavior", {})

    print(f"📝 Total behavioral data points processed: {behavioral_data_count}")

    if current_behavior.get("metadata"):
        candidate_id = current_behavior["metadata"].get("candidate_id", "Unknown")
        session_id = current_behavior["metadata"].get("session_id", "Unknown")
        print(f"👤 Candidate: {candidate_id}")
        print(f"📋 Session: {session_id}")

    behavior_profile = current_behavior.get("behavior_profile", {})
    if behavior_profile:
        confidence = behavior_profile.get("confidence_level", 0)
        engagement = behavior_profile.get("engagement_level", 0)
        stress = behavior_profile.get("stress_level", 0)
        valence = behavior_profile.get("emotional_valence", "unknown")

        print("📈 Final Behavioral Metrics:")
        print(f"   🎯 Confidence Level: {confidence:.2f}")
        print(f"   🔥 Engagement Level: {engagement:.2f}")
        print(f"   😰 Stress Level: {stress:.2f}")
        print(f"   💭 Emotional State: {valence.title()}")

    print("✅ Behavioral analysis complete! Data saved to MongoDB Atlas.")
    print("💡 Use 'show dashboard' to view detailed analysis anytime.")
    
    # Close the session service
    session_service.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
