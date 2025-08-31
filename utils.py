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
        
        # Get behavioral data from new structure
        current_behavior = session.state.get("current_behavior", {})
        behavioral_data = session.state.get("behavioral_data", [])
        last_update = session.state.get("last_update", "Never")
        user_queries = session.state.get("user_queries", [])
        candidate_info = session.state.get("candidate_info", {})
        
        # Create main state table
        print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.WHITE} {context} {Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        
        # Display candidate info if available
        if candidate_info.get("candidate_id"):
            candidate_table = {
                "Candidate ID": candidate_info.get("candidate_id", "Unknown"),
                "Session ID": candidate_info.get("session_id", "Unknown"),
                "Interview Start": candidate_info.get("interview_start", "Unknown")
            }
            print(create_table(candidate_table, "Candidate Information"))
            print()
        
        # Display current behavioral state
        if current_behavior.get("behavior_profile"):
            behavior_profile = current_behavior["behavior_profile"]
            behavior_table = {
                "Confidence Level": f"{behavior_profile.get('confidence_level', 0):.2f}",
                "Engagement Level": f"{behavior_profile.get('engagement_level', 0):.2f}",
                "Stress Level": f"{behavior_profile.get('stress_level', 0):.2f}",
                "Emotional Valence": behavior_profile.get('emotional_valence', 'unknown').title()
            }
            print(create_table(behavior_table, "Current Behavioral State"))
        else:
            print(f"{Colors.GRAY}No behavioral data available{Colors.RESET}")
        
        # Statistics Table
        stats = {
            "Behavioral Data Points": f"{len(behavioral_data)} entries",
            "User Queries": f"{len(user_queries)} queries",
            "Last Update": last_update,
            "Session ID": session_id[:8] + "...",
            "User ID": user_id
        }
        print(create_table(stats, "Session Statistics"))
        
        # Display recent behavioral data
        if behavioral_data:
            print(f"\n{Colors.BOLD}{Colors.BG_MAGENTA}{Colors.WHITE} Recent Behavioral Data {Colors.RESET}")
            for i, entry in enumerate(behavioral_data[-3:], 1):
                timestamp = entry.get('timestamp', 'Unknown')
                behavior_data_entry = entry.get('behavior_data', {})
                metadata = behavior_data_entry.get('metadata', {})
                candidate_id = metadata.get('candidate_id', 'Unknown')
                print(f"{Colors.CYAN}{i}.{Colors.RESET} {timestamp}")
                print(f"   {Colors.GRAY}Candidate: {candidate_id}{Colors.RESET}")
        
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
    """Create concise behavior lines from behavioral data and insights."""
    behavioral_data: List[Dict[str, Any]] = session_state.get("behavioral_data", [])
    behavioral_insights: Dict[str, Any] = session_state.get("behavioral_insights", {})
    current_behavior: Dict[str, Any] = session_state.get("current_behavior", {})
    lines: List[str] = []

    # Show current behavioral state
    if current_behavior.get("behavior_profile"):
        behavior_profile = current_behavior["behavior_profile"]
        confidence = behavior_profile.get("confidence_level", 0)
        engagement = behavior_profile.get("engagement_level", 0)
        stress = behavior_profile.get("stress_level", 0)
        valence = behavior_profile.get("emotional_valence", "unknown")
        
        lines.append(f"Current: {valence.title()} (Conf: {confidence:.2f}, Eng: {engagement:.2f}, Stress: {stress:.2f})")

    # Show behavioral insights
    if behavioral_insights.get("emotional_pattern"):
        lines.append(f"Pattern: {behavioral_insights['emotional_pattern']}")
    
    if behavioral_insights.get("confidence_pattern"):
        lines.append(f"Confidence: {behavioral_insights['confidence_pattern']}")

    # Show recent behavioral data points
    if behavioral_data:
        recent_data = behavioral_data[-max_items:]
        for entry in recent_data:
            timestamp = entry.get("timestamp", "Unknown")
            behavior_data_entry = entry.get("behavior_data", {})
            metadata = behavior_data_entry.get("metadata", {})
            candidate_id = metadata.get("candidate_id", "Unknown")
            behavior_profile = behavior_data_entry.get("behavior_profile", {})
            valence = behavior_profile.get("emotional_valence", "unknown")
            
            # Format timestamp for display
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
            
            lines.append(f"{time_str}: {valence.title()} ({candidate_id})")

    if not lines:
        return ["No behavioral data available yet."]
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

    # Prepare behavioral data
    current_behavior = session.state.get("current_behavior", {})
    behavioral_data = session.state.get("behavioral_data", [])
    candidate_info = session.state.get("candidate_info", {})
    
    left_rows = []
    # Focus on behavioral metrics and live stats
    left_rows.append(("Last Update", str(session.state.get("last_update", "Never"))))
    left_rows.append(("Last Ingest", str(session.state.get("last_behavior_ingest", "Never"))))
    
    if candidate_info.get("candidate_id"):
        left_rows.append(("Candidate", str(candidate_info.get("candidate_id", "Unknown"))))
    
    if current_behavior.get("behavior_profile"):
        behavior_profile = current_behavior["behavior_profile"]
        confidence = behavior_profile.get("confidence_level", 0)
        engagement = behavior_profile.get("engagement_level", 0)
        stress = behavior_profile.get("stress_level", 0)
        left_rows.append(("Confidence", f"{confidence:.2f}"))
        left_rows.append(("Engagement", f"{engagement:.2f}"))
        left_rows.append(("Stress", f"{stress:.2f}"))
    
    left_rows.append(("Data Points", str(len(behavioral_data))))
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
            # Bypass agent communication for now and use direct behavioral analysis
            session = runner.session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
            if session:
                # Use direct behavioral analysis instead of agent communication
                from manager.sub_agents.conversational_agent import handle_conversational_query
                final_response_text = handle_conversational_query(query, session.state)
            else:
                final_response_text = "Session not found for analysis."
                    
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
    """Process behavioral state updates based on user query and agent response"""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        if not session:
            display_error("Session not found", "Warning")
            return
        
        # Update last update timestamp
        if "last_update" not in session.state:
            session.state["last_update"] = datetime.now().isoformat()
        else:
            session.state["last_update"] = datetime.now().isoformat()
        
        # Update session
        session_service.update_session(app_name, user_id, session_id, session.state)
        
    except Exception as e:
        display_error(f"Error processing state updates: {e}", "State Update Error")

def display_behavioral_analysis(session_service, app_name: str, user_id: str, session_id: str):
    """Display comprehensive behavioral analysis dashboard."""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if not session:
            print(f"{Colors.RED}❌ No session found for behavioral analysis{Colors.RESET}")
            return

        state = session.state
        current_behavior = state.get("current_behavior", {})
        behavioral_insights = state.get("behavioral_insights", {})

        print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} 🤖 Behavioral Analysis Dashboard {Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")

        # Candidate Info
        candidate_info = state.get("candidate_info", {})
        if candidate_info.get("candidate_id"):
            print(f"{Colors.BOLD}{Colors.GREEN}👤 Candidate:{Colors.RESET} {candidate_info['candidate_id']}")
            if candidate_info.get("session_id"):
                print(f"{Colors.BOLD}{Colors.GREEN}📋 Session:{Colors.RESET} {candidate_info['session_id']}")
            print()

        # Behavioral Metrics
        behavior_profile = current_behavior.get("behavior_profile", {})
        if behavior_profile:
            print(f"{Colors.BOLD}{Colors.YELLOW}📈 Behavioral Metrics:{Colors.RESET}")
            confidence = behavior_profile.get("confidence_level", 0)
            engagement = behavior_profile.get("engagement_level", 0)
            stress = behavior_profile.get("stress_level", 0)
            valence = behavior_profile.get("emotional_valence", "unknown")

            # Visual bars for metrics
            def create_bar(value, max_val=1.0, length=20):
                filled = int((value / max_val) * length)
                bar = "█" * filled + "░" * (length - filled)
                return bar

            print(f"   🎯 Confidence: [{create_bar(confidence)}] {confidence:.2f}")
            print(f"   🔥 Engagement: [{create_bar(engagement)}] {engagement:.2f}")
            print(f"   😰 Stress: [{create_bar(stress)}] {stress:.2f}")
            print(f"   💭 Emotional State: {Colors.MAGENTA}{valence.title()}{Colors.RESET}")
            print()

        # Facial Expressions
        video_features = current_behavior.get("video_features", {})
        facial_expressions = video_features.get("facial_expressions", [])
        if facial_expressions:
            print(f"{Colors.BOLD}{Colors.CYAN}😊 Facial Expressions:{Colors.RESET}")
            for expr in facial_expressions[-3:]:  # Show last 3
                time_sec = expr.get("time_sec", 0)
                expression = expr.get("expression", "unknown")
                confidence = expr.get("confidence", 0)
                print(f"   {time_sec:.1f}s: {Colors.GREEN}{expression}{Colors.RESET} ({confidence:.2f})")
            print()

        # Speech Analysis
        audio_features = current_behavior.get("audio_features", {})
        speech_segments = audio_features.get("speech_segments", [])
        if speech_segments:
            print(f"{Colors.BOLD}{Colors.GRAY}🎤 Recent Speech:{Colors.RESET}")
            for segment in speech_segments[-2:]:  # Show last 2
                start = segment.get("start_sec", 0)
                text = segment.get("text", "")[:50]  # Truncate long text
                print(f"   {start:.1f}s: {Colors.WHITE}\"{text}...\"{Colors.RESET}")
            print()

        # Notable Observations
        observations = behavior_profile.get("notable_observations", [])
        if observations:
            print(f"{Colors.BOLD}{Colors.RED}🔍 Key Observations:{Colors.RESET}")
            for obs in observations[:3]:
                print(f"   • {Colors.GRAY}{obs}{Colors.RESET}")
            print()

        # Behavioral Insights
        if behavioral_insights:
            print(f"{Colors.BOLD}{Colors.MAGENTA}💡 Behavioral Insights:{Colors.RESET}")
            pattern = behavioral_insights.get("emotional_pattern", "")
            if pattern:
                print(f"   📊 Pattern: {Colors.CYAN}{pattern}{Colors.RESET}")

            confidence_trend = behavioral_insights.get("confidence_trend", [])
            if confidence_trend:
                avg_confidence = sum(confidence_trend) / len(confidence_trend)
                print(f"   📈 Avg Confidence Trend: {Colors.GREEN}{avg_confidence:.2f}{Colors.RESET}")

        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}❌ Error displaying behavioral analysis: {e}{Colors.RESET}")

def display_emotional_timeline(session_service, app_name: str, user_id: str, session_id: str):
    """Display emotional changes over time."""
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if not session:
            return

        behavior_timeline = session.state.get("behavior_timeline", [])
        if not behavior_timeline:
            print(f"{Colors.GRAY}No emotional timeline data available{Colors.RESET}")
            return

        print(f"\n{Colors.BOLD}{Colors.BG_MAGENTA}{Colors.WHITE} 💭 Emotional Timeline {Colors.RESET}")
        print(f"{Colors.MAGENTA}{'─' * 50}{Colors.RESET}")

        for entry in behavior_timeline[-5:]:  # Show last 5 entries
            timestamp = entry.get("timestamp", "Unknown")
            valence = entry.get("emotional_valence", "neutral")
            confidence = entry.get("confidence_level", 0)

            emoji_map = {
                "positive": "😊",
                "negative": "😔",
                "neutral": "😐"
            }
            emoji = emoji_map.get(valence.lower(), "😐")

            print(f"{Colors.WHITE}{timestamp}{Colors.RESET} | {emoji} {Colors.GREEN}{valence.title()}{Colors.RESET} | 🎯 {confidence:.2f}")

        print(f"{Colors.MAGENTA}{'─' * 50}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error displaying emotional timeline: {e}{Colors.RESET}")

def clear_screen():
    print("\033[2J\033[H", end="")

def show_loading_spinner(message: str = "Processing..."):
    import sys
    import time

    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0

    while True:
        sys.stdout.write(f"\r{Colors.CYAN}{spinner[i]}{Colors.RESET} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(spinner)

        if not hasattr(show_loading_spinner, 'running'):
            break

    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

def start_loading_spinner(message: str = "Processing..."):
    import threading
    show_loading_spinner.running = True
    spinner_thread = threading.Thread(target=show_loading_spinner, args=(message,))
    spinner_thread.daemon = True
    spinner_thread.start()
    return spinner_thread

def stop_loading_spinner():
    show_loading_spinner.running = False
