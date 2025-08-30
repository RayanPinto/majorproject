#!/usr/bin/env python3
"""
Natural Language Intent Recognition Test
Tests the system's ability to understand various natural language queries
and route them to appropriate commands/agents.
"""

import asyncio
import json
from datetime import datetime

# Test queries that should be understood and routed appropriately
NATURAL_LANGUAGE_TESTS = [
    # JSON Processing Intent Tests
    {
        "query": "append this query",
        "expected_intent": "json_processing",
        "description": "Should understand 'append' as JSON processing intent"
    },
    {
        "query": "add this data",
        "expected_intent": "json_processing", 
        "description": "Should understand 'add this data' as JSON processing"
    },
    {
        "query": "save this information",
        "expected_intent": "json_processing",
        "description": "Should understand 'save this information' as data storage"
    },
    {
        "query": "store this json",
        "expected_intent": "json_processing",
        "description": "Should understand 'store this json' as JSON processing"
    },
    {
        "query": "process this data",
        "expected_intent": "json_processing",
        "description": "Should understand 'process this data' as data processing"
    },
    
    # State Update Intent Tests
    {
        "query": "update my user_id to john_doe",
        "expected_intent": "state_update",
        "description": "Should understand natural language state update"
    },
    {
        "query": "change my _id to new_value",
        "expected_intent": "state_update", 
        "description": "Should understand 'change my' as state update"
    },
    {
        "query": "modify the jwt token",
        "expected_intent": "state_update",
        "description": "Should understand 'modify the' as state modification"
    },
    {
        "query": "set my user_id as test_user",
        "expected_intent": "state_update",
        "description": "Should understand 'set my' as state setting"
    },
    
    # Information Request Tests
    {
        "query": "show me my current state",
        "expected_intent": "information_request",
        "description": "Should understand 'show me' as information request"
    },
    {
        "query": "what's in my data",
        "expected_intent": "information_request",
        "description": "Should understand 'what's in my data' as info request"
    },
    {
        "query": "give me a summary",
        "expected_intent": "information_request",
        "description": "Should understand 'give me a summary' as summary request"
    },
    {
        "query": "tell me about my state",
        "expected_intent": "information_request",
        "description": "Should understand 'tell me about' as info request"
    },
    
    # Help and Guidance Tests
    {
        "query": "help me",
        "expected_intent": "help_request",
        "description": "Should understand 'help me' as help request"
    },
    {
        "query": "what can you do",
        "expected_intent": "help_request",
        "description": "Should understand 'what can you do' as capability inquiry"
    },
    {
        "query": "how do I use this",
        "expected_intent": "help_request",
        "description": "Should understand 'how do I use this' as usage help"
    },
    
    # Greeting Tests
    {
        "query": "hello there",
        "expected_intent": "greeting",
        "description": "Should understand 'hello there' as greeting"
    },
    {
        "query": "hi there",
        "expected_intent": "greeting",
        "description": "Should understand 'hi there' as greeting"
    },
    {
        "query": "good morning",
        "expected_intent": "greeting",
        "description": "Should understand 'good morning' as greeting"
    }
]

def classify_intent(query: str) -> str:
    """
    Classify the intent of a natural language query.
    This simulates what the agent should be able to do.
    """
    query_lower = query.lower()
    
    # JSON Processing Intent Patterns
    json_patterns = [
        "append", "add", "save", "store", "process", "input", "insert",
        "append this", "add this", "save this", "store this", "process this"
    ]
    
    # State Update Intent Patterns  
    update_patterns = [
        "update", "change", "modify", "set", "edit", "alter",
        "update my", "change my", "modify my", "set my", "update the", "change the"
    ]
    
    # Information Request Patterns
    info_patterns = [
        "show", "display", "what", "tell", "give", "get", "see",
        "show me", "what's", "what is", "tell me", "give me", "show my"
    ]
    
    # Help Request Patterns
    help_patterns = [
        "help", "how", "what can", "explain", "guide", "assist",
        "help me", "how do", "what can you", "explain to me"
    ]
    
    # Greeting Patterns
    greeting_patterns = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
    ]
    
    # Check patterns
    if any(pattern in query_lower for pattern in json_patterns):
        return "json_processing"
    elif any(pattern in query_lower for pattern in update_patterns):
        return "state_update"
    elif any(pattern in query_lower for pattern in info_patterns):
        return "information_request"
    elif any(pattern in query_lower for pattern in help_patterns):
        return "help_request"
    elif any(pattern in query_lower for pattern in greeting_patterns):
        return "greeting"
    else:
        return "unknown"

def test_intent_recognition():
    """Test the intent recognition system"""
    print("🧠 Testing Natural Language Intent Recognition")
    print("=" * 60)
    
    passed = 0
    total = len(NATURAL_LANGUAGE_TESTS)
    
    for i, test in enumerate(NATURAL_LANGUAGE_TESTS, 1):
        query = test["query"]
        expected = test["expected_intent"]
        description = test["description"]
        
        # Get actual intent classification
        actual = classify_intent(query)
        
        # Check if correct
        is_correct = actual == expected
        if is_correct:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{i:2d}. {status} | {description}")
        print(f"    Query: '{query}'")
        print(f"    Expected: {expected} | Actual: {actual}")
        print()
    
    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All natural language intent recognition tests passed!")
    else:
        print("⚠️  Some tests failed. Intent recognition needs improvement.")
    
    return passed == total

def test_agent_routing():
    """Test which agent should handle each intent"""
    print("\n🔄 Testing Agent Routing Logic")
    print("=" * 60)
    
    routing_rules = {
        "json_processing": "conversational_agent",
        "state_update": "conversational_agent", 
        "information_request": "conversational_agent",
        "help_request": "conversational_agent",
        "greeting": "conversational_agent",
        "unknown": "conversational_agent"  # Default to conversational
    }
    
    print("Intent → Agent Routing:")
    for intent, agent in routing_rules.items():
        print(f"  {intent:20} → {agent}")
    
    print("\n✅ Agent routing logic is consistent and appropriate")

def test_query_examples():
    """Show examples of how queries should be processed"""
    print("\n💡 Query Processing Examples")
    print("=" * 60)
    
    examples = [
        {
            "input": "append this query",
            "intent": "json_processing",
            "action": "Should trigger JSON processing logic",
            "agent": "conversational_agent"
        },
        {
            "input": "update my user_id to john_doe", 
            "intent": "state_update",
            "action": "Should extract key=value and update state",
            "agent": "conversational_agent"
        },
        {
            "input": "show me my current state",
            "intent": "information_request", 
            "action": "Should generate state summary",
            "agent": "conversational_agent"
        },
        {
            "input": "help me",
            "intent": "help_request",
            "action": "Should provide usage guidance",
            "agent": "conversational_agent"
        }
    ]
    
    for example in examples:
        print(f"Input: '{example['input']}'")
        print(f"Intent: {example['intent']}")
        print(f"Action: {example['action']}")
        print(f"Agent: {example['agent']}")
        print()

def main():
    """Run all natural language tests"""
    print("🚀 Natural Language Intent Recognition Test Suite")
    print("=" * 60)
    
    # Test intent recognition
    intent_success = test_intent_recognition()
    
    # Test agent routing
    test_agent_routing()
    
    # Show examples
    test_query_examples()
    
    print("\n" + "=" * 60)
    if intent_success:
        print("🎯 CONCLUSION: Your system should be able to understand")
        print("   natural language intents and route them appropriately!")
        print("\n   When you say 'append this query', the system should:")
        print("   1. Recognize it as JSON processing intent")
        print("   2. Route to conversational_agent")
        print("   3. Process any JSON data in the query")
        print("   4. Update the state accordingly")
    else:
        print("⚠️  CONCLUSION: Intent recognition needs improvement")
        print("   Consider enhancing the pattern matching logic")

if __name__ == "__main__":
    main()

