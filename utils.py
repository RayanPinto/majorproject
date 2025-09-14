#!/usr/bin/env python3
"""
Utility functions for the Stateful Agent System
Enhanced with beautiful colored UI and table displays
Now includes optional speech output functionality
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import shutil

# Import speech functionality (using ADK Runner approach)
try:
    import pygame
    SPEECH_AVAILABLE = True
    print("✅ Speech functionality loaded successfully (ADK Runner)")
    
    # Simple speech state management
    _speech_enabled = True
    
    def speak_text(text: str, async_speech: bool = True) -> None:
        # This is now handled by ADK Runner in call_agent_async
        pass
    
    def is_speech_enabled() -> bool:
        return _speech_enabled
    
    def get_speech_status() -> str:
        return "🔊 Speech enabled" if _speech_enabled else "🔇 Speech disabled"
    
    def toggle_speech() -> bool:
        global _speech_enabled
        _speech_enabled = not _speech_enabled
        return _speech_enabled
        
except ImportError as e:
    SPEECH_AVAILABLE = False
    print(f"❌ Speech import failed: {e}")
    print(f"💡 Install dependencies: pip install pygame")
    # Fallback functions if speech not available
    def speak_text(text: str, async_speech: bool = True) -> None:
        pass  # No-op if speech not available
    def is_speech_enabled() -> bool:
        return False
    def get_speech_status() -> str:
        return "Speech not available"
    def toggle_speech() -> bool:
        return False
except Exception as e:
    SPEECH_AVAILABLE = False
    print(f"❌ Speech initialization error: {e}")
    # Fallback functions if speech not available
    def speak_text(text: str, async_speech: bool = True) -> None:
        pass  # No-op if speech not available
    def is_speech_enabled() -> bool:
        return False
    def get_speech_status() -> str:
        return "Speech not available"
    def toggle_speech() -> bool:
        return False

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
    """Display agent response in a beautiful format with optional speech output"""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {agent_name} Response {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}{response_text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    
    # Add real speech output if available and enabled
    if SPEECH_AVAILABLE and is_speech_enabled():
        print(f"{Colors.GRAY}🔊 Generating speech audio...{Colors.RESET}")
        speak_text(response_text, async_speech=True)
    elif SPEECH_AVAILABLE:
        print(f"{Colors.GRAY}🔇 Speech disabled{Colors.RESET}")
    else:
        print(f"{Colors.GRAY}❌ Speech not available{Colors.RESET}")

def display_error(error_message: str, error_type: str = "Error"):
    """Display error messages in a beautiful format"""
    print(f"\n{Colors.BOLD}{Colors.BG_RED}{Colors.WHITE} {error_type} {Colors.RESET}")
    print(f"{Colors.RED}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.YELLOW}{error_message}{Colors.RESET}")
    print(f"{Colors.RED}{'=' * 60}{Colors.RESET}")

def display_success(message: str, title: str = "Success"):
    """Display success messages in a beautiful format with optional speech output"""
    print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.WHITE} {title} {Colors.RESET}")
    print(f"{Colors.GREEN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}{message}{Colors.RESET}")
    print(f"{Colors.GREEN}{'=' * 60}{Colors.RESET}")
    
    # Add real speech output for important success messages
    if SPEECH_AVAILABLE and is_speech_enabled():
        speak_text(f"{title}: {message}", async_speech=True)

def display_welcome():
    """Display welcome message with beautiful formatting and speech status"""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} Behavioral Analysis Assistant {Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.WHITE}Welcome! You can:{Colors.RESET}")
    print(f"{Colors.YELLOW}• Process behavioral data{Colors.RESET}")
    print(f"{Colors.YELLOW}• Analyze confidence, stress, and engagement{Colors.RESET}")
    print(f"{Colors.YELLOW}• Request behavioral insights{Colors.RESET}")
    print(f"{Colors.YELLOW}• View real-time dashboards{Colors.RESET}")
    
    # Show real speech status
    if SPEECH_AVAILABLE:
        speech_status = get_speech_status()
        print(f"{Colors.GRAY}Speech: {speech_status}{Colors.RESET}")
        print(f"{Colors.GRAY}Commands: 'toggle speech', 'speech status'{Colors.RESET}")
    
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.GRAY}Type 'exit' or 'quit' to end the conversation{Colors.RESET}\n")
    
    # Welcome speech (real audio)
    if SPEECH_AVAILABLE and is_speech_enabled():
        speak_text("Welcome to the Behavioral Analysis Assistant. Real speech is now available.", async_speech=True)

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
    """Call the agent asynchronously with speech support using ADK Runner"""
    try:
        from google.genai import types
        from google.adk.agents import LiveRequestQueue
        from google.adk.agents.run_config import RunConfig
        
        display_query_info(query)
        
        # Display state before processing
        display_state(runner.session_service, runner.app_name, user_id, session_id, "State Before Processing")
        
        print(f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}")
        final_response_text = None
        final_audio_data = None

        try:
            # Check if speech is enabled
            speech_enabled = SPEECH_AVAILABLE and is_speech_enabled()
            
            if speech_enabled:
                print(f"{Colors.CYAN}🎤 Speech enabled - generating text first, then converting to speech{Colors.RESET}")
                
                # Step 1: Get behavioral analysis text first
                session = runner.session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
                if session:
                    from manager.sub_agents.conversational_agent import handle_conversational_query
                    behavioral_text = handle_conversational_query(query, session.state)
                    print(f"{Colors.GREEN}✅ Generated behavioral analysis text: {len(behavioral_text)} chars{Colors.RESET}")
                    final_response_text = behavioral_text
                else:
                    behavioral_text = "No behavioral data available for analysis."
                    final_response_text = behavioral_text
                
                # Step 2: Use Windows built-in text-to-speech instead
                try:
                    print(f"{Colors.CYAN}🔊 Using Windows text-to-speech...{Colors.RESET}")
                    
                    # Use Windows SAPI for speech synthesis
                    import subprocess
                    
                    # Clean the text for natural human-like speech
                    clean_text = behavioral_text
                    
                    # Remove the "Intelligent Behavioral Analysis" prefix
                    clean_text = clean_text.replace('🤖 **Intelligent Behavioral Analysis**: ', '')
                    clean_text = clean_text.replace('**Intelligent Behavioral Analysis**: ', '')
                    clean_text = clean_text.replace('Intelligent Behavioral Analysis: ', '')
                    
                    # Remove markdown formatting
                    clean_text = clean_text.replace('**', '')  # Remove bold
                    clean_text = clean_text.replace('*', '')   # Remove italic
                    clean_text = clean_text.replace('🤖', '')  # Remove emoji
                    clean_text = clean_text.replace('#', '')   # Remove hash
                    clean_text = clean_text.replace('`', '')   # Remove code blocks
                    
                    # Replace punctuation that sounds awkward when spoken
                    clean_text = clean_text.replace(':', ',')  # Replace colons with commas (more natural)
                    clean_text = clean_text.replace(';', ',')  # Replace semicolons with commas
                    clean_text = clean_text.replace('  ', ' ')  # Remove double spaces
                    
                    # Remove bullet points and list formatting
                    clean_text = clean_text.replace('•', '')
                    clean_text = clean_text.replace('- ', '')
                    clean_text = clean_text.replace('   ', ' ')  # Clean up extra spaces
                    
                    # Remove all complex timestamps and dates completely
                    import re
                    # Remove full ISO timestamps completely
                    clean_text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*[+-]?\d{0,2}:?\d{0,2}', '', clean_text)
                    clean_text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?', '', clean_text)
                    clean_text = re.sub(r'2025-09-\d{2}T\d{2}:\d{2}:\d{2}.*?Z?', '', clean_text)
                    # Remove session IDs that sound robotic
                    clean_text = re.sub(r'INT\d{4}-\d{2}-\d{2}-\d+', 'the session', clean_text)
                    clean_text = re.sub(r'CAND\d+', 'the candidate', clean_text)
                    
                    # Replace technical decimal numbers with more natural speech
                    clean_text = clean_text.replace('0.44', 'zero point four four')
                    clean_text = clean_text.replace('0.63', 'zero point six three')
                    clean_text = clean_text.replace('0.11', 'zero point one one')
                    clean_text = clean_text.replace('0.78', 'zero point seven eight')
                    clean_text = clean_text.replace('0.38', 'zero point three eight')
                    clean_text = clean_text.replace('0.61', 'zero point six one')
                    
                    # Replace other decimal patterns
                    clean_text = re.sub(r'0\.(\d{2})', lambda m: f'zero point {m.group(1)[0]} {m.group(1)[1]}', clean_text)
                    
                    # Make it sound more conversational
                    clean_text = clean_text.replace('The candidate', 'This candidate')
                    clean_text = clean_text.replace('In summary,', 'Overall,')
                    clean_text = clean_text.replace('Additionally,', 'Also,')
                    clean_text = clean_text.replace('Furthermore,', 'Plus,')
                    
                    # Clean up multiple periods and spaces
                    clean_text = re.sub(r'\.{2,}', '.', clean_text)  # Multiple periods to single
                    clean_text = re.sub(r'\s+', ' ', clean_text)     # Multiple spaces to single
                    clean_text = clean_text.strip()                  # Remove leading/trailing spaces
                    
                    # Don't limit length - let it speak the full analysis
                    # if len(clean_text) > 500:
                    #     clean_text = clean_text[:500] + "..."
                    
                    # Use PowerShell with Windows Speech API - more human-like settings
                    ps_command = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

# Try to use a more natural voice if available
$voices = $synth.GetInstalledVoices()
foreach ($voice in $voices) {{
    if ($voice.VoiceInfo.Name -like "*Zira*" -or $voice.VoiceInfo.Name -like "*Eva*" -or $voice.VoiceInfo.Name -like "*Hazel*") {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
        break
    }}
}}

# Human-like speech settings
$synth.Rate = 1         # Slightly faster, more natural pace
$synth.Volume = 90      # Clear volume
$synth.Speak("{clean_text.replace('"', "'").replace('`', "'")}")
'''
                    
                    print(f"{Colors.CYAN}🎤 Speaking behavioral analysis...{Colors.RESET}")
                    
                    # Run PowerShell speech synthesis with much longer timeout for full speech
                    result = subprocess.run(['powershell', '-Command', ps_command], 
                                          capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        print(f"{Colors.GREEN}✅ Speech synthesis completed successfully{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️ Speech synthesis error: {result.stderr}{Colors.RESET}")
                        
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Windows speech synthesis failed: {e}{Colors.RESET}")
                    print(f"{Colors.GRAY}Continuing with text-only response{Colors.RESET}")
                        
            else:
                # No speech - use direct behavioral analysis
                session = runner.session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
                if session:
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
            
            # Play audio if available
            if final_audio_data and speech_enabled:
                try:
                    print(f"{Colors.CYAN}🔊 Playing audio response...{Colors.RESET}")
                    _play_adk_audio(final_audio_data)
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Audio playback error: {e}{Colors.RESET}")
        else:
            display_agent_response("Command processed successfully.", "System Response")

        # Process state updates
        process_state_updates(runner.session_service, runner.app_name, user_id, session_id, query, final_response_text)
        
        # Display state after processing
        display_state(runner.session_service, runner.app_name, user_id, session_id, "State After Processing")

        # Render dashboard
        render_two_column_dashboard(runner.session_service, runner.app_name, user_id, session_id)
        
    except Exception as e:
        display_error(f"Error during agent run: {e}", "Agent Error")

def _play_adk_audio(audio_data: bytes):
    """Play audio data from ADK - detect format first"""
    import tempfile
    import os
    import pygame
    import time
    
    print(f"{Colors.CYAN}🔍 Audio data received: {len(audio_data)} bytes{Colors.RESET}")
    
    # Check the first few bytes to detect format
    if len(audio_data) >= 4:
        header = audio_data[:4]
        print(f"{Colors.CYAN}🔍 Audio header: {header.hex()} ({header}){Colors.RESET}")
        
        # Check for common audio formats
        if header.startswith(b'RIFF'):
            print(f"{Colors.GREEN}✅ Detected WAV format{Colors.RESET}")
            file_ext = '.wav'
        elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
            print(f"{Colors.GREEN}✅ Detected MP3 format{Colors.RESET}")
            file_ext = '.mp3'
        elif header.startswith(b'OggS'):
            print(f"{Colors.GREEN}✅ Detected OGG format{Colors.RESET}")
            file_ext = '.ogg'
        else:
            print(f"{Colors.YELLOW}⚠️ Unknown format, trying as raw PCM{Colors.RESET}")
            file_ext = '.raw'
    else:
        print(f"{Colors.RED}❌ Audio data too small: {len(audio_data)} bytes{Colors.RESET}")
        return
    
    try:
        # Method 1: If it's already a complete audio file, save it directly
        if file_ext in ['.wav', '.mp3', '.ogg']:
            temp_fd, temp_file_path = tempfile.mkstemp(suffix=file_ext)
            os.close(temp_fd)
            
            # Write the raw audio data directly
            with open(temp_file_path, 'wb') as f:
                f.write(audio_data)
            
            print(f"{Colors.CYAN}🎵 Attempting direct playback of {file_ext} file...{Colors.RESET}")
            
            # Try pygame
            try:
                pygame.mixer.quit()
                pygame.mixer.init()
                pygame.mixer.music.load(temp_file_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                print(f"{Colors.GREEN}✅ Direct playback completed{Colors.RESET}")
                
                # Save debug copy
                debug_file = f"debug_audio_{int(time.time())}{file_ext}"
                import shutil
                shutil.copy2(temp_file_path, debug_file)
                print(f"{Colors.CYAN}💾 Audio saved as {debug_file}{Colors.RESET}")
                
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️ Pygame failed: {e}{Colors.RESET}")
                
                # Try system player
                try:
                    import subprocess
                    if file_ext == '.wav':
                        subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{temp_file_path}").PlaySync()'], 
                                     check=True, capture_output=True)
                    else:
                        # Try default system player
                        subprocess.run(['start', temp_file_path], shell=True, check=True)
                    
                    print(f"{Colors.GREEN}✅ System playback completed{Colors.RESET}")
                    
                except Exception as e2:
                    print(f"{Colors.YELLOW}⚠️ System playback failed: {e2}{Colors.RESET}")
            
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        else:
            # Method 2: Treat as raw PCM and convert to WAV
            print(f"{Colors.CYAN}🎵 Converting raw PCM to WAV...{Colors.RESET}")
            
            temp_fd, temp_file_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            # Try multiple PCM configurations
            configs = [
                (1, 2, 24000),  # Mono, 16-bit, 24kHz
                (1, 2, 22050),  # Mono, 16-bit, 22kHz
                (1, 2, 16000),  # Mono, 16-bit, 16kHz
                (2, 2, 24000),  # Stereo, 16-bit, 24kHz
                (1, 1, 24000),  # Mono, 8-bit, 24kHz
            ]
            
            for i, (channels, sampwidth, framerate) in enumerate(configs):
                try:
                    config_file = f"debug_audio_config_{i}_{int(time.time())}.wav"
                    import wave
                    with wave.open(config_file, 'wb') as wav_file:
                        wav_file.setnchannels(channels)
                        wav_file.setsampwidth(sampwidth)
                        wav_file.setframerate(framerate)
                        wav_file.writeframes(audio_data)
                    
                    print(f"{Colors.CYAN}💾 Config {i}: {channels}ch, {sampwidth*8}bit, {framerate}Hz → {config_file}{Colors.RESET}")
                    
                    if i == 0:  # Use first config for playback
                        temp_file_path = config_file
                        
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Config {i} failed: {e}{Colors.RESET}")
            
            # Also save first 100 bytes for inspection
            print(f"{Colors.CYAN}🔍 First 100 bytes: {audio_data[:100].hex()}{Colors.RESET}")
            
            # Save debug copy
            debug_file = f"debug_audio_pcm_{int(time.time())}.wav"
            import shutil
            shutil.copy2(temp_file_path, debug_file)
            print(f"{Colors.CYAN}💾 PCM conversion saved as {debug_file}{Colors.RESET}")
            
            # Try different pygame approaches
            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=24000, size=-16, channels=1)
                pygame.mixer.music.load(temp_file_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                print(f"{Colors.GREEN}✅ PCM playback completed{Colors.RESET}")
                
            except Exception as pygame_error:
                print(f"{Colors.YELLOW}⚠️ Pygame failed: {pygame_error}{Colors.RESET}")
                
                # Try Windows system player as backup
                try:
                    import subprocess
                    result = subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{temp_file_path}").PlaySync()'], 
                                         capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"{Colors.GREEN}✅ Windows system player succeeded{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️ Windows player error: {result.stderr}{Colors.RESET}")
                        
                except Exception as sys_error:
                    print(f"{Colors.YELLOW}⚠️ System player failed: {sys_error}{Colors.RESET}")
            
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        print(f"{Colors.RED}❌ Audio playback failed: {e}{Colors.RESET}")
        
        # Last resort - save raw data for inspection
        try:
            debug_file = f"debug_audio_raw_{int(time.time())}.bin"
            with open(debug_file, 'wb') as f:
                f.write(audio_data)
            print(f"{Colors.CYAN}💾 Raw audio data saved as {debug_file}{Colors.RESET}")
        except:
            pass

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
