import asyncio
import os
import json
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv

from manager.agent import state_manager_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from pymongo import MongoClient

from utils import call_agent_async

load_dotenv()

# ===== PART 1: Initialize Persistent Session Service (MongoDB-backed) =====
# We'll use an in-memory session service for the ADK runtime and persist state to MongoDB Atlas.

# MongoDB connection (prefer env var, fallback to provided URI)
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "adk_app"))
sessions_col = mongo_db.get_collection(os.getenv("MONGODB_COLLECTION", "sessions"))

# In-memory session service used by the Runner
session_service = InMemorySessionService()

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

    # Create the session inside the in-memory service with the chosen ID/state
    session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=state_to_use,
    )

    # ===== PART 4: Agent Runner Setup =====
    runner = Runner(
        agent=state_manager_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Persist initial state to MongoDB so the session exists even before first user input
    current_session = session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    sessions_col.update_one(
        {"app_name": APP_NAME, "user_id": USER_ID, "session_id": SESSION_ID},
        {
            "$set": {
                "app_name": APP_NAME,
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "state": current_session.state,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    # ===== PART 5: Interactive Loop =====
    print("\nWelcome to Stateful JSON Assistant!")
    print("You can simulate JSON inputs, request summaries, or interact with the state agent.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Ending session. Goodbye!")
            break

        # No need to save to history - focus on state management only

        # Handle state management commands directly
        if user_input.startswith("Process this JSON:"):
            # Handle JSON processing
            try:
                json_str = user_input.split("Process this JSON: ")[1]
                json_data = json.loads(json_str)
                
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
                    current_session.state["json_inputs"] = []
                
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
                session_service.create_session(
                    app_name=APP_NAME,
                    user_id=USER_ID,
                    session_id=SESSION_ID,
                    state=current_session.state
                )
                
                if updated_keys:
                    print(f"✅ State updated successfully!")
                    print(f"Updated keys: {', '.join(updated_keys)}")
                    print(f"Current state: {json.dumps(current_state, indent=2)}")
                else:
                    print(f"⚠️ No matching keys found in JSON.")
                    print(f"Template keys: {list(current_state.keys())}")
                    print(f"JSON keys: {list(json_data.keys())}")
                    print("State unchanged.")
                    
            except json.JSONDecodeError:
                print("❌ Invalid JSON format. Please provide valid JSON.")
            except Exception as e:
                print(f"❌ Error processing JSON: {e}")
                
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
        current_session = session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        sessions_col.update_one(
            {"app_name": APP_NAME, "user_id": USER_ID, "session_id": SESSION_ID},
            {
                "$set": {
                    "app_name": APP_NAME,
                    "user_id": USER_ID,
                    "session_id": SESSION_ID,
                    "state": current_session.state,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

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
