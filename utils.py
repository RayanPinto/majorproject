#!/usr/bin/env python3
"""
Utility functions for the Stateful Agent System
Enhanced with beautiful colored UI and table displays
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import shutil

# ANSI Color Codes for beautiful UI
class Colors:
    HEADER = '\033[95m'      # Purple
    BLUE = '\033[94m'        # Blue
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    RESET = '\033[0m'        # Reset
    WHITE = '\033[97m'       # White
    GRAY = '\033[90m'        # Gray
    BLACK = '\033[30m'       # Black
    MAGENTA = '\033[35m'     # Magenta
    BG_BLACK = '\033[40m'    # Background Black
    BG_BLUE = '\033[44m'     # Background Blue
    BG_GREEN = '\033[42m'    # Background Green
    BG_YELLOW = '\033[43m'   # Background Yellow
    BG_RED = '\033[41m'      # Background Red
    BG_MAGENTA = '\033[45m'  # Background Magenta
    BG_CYAN = '\033[46m'     # Background Cyan
    BG_WHITE = '\033[47m'    # Background White

def create_table(data: Dict[str, Any], title: str = "Data Table") -> str:
    """Create a beautiful formatted table from dictionary data"""
    if not data:
        return f"{Colors.GRAY}No data available{Colors.RESET}"
    
    # Calculate column widths
    max_key_width = max(len(str(key)) for key in data.keys()) if data else 0
    max_value_width = max(len(str(value)) for value in data.values()) if data else 0
    
    # Ensure minimum widths
    key_width = max(max_key_width, 15)
    value_width = max(max_value_width, 20)
    
    # Create table header
    table = f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {title} {Colors.RESET}\n"
    table += f"{Colors.CYAN}{'=' * (key_width + value_width + 7)}{Colors.RESET}\n"
    table += f"{Colors.BOLD}{Colors.BLUE}{'Key':<{key_width}} | {'Value':<{value_width}}{Colors.RESET}\n"
    table += f"{Colors.CYAN}{'-' * key_width}-+-{'-' * value_width}{Colors.RESET}\n"
    
    # Add data rows
    for key, value in data.items():
        # Truncate long values for display
        display_value = str(value)
        if len(display_value) > value_width - 2:
            display_value = display_value[:value_width - 5] + "..."
        
        table += f"{Colors.WHITE}{str(key):<{key_width}} | {Colors.YELLOW}{display_value:<{value_width}}{Colors.RESET}\n"
    
    table += f"{Colors.CYAN}{'=' * (key_width + value_width + 7)}{Colors.RESET}\n"
    return table

def display_state(session_service, app_name: str, user_id: str, session_id: str, context: str = "Current State"):
    """Display the current state in a beautiful formatted table"""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        if not session:
            print(f"{Colors.RED}Error: Session not found{Colors.RESET}")
            return
        
        current_state = session.state.get("current_state", {})
        json_inputs = session.state.get("json_inputs", [])
        last_update = session.state.get("last_update", "Never")
        user_queries = session.state.get("user_queries", [])
        
        # Create main state table
        print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.WHITE} {context} {Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        
        # Current State Table
        if current_state:
            print(create_table(current_state, "Current State Data"))
        else:
            print(f"{Colors.GRAY}No current state data available{Colors.RESET}")
        
        # Statistics Table
        stats = {
            "JSON Inputs": f"{len(json_inputs)} entries",
            "User Queries": f"{len(user_queries)} queries",
            "Last Update": last_update,
            "Session ID": session_id[:8] + "...",
            "User ID": user_id
        }
        print(create_table(stats, "Session Statistics"))
        
        # Recent Queries Table (last 5)
        if user_queries:
            recent_queries = user_queries[-5:]  # Last 5 queries
            queries_data = {}
            for i, query in enumerate(recent_queries, 1):
                queries_data[f"Query {i}"] = query[:50] + "..." if len(query) > 50 else query
            print(create_table(queries_data, "Recent Queries"))
        
    except Exception as e:
        print(f"{Colors.RED}Error displaying state: {e}{Colors.RESET}")

def display_agent_response(response_text: str, agent_name: str = "Agent"):
    """Display agent response in a beautiful format"""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {agent_name} Response {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}{response_text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")

def display_error(error_message: str, error_type: str = "Error"):
    """Display error messages in a beautiful format"""
    print(f"\n{Colors.BOLD}{Colors.BG_RED}{Colors.WHITE} {error_type} {Colors.RESET}")
    print(f"{Colors.RED}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.YELLOW}{error_message}{Colors.RESET}")
    print(f"{Colors.RED}{'=' * 60}{Colors.RESET}")

def display_success(message: str, title: str = "Success"):
    """Display success messages in a beautiful format"""
    print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.WHITE} {title} {Colors.RESET}")
    print(f"{Colors.GREEN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}{message}{Colors.RESET}")
    print(f"{Colors.GREEN}{'=' * 60}{Colors.RESET}")

def display_welcome():
    """Display welcome message with beautiful formatting"""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} Stateful JSON Assistant {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}Welcome! You can:{Colors.RESET}")
    print(f"{Colors.YELLOW}• Process JSON data{Colors.RESET}")
    print(f"{Colors.YELLOW}• Update state information{Colors.RESET}")
    print(f"{Colors.YELLOW}• Request summaries{Colors.RESET}")
    print(f"{Colors.YELLOW}• View current state{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.GRAY}Type 'exit' or 'quit' to end the conversation{Colors.RESET}\n")

def display_query_info(query: str):
    """Display query information in a beautiful format"""
    print(f"\n{Colors.BOLD}{Colors.BG_YELLOW}{Colors.WHITE} Processing Query {Colors.RESET}")
    print(f"{Colors.YELLOW}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}Query: {Colors.CYAN}{query}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'=' * 60}{Colors.RESET}")

def add_user_query_to_history(session_service, app_name: str, user_id: str, session_id: str, query: str):
    """Add user query to history with error handling"""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if session:
            if "user_queries" not in session.state:
                session.state["user_queries"] = []
            session.state["user_queries"].append(query)
            session.state["last_update"] = datetime.now().isoformat()
            session_service.update_session(app_name, user_id, session_id, session.state)
    except Exception as e:
        display_error(f"Error adding query to history: {e}", "Warning")

# ===== Enhanced two-column animated dashboard =====

def _format_seconds(sec: float) -> str:
    try:
        return f"{float(sec):.2f}s"
    except Exception:
        return str(sec)

def summarize_behavior_from_state(session_state: Dict[str, Any], max_items: int = 6) -> List[str]:
    """Create concise behavior lines from alerts and active span."""
    alerts: List[Dict[str, Any]] = session_state.get("alerts", [])
    aggregates: Dict[str, Any] = session_state.get("aggregates", {})
    lines: List[str] = []

    active = aggregates.get("active_span")
    if active and isinstance(active, dict) and all(k in active for k in ("label", "t_start", "t_end")):
        lbl = active.get("label", "unknown")
        t0 = _format_seconds(active.get("t_start", 0.0))
        t1 = _format_seconds(active.get("t_end", 0.0))
        lines.append(f"Currently {lbl} from {t0} to {t1} (ongoing)")

    closed = [a for a in alerts if a.get("kind") == "emotion_span"]
    closed = sorted(closed, key=lambda x: x.get("t_end", 0.0), reverse=True)
    for a in closed[:max_items]:
        lbl = a.get("label", "unknown")
        t0 = _format_seconds(a.get("t_start", 0.0))
        t1 = _format_seconds(a.get("t_end", 0.0))
        avg = a.get("avg_score")
        if isinstance(avg, (int, float)):
            lines.append(f"{lbl} from {t0} to {t1} (avg {avg:.2f})")
        else:
            lines.append(f"{lbl} from {t0} to {t1}")

    if not lines:
        return ["No behavior spans detected yet."]
    return lines

def _pad_or_trim(text: str, width: int) -> str:
    if len(text) > width:
        return text[: max(0, width - 3)] + "..."
    return text + (" " * (width - len(text)))

def render_two_column_dashboard(session_service, app_name: str, user_id: str, session_id: str, title: str = "Real-time Dashboard", animate: bool = True) -> None:
    """Render a clean two-column dashboard: left=state updates, right=behavior summary.

    Avoids emojis and logos; uses subtle colors and simple animations.
    """
    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        print(f"{Colors.RED}Error: Session not found{Colors.RESET}")
        return

    # Prepare data
    cs = session.state.get("current_state", {})
    left_rows = []
    # Focus on key fields and live stats
    left_rows.append(("Last Update", str(session.state.get("last_update", "Never"))))
    left_rows.append(("Last Ingest", str(session.state.get("last_ingest_at", "Never"))))
    if "last_label" in cs:
        left_rows.append(("Last Label", str(cs.get("last_label"))))
    if "last_label_score" in cs:
        left_rows.append(("Label Score", str(cs.get("last_label_score"))))
    left_rows.append(("Timeline Events", str(len(session.state.get("timeline", [])))))
    left_rows.append(("Alerts", str(len(session.state.get("alerts", [])))))

    behavior_lines = summarize_behavior_from_state(session.state, max_items=8)

    # Terminal sizing and layout
    term_width = shutil.get_terminal_size((120, 40)).columns
    total_width = max(80, min(term_width, 160))
    gutter = 4
    col_width = (total_width - gutter) // 2

    # Clear screen and draw header with a subtle pulse
    print("\033[2J\033[H", end="")
    border_color = Colors.CYAN
    header = f"{Colors.BOLD}{border_color}{'=' * total_width}{Colors.RESET}"
    print(header)
    print(f"{Colors.BOLD}{Colors.WHITE}{title:^{total_width}}{Colors.RESET}")
    print(header)

    # Column titles
    left_title = f"{Colors.BLUE}State Updates{Colors.RESET}"
    right_title = f"{Colors.BLUE}Behavior Summary{Colors.RESET}"

    print(_pad_or_trim(left_title, col_width) + (" " * gutter) + _pad_or_trim(right_title, col_width))
    print(_pad_or_trim(border_color + ("-" * col_width) + Colors.RESET, col_width) + (" " * gutter) + _pad_or_trim(border_color + ("-" * col_width) + Colors.RESET, col_width))

    # Compute max rows
    max_rows = max(len(left_rows), len(behavior_lines))

    for i in range(max_rows):
        l = left_rows[i] if i < len(left_rows) else ("", "")
        r = behavior_lines[i] if i < len(behavior_lines) else ""
        left_text = f"{Colors.WHITE}{l[0]}{Colors.RESET}: {Colors.YELLOW}{l[1]}{Colors.RESET}" if l[0] else ""
        line = _pad_or_trim(left_text, col_width) + (" " * gutter) + _pad_or_trim(f"{Colors.WHITE}{r}{Colors.RESET}", col_width)
        print(line)
        if animate:
            time.sleep(0.03)

    print(header)

async def process_agent_response(event):
    """Process agent response events - from reference code"""
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
    """Call the agent asynchronously with beautiful display - using reference pattern"""
    try:
        # Create proper Content object using Google GenAI types (exact pattern from reference)
        from google.genai import types
        content = types.Content(role="user", parts=[types.Part(text=query)])
        
        display_query_info(query)
        
        # Display state before processing
        display_state(runner.session_service, runner.app_name, user_id, session_id, "State Before Processing")
        
        print(f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}")
        final_response_text = None
        agent_name = None

        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.author:
                    agent_name = event.author

                # Process agent response using reference pattern
                response = await process_agent_response(event)
                if response:
                    final_response_text = response
                    
        except Exception as e:
            display_error(f"Agent communication error: {e}", "Communication Error")
            final_response_text = "I'm having trouble connecting to the AI service right now. Your state operations are still working though!"

        # Display agent response
        if final_response_text:
            display_agent_response(final_response_text, "Agent Response")
        else:
            display_agent_response("Command processed successfully.", "System Response")

        # Process state updates (this works regardless of agent issues)
        process_state_updates(runner.session_service, runner.app_name, user_id, session_id, query, final_response_text)
        
        # Display state after processing
        display_state(runner.session_service, runner.app_name, user_id, session_id, "State After Processing")

        # Render concise two-column dashboard for presentation
        render_two_column_dashboard(runner.session_service, runner.app_name, user_id, session_id)
        
    except Exception as e:
        display_error(f"Error during agent run: {e}", "Agent Error")

def process_state_updates(session_service, app_name: str, user_id: str, session_id: str, query: str, response: str):
    """Process state updates based on user query and agent response"""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        if not session:
            display_error("Session not found", "Warning")
            return
        
        # Initialize state if needed
        if "current_state" not in session.state:
            session.state["current_state"] = {}
        if "json_inputs" not in session.state:
            session.state["json_inputs"] = []
        if "last_update" not in session.state:
            session.state["last_update"] = datetime.now().isoformat()
        
        # Process JSON processing commands
        if query.lower().startswith("process this json:"):
            json_part = query[len("process this json:"):].strip()
            try:
                json_data = json.loads(json_part)
                session.state["current_state"] = json_data
                session.state["json_inputs"].append(json_data)
                session.state["last_update"] = datetime.now().isoformat()
                display_success("JSON data processed and state updated successfully", "JSON Processing")
            except json.JSONDecodeError:
                display_error("Invalid JSON format", "JSON Error")
        
        # Process state update commands
        elif "update" in query.lower() or "change" in query.lower() or "modify" in query.lower():
            # Extract field and value from update command
            update_pattern = r"update\s+(?:the\s+)?(\w+)\s+(?:from\s+\w+\s+)?to\s+(\w+)"
            match = re.search(update_pattern, query.lower())
            if match:
                field = match.group(1)
                new_value = match.group(2)
                if field in session.state["current_state"]:
                    session.state["current_state"][field] = new_value
                    session.state["last_update"] = datetime.now().isoformat()
                    display_success(f"Updated {field} to {new_value}", "State Update")
                else:
                    display_error(f"Field '{field}' not found in current state", "Update Error")
        
        # Update session
        session_service.update_session(app_name, user_id, session_id, session.state)
        
    except Exception as e:
        display_error(f"Error processing state updates: {e}", "State Update Error")
