#!/usr/bin/env python3
"""
Real-time Behavioral Analysis System
Clean, focused system for real-time JSON ingestion and behavioral analysis
"""

import asyncio
import os
import json
import socket
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv

from manager.sub_agents.conversational_agent import conversational_agent
from google.adk.runners import Runner
from pymongo import MongoClient
from google.adk.sessions import InMemorySessionService
from mongodb_session_service import MongoDBSessionService

from utils import add_user_query_to_history, call_agent_async, display_behavioral_analysis, display_emotional_timeline
from manager.tools.tools import ingest_from_model_output, ensure_session_structures

load_dotenv()

# ===== PART 1: Initialize Persistent Session Service (MongoDB-backed) =====
# We'll use an in-memory session service for the ADK runtime and persist state to MongoDB Atlas.

# MongoDB connection (prefer env var, fallback to provided URI)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "adk_app"))
sessions_col = mongo_db.get_collection(os.getenv("MONGODB_COLLECTION", "sessions"))

# MongoDB session service used by the Runner
session_service = MongoDBSessionService(
    mongo_uri=MONGODB_URI,
    database_name=os.getenv("MONGODB_DB", "adk_app"),
    collection_name=os.getenv("MONGODB_COLLECTION", "sessions")
)

# ===== PART 2: Initial State Structure =====
# Define the initial state structure for behavioral analysis

initial_state = {
    "candidate_info": {
        "candidate_id": "CAND1234567890",
        "session_id": "INT2025-09-01-008",
        "interview_start": None
    },
    "behavioral_data": [],
    "current_behavior": {},
    "behavior_timeline": [],
    "behavioral_insights": {
        "emotional_pattern": "neutral",
        "confidence_trend": [],
        "stress_indicators": [],
        "engagement_peaks": []
    },
    "last_update": None,
    "last_behavior_ingest": None,
    "question_windows": {},
    "alerts": []
}

# ===== JSON RECEIVER FUNCTIONALITY =====

class JSONReceiver:
    """Receives JSON data from producer and processes it"""
    
    def __init__(self, session_service, app_name: str, user_id: str, session_id: str):
        self.session_service = session_service
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.is_running = False
        self.receiver_thread = None
        self.socket = None
        self.processed_count = 0
        
    def start_receiving(self, port: int = 12345):
        """Start receiving JSON data on specified port"""
        if self.is_running:
            print("⚠️ JSON receiver is already running")
            return
            
        self.is_running = True
        self.receiver_thread = threading.Thread(target=self._receive_loop, args=(port,), daemon=True)
        self.receiver_thread.start()
        print(f"✅ JSON receiver started on port {port}")
        print("📡 Waiting for producer to connect...")
        
    def stop_receiving(self):
        """Stop receiving JSON data"""
        self.is_running = False
        if self.socket:
            self.socket.close()
        print("⏹️ JSON receiver stopped")
        
    def _receive_loop(self, port: int):
        """Main receiving loop"""
        try:
            # Create socket server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('localhost', port))
            self.socket.listen(1)
            self.socket.settimeout(1.0)  # 1 second timeout
            
            print(f"🔌 Socket server listening on port {port}")
            
            while self.is_running:
                try:
                    # Accept connection
                    client_socket, addr = self.socket.accept()
                    print(f"🔗 Producer connected from {addr}")
                    
                    # Set client socket timeout
                    client_socket.settimeout(5.0)  # 5 second timeout for client
                    
                    # Receive data
                    while self.is_running:
                        try:
                            data = client_socket.recv(4096)
                            if not data:
                                print("📭 No data received, connection may be closed")
                                break
                                
                            # Process received JSON
                            json_str = data.decode('utf-8').strip()
                            if json_str:
                                self._process_json(json_str)
                            else:
                                print("📭 Empty JSON string received")
                                
                        except socket.timeout:
                            continue
                        except Exception as e:
                            print(f"❌ Error receiving data: {e}")
                            break
                            
                    client_socket.close()
                    print("🔌 Producer disconnected")
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        print(f"❌ Connection error: {e}")
                        
        except Exception as e:
            print(f"❌ Socket error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                
    def _process_json(self, json_str: str):
        """Process received JSON string"""
        try:
            # Parse JSON
            json_data = json.loads(json_str)
            print(f"📥 Received JSON from producer: {json_data.get('metadata', {}).get('candidate_id', 'Unknown')}")
            
            # Convert to your system's expected format
            converted_data = self._convert_json_format(json_data)
            print(f"🔄 Converted JSON structure with {len(converted_data)} fields")
            
            # Process using existing system
            success = ingest_from_model_output(
                self.session_service,
                self.app_name,
                self.user_id,
                self.session_id,
                converted_data
            )
            
            if success:
                self.processed_count += 1
                print(f"✅ Processed JSON #{self.processed_count}")
                
                # Show behavioral metrics
                print(f"   Confidence: {converted_data.get('confidence_level', 0.0)}")
                print(f"   Engagement: {converted_data.get('engagement_level', 0.0)}")
                print(f"   Stress: {converted_data.get('stress_level', 0.0)}")
                print(f"   Emotional: {converted_data.get('emotional_valence', 'neutral')}")
                print(f"   Candidate: {converted_data.get('candidate_id', 'Unknown')}")
                
                # Verify state update
                session = self.session_service.get_session(
                    app_name=self.app_name,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                if session and "behavioral_data" in session.state:
                    print(f"   📊 Total behavioral data points: {len(session.state['behavioral_data'])}")
            else:
                print(f"❌ Failed to process JSON #{self.processed_count + 1}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON received: {e}")
        except Exception as e:
            print(f"❌ Error processing JSON: {e}")
            import traceback
            print(f"🔍 Full error: {traceback.format_exc()}")
            
    def _convert_json_format(self, producer_json: dict) -> dict:
        """Convert producer JSON format to system expected format"""
        
        # Extract data from producer format
        metadata = producer_json.get('metadata', {})
        video_features = producer_json.get('video_features', {})
        audio_features = producer_json.get('audio_features', {})
        behavior_profile = producer_json.get('behavior_profile', {})
        
        # Convert to system format - this should match what ingest_from_model_output expects
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        
        # Create the structure that ingest_from_model_output expects
        converted_data = {
            "metadata": metadata,  # Direct access for candidate_id, session_id
            "video_features": video_features,
            "audio_features": audio_features,
            "behavior_profile": behavior_profile,
            "timestamp": timestamp,
            "candidate_id": metadata.get('candidate_id', 'CAND123'),
            "session_id": metadata.get('session_id', 'INT2025-09-01-001'),
            "confidence_level": behavior_profile.get('confidence_level', 0.0),
            "engagement_level": behavior_profile.get('engagement_level', 0.0),
            "stress_level": behavior_profile.get('stress_level', 0.0),
            "emotional_valence": behavior_profile.get('emotional_valence', 'neutral'),
            "facial_expressions": video_features.get('facial_expressions', []),
            "gaze_tracking": video_features.get('gaze_tracking', []),
            "head_movements": video_features.get('head_movements', []),
            "body_language": video_features.get('body_language', {}),
            "speech_segments": audio_features.get('speech_segments', []),
            "prosody": audio_features.get('prosody', {}),
            "pauses": audio_features.get('pauses', []),
            "voice_tone": audio_features.get('voice_tone', 'neutral')
        }
        
        return converted_data

# Global JSON receiver instance
json_receiver = None

def start_json_receiver(session_service, app_name: str, user_id: str, session_id: str):
    """Start the JSON receiver"""
    global json_receiver
    if json_receiver is None:
        json_receiver = JSONReceiver(session_service, app_name, user_id, session_id)
    json_receiver.start_receiving()

def stop_json_receiver():
    """Stop the JSON receiver"""
    global json_receiver
    if json_receiver:
        json_receiver.stop_receiving()

# ===== MAIN APPLICATION =====

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
    from utils import display_welcome
    display_welcome()

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Ending session. Goodbye!")
            break

        # Save to history
        add_user_query_to_history(session_service, APP_NAME, USER_ID, SESSION_ID, user_input)

        # Behavioral Analysis Commands
        if "start json producer" in user_input.lower():
            print("🚀 Starting real-time JSON producer...")
            print("📡 Producer will generate unique JSON data continuously")
            print("💡 Run 'python json_producer.py' in another terminal to start the producer")
            print("🔄 Your system will automatically process incoming JSON data")
            print("⏹️  Use 'stop json producer' to stop receiving data")
            
            # Start the JSON receiver
            start_json_receiver(session_service, APP_NAME, USER_ID, SESSION_ID)
            
        elif "stop json producer" in user_input.lower():
            print("⏹️ Stopping JSON producer...")
            stop_json_receiver()

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
        
        elif "toggle speech" in user_input.lower():
            # Toggle speech functionality
            try:
                from utils import toggle_speech, get_speech_status
                new_state = toggle_speech()
                status = get_speech_status()
                print(f"🔊 Speech toggled: {status}")
            except ImportError:
                print("❌ Speech functionality not available.")
                print("💡 Install dependencies: pip install pygame")
        
        elif "speech status" in user_input.lower():
            # Show speech status
            try:
                from utils import get_speech_status
                status = get_speech_status()
                print(f"🔊 Speech Status: {status}")
            except ImportError:
                print("❌ Speech functionality not available.")
                print("💡 Install dependencies: pip install pygame")
        
        elif "test speech" in user_input.lower():
            # Test speech functionality with ADK Runner
            print("🎤 Testing speech with ADK Runner...")
            print("💡 Speech will be tested with your next agent query")
            print("✨ Try: 'analyze behavior' to test speech output")
        
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
    
    if final_session:
        print(f"\n📊 Final Session State:")
        print(f"   Behavioral Data Points: {len(final_session.state.get('behavioral_data', []))}")
        print(f"   User Queries: {len(final_session.state.get('user_queries', []))}")
        print(f"   Last Update: {final_session.state.get('last_update', 'Never')}")
    
    print("\n✅ Session completed and saved to MongoDB")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
