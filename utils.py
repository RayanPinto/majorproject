from datetime import datetime
import json
import traceback
from google.genai import types
from typing import Dict, Any, Optional

# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

# === STATE UPDATE FUNCTIONS ===
# Simplified - no history tracking needed

def log_json_input(session_service, app_name, user_id, session_id, json_data):
    """Log JSON input with enhanced error handling"""
    try:
        if not session_service:
            raise ValueError("Session service is not available")
        
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        json_inputs = session.state.get("json_inputs", [])
        json_inputs.append({
            "json_data": json_data,
            "timestamp": datetime.now().isoformat()
        })

        updated_state = session.state.copy()
        updated_state["json_inputs"] = json_inputs
        updated_state["last_update"] = datetime.now().isoformat()

        session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id, state=updated_state)
        print(f"{Colors.GREEN}✅ JSON input logged successfully{Colors.RESET}")
        
    except ValueError as e:
        print(f"{Colors.RED}❌ Validation Error: {e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error logging JSON input: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Stack trace: {traceback.format_exc()}{Colors.RESET}")

# Merged display_state (removed duplicate; shows current keys including current_state)
def display_state(session_service, app_name, user_id, session_id, label="Current State"):
    """Display state with enhanced error handling"""
    try:
        if not session_service:
            print(f"{Colors.YELLOW}⚠️ Session service not available{Colors.RESET}")
            return
        
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if not session:
            print(f"{Colors.YELLOW}⚠️ Session not found: {session_id}{Colors.RESET}")
            return
        
        print(f"\n{'-' * 10} {label} {'-' * 10}")
        
        # Show only state management related fields
        current_state = session.state.get("current_state", {})
        json_inputs = session.state.get("json_inputs", [])
        last_update = session.state.get("last_update", "Never")
        
        print(f"📊 Current State: {json.dumps(current_state, indent=2)}")
        print(f"📥 JSON Inputs: {len(json_inputs)} entries")
        print(f"🕒 Last Update: {last_update}")
        
        print("-" * (22 + len(label)))
        
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}❌ JSON Error displaying state: {e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error displaying state: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Stack trace: {traceback.format_exc()}{Colors.RESET}")

# === AGENT RESPONSE HANDLING ===

async def process_agent_response(event):
    print(f"Event ID: {event.id}, Author: {event.author}")
    has_specific_part = False

    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    final_response = None
    if not has_specific_part and event.is_final_response():
        if event.content and event.content.parts and hasattr(event.content.parts[0], "text"):
            final_response = event.content.parts[0].text.strip()
            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ AGENT RESPONSE ═════════════════════════════════════════{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            print(
                f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚═════════════════════════════════════════════════════════════{Colors.RESET}\n"
            )
        else:
            print(
                f"{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Final Agent Response: [No text]{Colors.RESET}\n"
            )

    return final_response

async def call_agent_async(runner, user_id, session_id, query):
    """Call agent with enhanced error handling"""
    try:
        if not runner:
            raise ValueError("Agent runner is not available")
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        content = types.Content(role="user", parts=[types.Part(text=query)])
        print(f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}")
        final_response_text = None
        agent_name = None

        display_state(runner.session_service, runner.app_name, user_id, session_id, "State BEFORE processing")

        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.author:
                    agent_name = event.author

                response = await process_agent_response(event)
                if response:
                    final_response_text = response
                    
        except Exception as e:
            print(f"{Colors.BG_RED}{Colors.WHITE}❌ ERROR during agent run: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}Stack trace: {traceback.format_exc()}{Colors.RESET}")

        # No need to track agent responses - focus on state management only

        display_state(runner.session_service, runner.app_name, user_id, session_id, "State AFTER processing")
        print(f"{Colors.YELLOW}{'-' * 30}{Colors.RESET}")
        return final_response_text
        
    except ValueError as e:
        print(f"{Colors.RED}❌ Validation Error: {e}{Colors.RESET}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ Unexpected error in agent call: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Stack trace: {traceback.format_exc()}{Colors.RESET}")
        return None
