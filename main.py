import asyncio
import os
import json
import sys
import traceback
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

from manager.agent import state_manager_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from utils import call_agent_async

load_dotenv()

# ===== ERROR HANDLING CLASSES =====

class StateManagementError(Exception):
    """Base exception for state management errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(StateManagementError):
    """Raised when validation fails"""
    pass

class JSONProcessingError(StateManagementError):
    """Raised when JSON processing fails"""
    pass

class StateUpdateError(StateManagementError):
    """Raised when state update fails"""
    pass

class DatabaseError(StateManagementError):
    """Raised when database operations fail"""
    pass

class UserInputError(StateManagementError):
    """Raised when user input is invalid"""
    pass

# ===== ERROR HANDLING UTILITIES =====

def log_error(error: Exception, context: str = "", details: Dict = None):
    """Log error with context and details"""
    timestamp = datetime.now().isoformat()
    error_info = {
        "timestamp": timestamp,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "details": details or {}
    }
    
    if hasattr(error, 'error_code'):
        error_info["error_code"] = error.error_code
    if hasattr(error, 'details'):
        error_info["details"].update(error.details)
    
    print(f"❌ ERROR [{timestamp}] {context}: {error}")
    if details:
        print(f"   Details: {details}")
    
    return error_info

def format_error_response(error: Exception, user_friendly: bool = True) -> str:
    """Format error message for user display"""
    if user_friendly:
        if isinstance(error, ValidationError):
            return f"❌ Validation Error: {error.message}"
        elif isinstance(error, JSONProcessingError):
            return f"❌ JSON Processing Error: {error.message}"
        elif isinstance(error, StateUpdateError):
            return f"❌ State Update Error: {error.message}"
        elif isinstance(error, DatabaseError):
            return f"❌ Database Error: {error.message}"
        elif isinstance(error, UserInputError):
            return f"❌ Input Error: {error.message}"
        else:
            return f"❌ System Error: {str(error)}"
    else:
        return f"Error: {error}"

def validate_json_structure(json_data: Dict, template_keys: List[str]) -> Dict[str, Any]:
    """Validate JSON structure against template"""
    errors = []
    warnings = []
    
    # Check for missing required keys
    for key in template_keys:
        if key not in json_data:
            warnings.append(f"Missing template key: {key}")
    
    # Check for extra keys
    extra_keys = [key for key in json_data.keys() if key not in template_keys]
    if extra_keys:
        warnings.append(f"Extra keys will be ignored: {', '.join(extra_keys)}")
    
    # Validate data types
    for key, value in json_data.items():
        if key in template_keys:
            if not isinstance(value, (str, int, float, bool, type(None))):
                errors.append(f"Invalid data type for {key}: expected primitive type, got {type(value).__name__}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def validate_user_input(command: str) -> Dict[str, Any]:
    """Validate user input command"""
    errors = []
    warnings = []
    
    if not command.strip():
        errors.append("Empty command")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check for common command patterns
    if command.startswith("Process this JSON:"):
        json_part = command[len("Process this JSON:"):].strip()
        if not json_part:
            errors.append("No JSON data provided after 'Process this JSON:'")
        else:
            try:
                json.loads(json_part)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {str(e)}")
    
    elif command.startswith("Update state:"):
        update_part = command[len("Update state:"):].strip()
        if not update_part:
            errors.append("No key-value pair provided after 'Update state:'")
        elif "=" not in update_part:
            errors.append("Invalid format: use 'key=value'")
        else:
            parts = update_part.split("=", 1)
            if len(parts) != 2:
                errors.append("Invalid format: use 'key=value'")
            else:
                key, value = parts
                if not key.strip():
                    errors.append("Empty key in update command")
                # Check for extra text after the value
                if " " in value and not value.strip().startswith('"'):
                    errors.append("Invalid format: value contains unexpected spaces")
                # Empty values are not allowed in this context
                if not value.strip():
                    errors.append("Empty value in update command")
    
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# ===== PART 1: Initialize Persistent Session Service (MongoDB-backed) =====
# We'll use an in-memory session service for the ADK runtime and persist state to MongoDB Atlas.

# MongoDB connection with error handling
def initialize_database():
    """Initialize database connection with error handling"""
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            raise DatabaseError("MongoDB URI not found in environment variables", "DB_001")
        
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ping')
        
        mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "adk_app"))
        sessions_col = mongo_db.get_collection(os.getenv("MONGODB_COLLECTION", "sessions"))
        
        print("✅ Database connection established successfully")
        return mongo_client, mongo_db, sessions_col
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"Failed to connect to MongoDB: {str(e)}"
        log_error(e, "Database Connection", {"mongodb_uri": MONGODB_URI})
        raise DatabaseError(error_msg, "DB_002", {"original_error": str(e)})
    except Exception as e:
        error_msg = f"Unexpected database error: {str(e)}"
        log_error(e, "Database Initialization")
        raise DatabaseError(error_msg, "DB_003", {"original_error": str(e)})

# Initialize database
try:
    mongo_client, mongo_db, sessions_col = initialize_database()
except DatabaseError as e:
    print(f"⚠️ Database connection failed: {e.message}")
    print("🔄 Running in offline mode (state will not be persisted)")
    mongo_client = mongo_db = sessions_col = None

# In-memory session service used by the Runner
session_service = InMemorySessionService()

def safe_persist_state(app_name: str, user_id: str, session_id: str, state: Dict, sessions_col):
    """Safely persist state to database with error handling"""
    if sessions_col is None:
        return False  # Database not available
    
    try:
        sessions_col.update_one(
            {"app_name": app_name, "user_id": user_id, "session_id": session_id},
            {
                "$set": {
                    "app_name": app_name,
                    "user_id": user_id,
                    "session_id": session_id,
                    "state": state,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        log_error(e, "State Persistence", {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id
        })
        return False

async def handle_json_processing(user_input: str, app_name: str, user_id: str, session_id: str, session_service, sessions_col):
    """Handle JSON processing with comprehensive error handling"""
    try:
        # Extract JSON string
        json_str = user_input.split("Process this JSON: ")[1]
        if not json_str.strip():
            raise UserInputError("No JSON data provided after 'Process this JSON:'", "INPUT_001")
        
        # Parse JSON
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise JSONProcessingError(f"Invalid JSON format: {str(e)}", "JSON_001", {"json_string": json_str})
        
        # Get current session
        try:
            current_session = session_service.get_session(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
        except Exception as e:
            raise StateUpdateError(f"Failed to get session: {str(e)}", "SESS_002")
        
        # Initialize state if needed
        if "current_state" not in current_session.state:
            current_session.state["current_state"] = {
                "_id": "",
                "user_id": "",
                "jwt": ""
            }
            current_session.state["json_inputs"] = []
        
        # Validate JSON structure
        template_keys = ["_id", "user_id", "jwt"]
        validation_result = validate_json_structure(json_data, template_keys)
        
        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                print(f"⚠️ {warning}")
        
        if not validation_result["valid"]:
            for error in validation_result["errors"]:
                print(f"❌ {error}")
            raise ValidationError("JSON validation failed", "VAL_001", {"errors": validation_result["errors"]})
        
        # Store raw JSON input
        current_session.state["json_inputs"].append({
            "json_data": json_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update matching keys in current state
        current_state = current_session.state["current_state"]
        updated_keys = []
        
        for key, value in json_data.items():
            if key in current_state:
                current_state[key] = value
                updated_keys.append(key)
        
        current_session.state["current_state"] = current_state
        current_session.state["last_update"] = datetime.now().isoformat()
        
        # Update session
        try:
            session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                state=current_session.state
            )
        except Exception as e:
            raise StateUpdateError(f"Failed to update session: {str(e)}", "SESS_003")
        
        # Persist to database
        if safe_persist_state(app_name, user_id, session_id, current_session.state, sessions_col):
            print("💾 State persisted to database")
        
        # Display results
        if updated_keys:
            print(f"✅ State updated successfully!")
            print(f"Updated keys: {', '.join(updated_keys)}")
            print(f"Current state: {json.dumps(current_state, indent=2)}")
        else:
            print(f"⚠️ No matching keys found in JSON.")
            print(f"Template keys: {list(current_state.keys())}")
            print(f"JSON keys: {list(json_data.keys())}")
            print("State unchanged.")
            
    except (UserInputError, JSONProcessingError, ValidationError, StateUpdateError) as e:
        print(format_error_response(e))
        log_error(e, "JSON Processing", {"user_input": user_input})
    except Exception as e:
        print(f"❌ Unexpected error processing JSON: {str(e)}")
        log_error(e, "JSON Processing", {"user_input": user_input})

# For testing: Load a sample JSON file (simulating model output)
SAMPLE_JSON_FILE = "sample_json_output.json"  # Assume this file exists with structured JSON

# ===== PART 2: Define Initial State =====
initial_state = {
    "json_inputs": [],  # Store raw input JSONs for reference
    "current_state": {  # Default template with empty values
        "_id": "",
        "user_id": "",
        "jwt": ""
    },
    "last_update": None,  # Timestamp of last state update
}

async def main_async():
    # Setup constants
    APP_NAME = "Stateful JSON Assistant"
    USER_ID = "developer_user"

    # ===== PART 3: Session Management - Load from Mongo or Create =====
    try:
        if sessions_col is not None:
            # Try to load the most recent session for this app/user from MongoDB
            existing_doc = sessions_col.find_one(
                {"app_name": APP_NAME, "user_id": USER_ID},
                sort=[("updated_at", -1)],
            )

            if existing_doc and isinstance(existing_doc.get("state"), dict):
                # Use state from Mongo and continue that session
                state_to_use = existing_doc["state"]
                SESSION_ID = existing_doc.get("session_id") or str(uuid4())
                print(f"✅ Continuing existing session (Mongo): {SESSION_ID}")
            else:
                # No prior session found; start fresh
                state_to_use = initial_state
                SESSION_ID = str(uuid4())
                print(f"🆕 Created new session (Mongo): {SESSION_ID}")
        else:
            # Database not available, start fresh
            state_to_use = initial_state
            SESSION_ID = str(uuid4())
            print(f"🆕 Created new session (Offline): {SESSION_ID}")
            
    except Exception as e:
        log_error(e, "Session Loading")
        # Fallback to fresh session
        state_to_use = initial_state
        SESSION_ID = str(uuid4())
        print(f"🆕 Created new session (Fallback): {SESSION_ID}")

    # Create the session inside the in-memory service with the chosen ID/state
    try:
        session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state=state_to_use,
        )
        print("✅ Session created successfully")
    except Exception as e:
        log_error(e, "Session Creation")
        raise StateUpdateError(f"Failed to create session: {str(e)}", "SESS_001")

    # ===== PART 4: Agent Runner Setup =====
    try:
        runner = Runner(
            agent=state_manager_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        print("✅ Agent runner initialized successfully")
    except Exception as e:
        log_error(e, "Agent Runner Setup")
        raise StateUpdateError(f"Failed to initialize agent runner: {str(e)}", "RUNNER_001")

    # Persist initial state to MongoDB so the session exists even before first user input
    try:
        current_session = session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        
        if safe_persist_state(APP_NAME, USER_ID, SESSION_ID, current_session.state, sessions_col):
            print("✅ Initial state persisted to database")
        else:
            print("⚠️ Failed to persist initial state (continuing in memory only)")
            
    except Exception as e:
        log_error(e, "Initial State Persistence")
        print("⚠️ Failed to persist initial state (continuing in memory only)")

    # ===== PART 5: Interactive Loop =====
    print("\n🎉 Welcome to Stateful JSON Assistant!")
    print("📝 Available commands:")
    print("  • Process this JSON: {...} - Update state with JSON data")
    print("  • Update state: key=value - Manually update a specific key")
    print("  • summary - Show current state summary")
    print("  • access state - Show full current state")
    print("  • show template - Display the default template")
    print("  • simulate json - Load sample JSON from file")
    print("  • help - Show this help message")
    print("  • exit/quit - End the conversation")
    print("\nType 'help' for more information.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                print("💡 Please enter a command. Type 'help' for available commands.")
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Ending session. Goodbye!")
                break

            if user_input.lower() == "help":
                print("\n📚 Available Commands:")
                print("  • Process this JSON: {...} - Update state with JSON data")
                print("  • Update state: key=value - Manually update a specific key")
                print("  • summary - Show current state summary")
                print("  • access state - Show full current state")
                print("  • show template - Display the default template")
                print("  • simulate json - Load sample JSON from file")
                print("  • help - Show this help message")
                print("  • exit/quit - End the conversation")
                continue

            # Validate user input first
            validation_result = validate_user_input(user_input)
            if not validation_result["valid"]:
                for error in validation_result["errors"]:
                    print(f"❌ {error}")
                if validation_result["warnings"]:
                    for warning in validation_result["warnings"]:
                        print(f"⚠️ {warning}")
                continue

            # Handle state management commands directly
            if user_input.startswith("Process this JSON:"):
                await handle_json_processing(user_input, APP_NAME, USER_ID, SESSION_ID, session_service, sessions_col)
                
            elif user_input.startswith("Update state:"):
                # Handle manual state updates
                try:
                    update_str = user_input.split("Update state: ")[1].strip()
                    key, value = update_str.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Get current session
                    current_session = session_service.get_session(
                        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
                    )
                    
                    # Initialize state if needed
                    if "current_state" not in current_session.state:
                        current_session.state["current_state"] = {
                            "_id": "",
                            "user_id": "",
                            "jwt": ""
                        }
                    
                    current_state = current_session.state["current_state"]
                    
                    if key in current_state:
                        current_state[key] = value
                        current_session.state["current_state"] = current_state
                        current_session.state["last_update"] = datetime.now().isoformat()
                        
                        # Update session
                        session_service.create_session(
                            app_name=APP_NAME,
                            user_id=USER_ID,
                            session_id=SESSION_ID,
                            state=current_session.state
                        )
                        
                        print(f"✅ State updated: {key} = {value}")
                        print(f"Current state: {json.dumps(current_state, indent=2)}")
                    else:
                        print(f"❌ Key '{key}' not found in template.")
                        print(f"Available keys: {list(current_state.keys())}")
                        
                except ValueError:
                    print("❌ Invalid format. Use 'Update state: key=value'")
                except Exception as e:
                    print(f"❌ Error updating state: {e}")
                    
            elif user_input.lower() in ["summary", "summarize"]:
                # Handle summary requests
                current_session = session_service.get_session(
                    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
                )
                
                current_state = current_session.state.get("current_state", {})
                last_update = current_session.state.get("last_update", "Never")
                
                print("📋 Current State Summary:")
                print(f"🕒 Last Updated: {last_update}")
                print()
                
                if not current_state:
                    print("No state data yet. Template not initialized.")
                else:
                    for key, value in current_state.items():
                        if value:
                            print(f"✅ {key}: {value}")
                        else:
                            print(f"⏳ {key}: [Empty - waiting for data]")
                            
            elif user_input.lower() in ["access state", "show state"]:
                # Handle state access requests
                current_session = session_service.get_session(
                    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
                )
                
                current_state = current_session.state.get("current_state", {})
                last_update = current_session.state.get("last_update", "Never")
                
                print("📊 Current State:")
                print(json.dumps(current_state, indent=2))
                print(f"🕒 Last Updated: {last_update}")
                
            elif user_input.lower() in ["show template", "template"]:
                # Handle template display requests
                template = {
                    "_id": "",
                    "user_id": "",
                    "jwt": ""
                }
                print("📋 Default Template:")
                print(json.dumps(template, indent=2))
                print("This template defines the expected keys for state management.")
                
            elif "simulate json" in user_input.lower():
                try:
                    with open(SAMPLE_JSON_FILE, 'r') as f:
                        json_data = json.load(f)
                    # Simulate passing JSON to the agent via query
                    simulated_query = f"Process this JSON: {json.dumps(json_data)}"
                    print(f"Simulating JSON input: {json.dumps(json_data, indent=2)}")
                    # Process it directly
                    user_input = simulated_query
                    # Re-run the loop to process this JSON
                    continue
                except Exception as e:
                    print(f"Error loading sample JSON: {e}")
            else:
                # Normal agent call for other queries
                await call_agent_async(runner, USER_ID, SESSION_ID, user_input)

            # Persist updated state to MongoDB after each turn
            try:
                current_session = session_service.get_session(
                    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
                )
                result = safe_persist_state(APP_NAME, USER_ID, SESSION_ID, current_session.state, sessions_col)
                if result:
                    pass  # Successfully persisted
            except Exception as e:
                log_error(e, "State Persistence")
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            log_error(e, "Main Loop")
            print("🔄 Continuing...")

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

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
