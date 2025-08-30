#!/usr/bin/env python3
"""
Beautiful UI Demo
Showcases the enhanced UI with colored tables and human-friendly design
"""

import json
from datetime import datetime
from utils import (
    display_welcome, 
    create_table, 
    display_state, 
    display_agent_response, 
    display_error, 
    display_success,
    display_query_info,
    Colors
)

def demo_beautiful_ui():
    """Demonstrate the beautiful UI features"""
    
    print(f"{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} BEAUTIFUL UI DEMO {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    
    # Demo 1: Welcome Message
    print("\n" + "="*60)
    print("DEMO 1: Welcome Message")
    print("="*60)
    display_welcome()
    
    # Demo 2: Sample State Data
    print("\n" + "="*60)
    print("DEMO 2: Sample State Data")
    print("="*60)
    
    sample_state = {
        "_id": "user123",
        "user_id": "john_doe", 
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "email": "john.doe@example.com",
        "role": "admin",
        "last_login": "2025-08-25T23:45:00Z"
    }
    
    print(create_table(sample_state, "Current State Data"))
    
    # Demo 3: Session Statistics
    print("\n" + "="*60)
    print("DEMO 3: Session Statistics")
    print("="*60)
    
    stats = {
        "JSON Inputs": "8 entries",
        "User Queries": "15 queries", 
        "Last Update": "2025-08-25T23:45:00Z",
        "Session ID": "1cac585d...",
        "User ID": "john_doe",
        "Status": "Active",
        "Database": "MongoDB"
    }
    
    print(create_table(stats, "Session Statistics"))
    
    # Demo 4: Recent Queries
    print("\n" + "="*60)
    print("DEMO 4: Recent Queries")
    print("="*60)
    
    recent_queries = {
        "Query 1": "hi",
        "Query 2": "help me",
        "Query 3": "Process this JSON: {\"_id\": \"user123\", \"user_id\": \"john_doe\"}",
        "Query 4": "show me my current state",
        "Query 5": "update the _id from user123 to user456"
    }
    
    print(create_table(recent_queries, "Recent Queries"))
    
    # Demo 5: Agent Response
    print("\n" + "="*60)
    print("DEMO 5: Agent Response")
    print("="*60)
    
    sample_response = """Hello! I've successfully processed your JSON data and updated your state. 

Your current state now contains:
- User ID: john_doe
- JWT Token: Updated successfully
- Last modified: 2025-08-25T23:45:00Z

Is there anything else you'd like me to help you with?"""
    
    display_agent_response(sample_response, "Agent Response")
    
    # Demo 6: Success Message
    print("\n" + "="*60)
    print("DEMO 6: Success Message")
    print("="*60)
    
    display_success("JSON data processed and state updated successfully", "JSON Processing")
    
    # Demo 7: Error Message
    print("\n" + "="*60)
    print("DEMO 7: Error Message")
    print("="*60)
    
    display_error("Invalid JSON format. Please provide valid JSON data.", "JSON Error")
    
    # Demo 8: Query Processing
    print("\n" + "="*60)
    print("DEMO 8: Query Processing")
    print("="*60)
    
    sample_query = 'Process this JSON: {"_id": "demo123", "user_id": "demo_user", "jwt": "demo_token"}'
    display_query_info(sample_query)
    
    # Demo 9: Complex State Data
    print("\n" + "="*60)
    print("DEMO 9: Complex State Data")
    print("="*60)
    
    complex_state = {
        "user_profile": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "administrator"
        },
        "preferences": {
            "theme": "dark",
            "language": "en",
            "notifications": True
        },
        "security": {
            "two_factor": True,
            "last_password_change": "2025-07-15T10:30:00Z"
        },
        "activity": {
            "login_count": 156,
            "last_activity": "2025-08-25T23:45:00Z"
        }
    }
    
    # Flatten complex state for table display
    flattened_state = {}
    for category, data in complex_state.items():
        if isinstance(data, dict):
            for key, value in data.items():
                flattened_state[f"{category}.{key}"] = str(value)
        else:
            flattened_state[category] = str(data)
    
    print(create_table(flattened_state, "Complex State Data"))
    
    # Demo 10: System Status
    print("\n" + "="*60)
    print("DEMO 10: System Status")
    print("="*60)
    
    system_status = {
        "Database": "Connected",
        "Session Service": "MongoDB",
        "Agent System": "Operational",
        "API Status": "Rate Limited",
        "Memory Usage": "45.2 MB",
        "Uptime": "2 hours 15 minutes",
        "Version": "1.0.0"
    }
    
    print(create_table(system_status, "System Status"))
    
    # Final Summary
    print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.WHITE} DEMO COMPLETE {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}The beautiful UI features demonstrated:{Colors.RESET}")
    print(f"{Colors.YELLOW}• Colored tables with proper formatting{Colors.RESET}")
    print(f"{Colors.YELLOW}• Human-friendly design without emojis{Colors.RESET}")
    print(f"{Colors.YELLOW}• Clear section headers and separators{Colors.RESET}")
    print(f"{Colors.YELLOW}• Consistent color scheme throughout{Colors.RESET}")
    print(f"{Colors.YELLOW}• Easy-to-read data presentation{Colors.RESET}")
    print(f"{Colors.YELLOW}• Professional appearance{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

def demo_interactive_commands():
    """Show sample commands for testing"""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} SAMPLE COMMANDS FOR TESTING {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    
    commands = {
        "Greeting": "hi",
        "Help": "help me",
        "JSON Processing": 'Process this JSON: {"_id": "user123", "user_id": "john_doe", "jwt": "token123"}',
        "State Info": "show me my current state",
        "State Update": "update the _id from user123 to user456",
        "Summary": "give me a summary",
        "Exit": "exit"
    }
    
    print(create_table(commands, "Sample Commands"))
    
    print(f"{Colors.GRAY}To test the full system, run: python main.py{Colors.RESET}")

if __name__ == "__main__":
    demo_beautiful_ui()
    demo_interactive_commands()



