#!/usr/bin/env python3
"""
MongoDB Session Service
A proper session service that uses MongoDB for persistence.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pymongo import MongoClient
from google.adk.sessions import BaseSessionService, Session

class MongoDBSessionService(BaseSessionService):
    """MongoDB-based session service for the ADK system"""
    
    def __init__(self, mongo_uri: str, database_name: str = "adk_app", collection_name: str = "sessions"):
        self.mongo_client = MongoClient(mongo_uri)
        self.database = self.mongo_client[database_name]
        self.collection = self.database[collection_name]
    
    def create_session(self, app_name: str, user_id: str, session_id: str, state: Dict[str, Any]) -> Session:
        """Create a new session in MongoDB"""
        session_data = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "state": state,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Upsert the session
        self.collection.update_one(
            {
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id
            },
            {"$set": session_data},
            upsert=True
        )
        
        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state
        )
    
    def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[Session]:
        """Get a session from MongoDB"""
        session_doc = self.collection.find_one({
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id
        })
        
        if session_doc:
            return Session(
                id=session_doc["session_id"],
                app_name=session_doc["app_name"],
                user_id=session_doc["user_id"],
                state=session_doc["state"]
            )
        
        return None
    
    def update_session(self, app_name: str, user_id: str, session_id: str, state: Dict[str, Any]) -> Session:
        """Update an existing session in MongoDB"""
        update_data = {
            "state": state,
            "updated_at": datetime.now(timezone.utc)
        }
        
        self.collection.update_one(
            {
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id
            },
            {"$set": update_data}
        )
        
        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state
        )
    
    def delete_session(self, app_name: str, user_id: str, session_id: str) -> bool:
        """Delete a session from MongoDB"""
        result = self.collection.delete_one({
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id
        })
        
        return result.deleted_count > 0
    
    def list_sessions(self, app_name: str, user_id: str) -> list[Session]:
        """List all sessions for a user"""
        session_docs = self.collection.find({
            "app_name": app_name,
            "user_id": user_id
        })
        
        sessions = []
        for doc in session_docs:
            sessions.append(Session(
                id=doc["session_id"],
                app_name=doc["app_name"],
                user_id=doc["user_id"],
                state=doc["state"]
            ))
        
        return sessions
    
    def list_events(self, app_name: str, user_id: str, session_id: str) -> list:
        """List events for a session (not implemented for this simple version)"""
        return []
    
    def close(self):
        """Close the MongoDB connection"""
        self.mongo_client.close()
