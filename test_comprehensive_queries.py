#!/usr/bin/env python3
"""
Comprehensive Query Test Suite
Tests the system with various natural language queries and commands.
"""

import asyncio
import json
from datetime import datetime

# Comprehensive test queries organized by category
COMPREHENSIVE_TEST_QUERIES = [
    # ===== JSON PROCESSING QUERIES =====
    {
        "category": "JSON Processing",
        "queries": [
            "Process this JSON: {\"_id\": \"user123\", \"user_id\": \"john_doe\", \"jwt\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\"}",
            "append this query",
            "add this data",
            "save this information",
            "store this json",
            "process this data",
            "add this json {\"_id\": \"test456\", \"user_id\": \"jane_smith\", \"jwt\": \"test_token_123\"}",
            "save this json {\"_id\": \"demo789\", \"user_id\": \"demo_user\", \"jwt\": \"demo_jwt\"}",
            "store this data {\"_id\": \"final123\", \"user_id\": \"final_user\", \"jwt\": \"final_token\"}"
        ]
    },
    
    # ===== STATE UPDATE QUERIES =====
    {
        "category": "State Updates",
        "queries": [
            "Update state: _id=new_value",
            "update my user_id to john_doe",
            "change my _id to new_value",
            "modify the jwt token",
            "set my user_id as test_user",
            "update my _id to test456",
            "change user_id to jane_smith",
            "set jwt to new_token_123",
            "modify my _id to updated_id"
        ]
    },
    
    # ===== INFORMATION REQUEST QUERIES =====
    {
        "category": "Information Requests",
        "queries": [
            "show me my current state",
            "what's in my data",
            "give me a summary",
            "tell me about my state",
            "display my current state",
            "what's my current state",
            "show me the summary",
            "tell me what's in my data",
            "give me an overview",
            "what is in my current state"
        ]
    },
    
    # ===== HELP AND GUIDANCE QUERIES =====
    {
        "category": "Help & Guidance",
        "queries": [
            "help me",
            "what can you do",
            "how do I use this",
            "explain how this works",
            "guide me through this",
            "what are your capabilities",
            "how does this system work",
            "assist me please",
            "what can you help with",
            "explain to me how to use this"
        ]
    },
    
    # ===== GREETING QUERIES =====
    {
        "category": "Greetings",
        "queries": [
            "hello there",
            "hi there",
            "good morning",
            "hey there",
            "good afternoon",
            "good evening",
            "hello",
            "hi",
            "hey"
        ]
    },
    
    # ===== EDGE CASE QUERIES =====
    {
        "category": "Edge Cases",
        "queries": [
            "Process this JSON: {\"invalid_key\": \"value\"}",
            "update state: invalid_key=value",
            "show me something that doesn't exist",
            "process invalid json",
            "update my nonexistent_field",
            "what's the weather like",
            "tell me a joke",
            "calculate 2+2",
            "random query with no clear intent"
        ]
    },
    
    # ===== COMPLEX NATURAL LANGUAGE QUERIES =====
    {
        "category": "Complex Natural Language",
        "queries": [
            "I want to add some JSON data to my state",
            "Can you please update my user ID for me",
            "Would you mind showing me what's currently stored",
            "I need help understanding how to use this system",
            "Could you process this JSON data for me",
            "Please save this information to my state",
            "I'd like to see a summary of my current data",
            "Can you help me modify my JWT token",
            "I want to change my user ID to something else",
            "Please tell me what you can do to help me"
        ]
    }
]

def print_test_header():
    """Print a nice header for the test"""
    print("🚀 COMPREHENSIVE QUERY TEST SUITE")
    print("=" * 60)
    print("Testing your stateful agent system with various input queries")
    print("=" * 60)
    print()

def print_category_header(category):
    """Print a category header"""
    print(f"📋 {category.upper()}")
    print("-" * 40)

def print_query_test(query, index):
    """Print a formatted query test"""
    print(f"{index:2d}. '{query}'")

def print_test_summary():
    """Print test summary and instructions"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_queries = sum(len(cat["queries"]) for cat in COMPREHENSIVE_TEST_QUERIES)
    
    print(f"Total test queries: {total_queries}")
    print(f"Categories: {len(COMPREHENSIVE_TEST_QUERIES)}")
    print()
    
    print("🎯 HOW TO TEST:")
    print("1. Run: python main.py")
    print("2. Copy and paste each query one by one")
    print("3. Observe the system's response and state changes")
    print("4. Check if the intent is correctly recognized")
    print("5. Verify that state updates work as expected")
    print()
    
    print("✅ EXPECTED BEHAVIORS:")
    print("• JSON Processing: Should extract and update state with JSON data")
    print("• State Updates: Should modify specific state fields")
    print("• Information Requests: Should provide state summaries")
    print("• Help Requests: Should provide guidance and capabilities")
    print("• Greetings: Should respond politely")
    print("• Edge Cases: Should handle gracefully with error messages")
    print()

def main():
    """Run the comprehensive test suite"""
    print_test_header()
    
    query_index = 1
    
    for category_data in COMPREHENSIVE_TEST_QUERIES:
        category = category_data["category"]
        queries = category_data["queries"]
        
        print_category_header(category)
        
        for query in queries:
            print_query_test(query, query_index)
            query_index += 1
        
        print()
    
    print_test_summary()
    
    print("🎉 READY TO TEST!")
    print("Copy the queries above and test them in your system.")
    print("Your system should demonstrate excellent natural language understanding!")

if __name__ == "__main__":
    main()



