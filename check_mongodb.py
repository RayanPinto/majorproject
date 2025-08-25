#!/usr/bin/env python3
"""Check MongoDB data storage"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "adk_app"))
sessions_col = mongo_db.get_collection(os.getenv("MONGODB_COLLECTION", "sessions"))

print("🔍 MongoDB Data Storage Check")
print("=" * 50)

# Check connection
try:
    # Test connection
    mongo_client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

# Count documents
total_docs = sessions_col.count_documents({})
print(f"📊 Total documents in collection: {total_docs}")

# Get recent documents
recent_docs = list(sessions_col.find({}, {
    '_id': 0, 
    'app_name': 1, 
    'user_id': 1, 
    'session_id': 1, 
    'updated_at': 1
}).sort('updated_at', -1).limit(5))

print(f"\n📋 Recent {len(recent_docs)} documents:")
for i, doc in enumerate(recent_docs, 1):
    session_id = doc.get('session_id', 'N/A')
    session_short = session_id[:8] + "..." if len(session_id) > 8 else session_id
    print(f"  {i}. App: {doc.get('app_name', 'N/A')}")
    print(f"     User: {doc.get('user_id', 'N/A')}")
    print(f"     Session: {session_short}")
    print(f"     Updated: {doc.get('updated_at', 'N/A')}")
    print()

# Check specific session data
if recent_docs:
    latest_doc = recent_docs[0]
    session_id = latest_doc.get('session_id')
    if session_id:
        session_data = sessions_col.find_one({'session_id': session_id})
        if session_data and 'state' in session_data:
            state = session_data['state']
            print("🔍 Latest Session State:")
            print(f"  JSON Inputs: {len(state.get('json_inputs', []))}")
            print(f"  User Queries: {len(state.get('user_queries', []))}")
            print(f"  Current State: {state.get('current_state', {})}")
            print(f"  Last Update: {state.get('last_update', 'N/A')}")

print("\n✅ MongoDB data storage check completed!")
