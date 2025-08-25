#!/usr/bin/env python3
"""
Test Commands for Stateful Agent System
A comprehensive list of commands to test all system functionality.
"""

def print_test_commands():
    """Print all test commands organized by category"""
    
    print("🚀 STATEFUL AGENT SYSTEM - TEST COMMANDS")
    print("=" * 60)
    print("Copy and paste these commands into your system when prompted 'You:'")
    print()
    
    # ===== GREETINGS & BASIC INTERACTION =====
    print("📋 1. GREETINGS & BASIC INTERACTION")
    print("-" * 40)
    greetings = [
        "hi",
        "hello",
        "hey there",
        "good morning",
        "how are you?",
        "what's up?"
    ]
    for cmd in greetings:
        print(f"   • {cmd}")
    print()
    
    # ===== HELP & GUIDANCE =====
    print("📋 2. HELP & GUIDANCE")
    print("-" * 40)
    help_commands = [
        "help",
        "help me",
        "what can you do?",
        "show me your capabilities",
        "how do I use this system?",
        "what commands are available?",
        "give me some examples"
    ]
    for cmd in help_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== JSON PROCESSING =====
    print("📋 3. JSON PROCESSING")
    print("-" * 40)
    json_commands = [
        'Process this JSON: {"_id": "user123", "user_id": "john_doe", "jwt": "token123"}',
        'Process this JSON: {"_id": "demo456", "user_id": "demo_user", "jwt": "demo_token_xyz"}',
        'Process this JSON: {"_id": "test789", "user_id": "test_user", "jwt": "test_jwt_123"}',
        'Process this JSON: {"_id": "admin001", "user_id": "admin", "jwt": "admin_secret_token"}',
        'Process this JSON: {"_id": "guest999", "user_id": "guest_user", "jwt": "guest_access_456"}'
    ]
    for cmd in json_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== STATE UPDATES =====
    print("📋 4. STATE UPDATES")
    print("-" * 40)
    update_commands = [
        "update the _id from user123 to user456",
        "change my user_id to new_username",
        "update the jwt token to new_token_123",
        "modify the _id to admin_user",
        "change user_id to updated_user",
        "update jwt to refreshed_token_789",
        "set _id to premium_user",
        "modify user_id to vip_user"
    ]
    for cmd in update_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== STATE INFORMATION =====
    print("📋 5. STATE INFORMATION")
    print("-" * 40)
    info_commands = [
        "show me my current state",
        "what's in my data?",
        "display my current state",
        "show me the current JSON",
        "what data do you have?",
        "show my state information",
        "display current data",
        "what's stored in my state?"
    ]
    for cmd in info_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== SUMMARIES =====
    print("📋 6. SUMMARIES")
    print("-" * 40)
    summary_commands = [
        "give me a summary",
        "summarize my data",
        "provide a summary of my state",
        "summarize the current information",
        "give me an overview",
        "create a summary",
        "summarize what you know about me"
    ]
    for cmd in summary_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== NATURAL LANGUAGE PROCESSING =====
    print("📋 7. NATURAL LANGUAGE PROCESSING")
    print("-" * 40)
    nlp_commands = [
        "append this query",
        "add this to my data",
        "store this information",
        "remember this for me",
        "save this data",
        "add this to my state",
        "include this in my information"
    ]
    for cmd in nlp_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== COMPLEX QUERIES =====
    print("📋 8. COMPLEX QUERIES")
    print("-" * 40)
    complex_commands = [
        "I want to add some JSON data to my state",
        "Can you process this information and update my profile?",
        "Please update my user information with new details",
        "I need to modify my current data structure",
        "Help me update my state with new information",
        "Process this data and add it to my current state",
        "I'd like to change some of my stored information"
    ]
    for cmd in complex_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== EDGE CASES =====
    print("📋 9. EDGE CASES")
    print("-" * 40)
    edge_commands = [
        "",  # Empty input
        "   ",  # Whitespace only
        "update",  # Incomplete command
        "process",  # Incomplete command
        "show",  # Incomplete command
        "invalid json: {this is not json}",
        "update non_existent_field to new_value",
        "process this: not a json string"
    ]
    for cmd in edge_commands:
        print(f"   • '{cmd}'")
    print()
    
    # ===== SYSTEM COMMANDS =====
    print("📋 10. SYSTEM COMMANDS")
    print("-" * 40)
    system_commands = [
        "exit",
        "quit",
        "bye",
        "goodbye",
        "end session",
        "stop"
    ]
    for cmd in system_commands:
        print(f"   • {cmd}")
    print()
    
    # ===== TESTING SEQUENCES =====
    print("📋 11. RECOMMENDED TESTING SEQUENCES")
    print("-" * 40)
    print("   Sequence 1 - Basic Flow:")
    print("   1. hi")
    print("   2. help me")
    print("   3. Process this JSON: {\"_id\": \"user123\", \"user_id\": \"john_doe\", \"jwt\": \"token123\"}")
    print("   4. show me my current state")
    print("   5. update the _id from user123 to user456")
    print("   6. show me my current state")
    print("   7. give me a summary")
    print("   8. exit")
    print()
    
    print("   Sequence 2 - Multiple Updates:")
    print("   1. Process this JSON: {\"_id\": \"demo456\", \"user_id\": \"demo_user\", \"jwt\": \"demo_token\"}")
    print("   2. update the user_id to new_username")
    print("   3. update the jwt to new_token_123")
    print("   4. show me my current state")
    print("   5. summarize my data")
    print("   6. exit")
    print()
    
    print("   Sequence 3 - Natural Language:")
    print("   1. hi there")
    print("   2. what can you do?")
    print("   3. I want to add some JSON data to my state")
    print("   4. Process this JSON: {\"_id\": \"test789\", \"user_id\": \"test_user\", \"jwt\": \"test_jwt\"}")
    print("   5. append this query")
    print("   6. what's in my data?")
    print("   7. exit")
    print()
    
    print("🎯 TESTING TIPS:")
    print("• Start with simple greetings to ensure the system is responsive")
    print("• Try JSON processing to see state updates")
    print("• Test state updates to verify persistence")
    print("• Use natural language to test intent recognition")
    print("• Check state before and after operations")
    print("• Try edge cases to test error handling")
    print()
    
    print("💡 EXPECTED BEHAVIORS:")
    print("• Greetings: Friendly responses")
    print("• Help: Guidance and capabilities")
    print("• JSON Processing: State updates with JSON data")
    print("• State Updates: Field modifications")
    print("• State Info: Current state display")
    print("• Summaries: Data overview")
    print("• Natural Language: Intent recognition")
    print("• Error Handling: Graceful error messages")
    print()
    
    print("🚀 Ready to test! Run 'python main.py' and start with any command above.")

if __name__ == "__main__":
    print_test_commands()
