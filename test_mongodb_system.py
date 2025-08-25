#!/usr/bin/env python3
"""
Test MongoDB System
Tests the system with the new MongoDB session service.
"""

import os
from dotenv import load_dotenv

def test_mongodb_system():
    """Test the MongoDB-based system"""
    print("🔍 Testing MongoDB-Based System")
    print("=" * 40)
    
    try:
        # Test imports
        from mongodb_session_service import MongoDBSessionService
        print("✅ MongoDB session service imported")
        
        from main import main_async, APP_NAME, USER_ID
        print("✅ Main system imported")
        
        # Test session service creation
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        session_service = MongoDBSessionService(mongo_uri)
        print("✅ MongoDB session service created")
        
        # Test session operations
        test_session = session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session",
            state={"test": "data"}
        )
        print("✅ Session created successfully")
        
        # Test session retrieval
        retrieved_session = session_service.get_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session"
        )
        print("✅ Session retrieved successfully")
        
        # Test session update
        updated_session = session_service.update_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session",
            state={"test": "updated_data", "new_field": "value"}
        )
        print("✅ Session updated successfully")
        
        # Clean up
        session_service.delete_session("test_app", "test_user", "test_session")
        session_service.close()
        print("✅ Test session cleaned up")
        
        print("\n🎉 MongoDB system is working correctly!")
        print("✅ All session operations successful")
        print("✅ Ready for comprehensive testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ System needs fixing")
        return False

def show_test_queries():
    """Show test queries for the system"""
    print("\n📋 TEST QUERIES FOR YOUR SYSTEM:")
    print("=" * 40)
    
    test_queries = [
        "hi",
        "help me", 
        "show me my current state",
        'Process this JSON: {"_id": "test123", "user_id": "test_user", "jwt": "test_token"}',
        "update my user_id to new_user",
        "append this query",
        "what's in my data"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. '{query}'")
    
    print("\n🎯 HOW TO TEST:")
    print("1. Run: python main.py")
    print("2. Copy and paste any query above")
    print("3. Observe the system's response")
    print("4. Check that state changes are persisted to MongoDB")

if __name__ == "__main__":
    load_dotenv()
    success = test_mongodb_system()
    if success:
        show_test_queries()
    else:
        print("\n❌ Please fix the system issues before testing.")
