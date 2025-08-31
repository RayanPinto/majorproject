from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import litellm

# Enhanced RAG function for behavioral analysis
def rag_retrieve(query, session_state):
    # Extract behavioral data from session state
    current_behavior = session_state.get("current_behavior", {})
    behavioral_data = session_state.get("behavioral_data", [])
    behavioral_insights = session_state.get("behavioral_insights", {})

    # Build behavioral context
    behavioral_context = {
        "current_behavior": current_behavior,
        "behavioral_history": behavioral_data[-5:],  # Last 5 entries
        "insights": behavioral_insights
    }

    # Create behavioral analysis prompt
    rag_prompt = f"""Analyze this behavioral data for the query: {query}

Behavioral Context: {json.dumps(behavioral_context, indent=2)}

Provide relevant behavioral insights and patterns that answer the query."""

    try:
        response = litellm.completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": rag_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback to local analysis
        return f"Behavioral analysis based on available data: {json.dumps(behavioral_context)}"

def conversational_response(user_input, session_state):
    user_input_lower = user_input.lower().strip()
    state_info = extract_state_info(session_state)
    
    # Check if we have behavioral data and user is asking for analysis
    if state_info["has_data"] and any(keyword in user_input_lower for keyword in ["analyze", "behavior", "insights", "summary", "patterns"]):
        return generate_summary_response(state_info)
    
    # Handle specific behavioral analysis requests
    if "confidence" in user_input_lower and state_info["has_data"]:
        current_behavior = state_info["current_behavior"]
        behavior_profile = current_behavior.get("behavior_profile", {})
        confidence = behavior_profile.get("confidence_level", 0)
        
        if confidence > 0.7:
            return f"🎯 **Confidence Analysis**: The candidate shows high confidence ({confidence:.2f}). This indicates strong self-assurance and belief in their abilities."
        elif confidence < 0.4:
            return f"😰 **Confidence Analysis**: The candidate shows low confidence ({confidence:.2f}). This suggests nervousness or uncertainty that may need addressing."
        else:
            return f"😐 **Confidence Analysis**: The candidate shows moderate confidence ({confidence:.2f}). This is within normal range for interview situations."
    
    if "stress" in user_input_lower and state_info["has_data"]:
        current_behavior = state_info["current_behavior"]
        behavior_profile = current_behavior.get("behavior_profile", {})
        stress = behavior_profile.get("stress_level", 0)
        
        if stress > 0.6:
            return f"⚠️ **Stress Analysis**: High stress levels detected ({stress:.2f}). The candidate may be experiencing anxiety or pressure."
        elif stress < 0.3:
            return f"😌 **Stress Analysis**: Low stress levels ({stress:.2f}). The candidate appears calm and composed."
        else:
            return f"😐 **Stress Analysis**: Moderate stress levels ({stress:.2f}). This is typical for interview situations."
    
    if "engagement" in user_input_lower and state_info["has_data"]:
        current_behavior = state_info["current_behavior"]
        behavior_profile = current_behavior.get("behavior_profile", {})
        engagement = behavior_profile.get("engagement_level", 0)
        
        if engagement > 0.8:
            return f"🔥 **Engagement Analysis**: High engagement detected ({engagement:.2f}). The candidate is very interested and involved."
        elif engagement < 0.5:
            return f"📉 **Engagement Analysis**: Low engagement ({engagement:.2f}). The candidate may need more stimulating questions."
        else:
            return f"😐 **Engagement Analysis**: Moderate engagement ({engagement:.2f}). The candidate shows reasonable interest."
    
    # If no behavioral data, provide helpful message
    if not state_info["has_data"]:
        return "🤖 No behavioral data available yet. Please use 'simulate json' or 'simulate event' to load some behavioral data first."
    
    # Default response with behavioral context
    retrieved_context = rag_retrieve(user_input, session_state)
    return f"🤖 **Behavioral Analysis**: {retrieved_context}"

# ... (rest unchanged)

def extract_state_info(session_state):
    """Extract behavioral state information from session for analysis."""
    current_behavior = session_state.get("current_behavior", {})
    behavioral_data = session_state.get("behavioral_data", [])
    behavioral_insights = session_state.get("behavioral_insights", {})
    candidate_info = session_state.get("candidate_info", {})
    last_update = session_state.get("last_update", "Never")
    last_behavior_ingest = session_state.get("last_behavior_ingest", None)
    behavior_timeline = session_state.get("behavior_timeline", [])
    alerts = session_state.get("alerts", [])

    # Check if we have behavioral data
    has_behavior_data = (
        bool(current_behavior.get("metadata")) or 
        bool(behavioral_data) or 
        bool(current_behavior.get("behavior_profile")) or
        bool(current_behavior.get("video_features")) or
        bool(current_behavior.get("audio_features"))
    )

    return {
        "current_behavior": current_behavior,
        "behavioral_data_count": len(behavioral_data),
        "behavioral_insights": behavioral_insights,
        "candidate_info": candidate_info,
        "last_update": last_update,
        "last_behavior_ingest": last_behavior_ingest,
        "has_data": has_behavior_data,
        "behavior_timeline_len": len(behavior_timeline),
        "alerts_count": len(alerts),
        "full_session_state": session_state,
    }

def _format_seconds(sec: float) -> str:
    try:
        return f"{float(sec):.2f}s"
    except Exception:
        return str(sec)

def _generate_behavior_summary_from_state(session_state: Dict[str, Any], max_items: int = 5) -> str:
    """Generate concise behavior summary from alerts and active span.

    Produces lines like: "sad from 12.30s to 17.56s (avg 0.82)".
    Includes currently active span if present.
    """
    alerts: List[Dict[str, Any]] = session_state.get("alerts", [])
    aggregates: Dict[str, Any] = session_state.get("aggregates", {})
    lines: List[str] = []

    # Include active span if exists
    active = aggregates.get("active_span")
    if active and isinstance(active, dict) and all(k in active for k in ("label", "t_start", "t_end")):
        lbl = active.get("label")
        t0 = _format_seconds(active.get("t_start"))
        t1 = _format_seconds(active.get("t_end"))
        lines.append(f"Currently {lbl} from {t0} to {t1} (ongoing)")

    # Recent closed spans (reverse chronological)
    closed_spans = [a for a in alerts if a.get("kind") == "emotion_span"]
    closed_spans = sorted(closed_spans, key=lambda x: x.get("t_end", 0.0), reverse=True)
    for a in closed_spans[:max_items]:
        lbl = a.get("label", "unknown")
        t0 = _format_seconds(a.get("t_start", 0.0))
        t1 = _format_seconds(a.get("t_end", 0.0))
        avg = a.get("avg_score")
        if isinstance(avg, (int, float)):
            lines.append(f"{lbl} from {t0} to {t1} (avg {avg:.2f})")
        else:
            lines.append(f"{lbl} from {t0} to {t1}")

    if not lines:
        return "No behavior spans detected yet."
    return "\n".join(lines)

def generate_summary_response(state_info):
    """Generate a behavioral analysis summary of the candidate."""
    last_update = state_info["last_update"]
    last_behavior_ingest = state_info.get("last_behavior_ingest")
    current_behavior = state_info["current_behavior"]
    behavioral_data_count = state_info["behavioral_data_count"]

    if not state_info["has_data"]:
        return "🤖 No behavioral data available yet. Please ingest some behavioral data first using 'simulate json'."

    parts: List[str] = []
    parts.append("🤖 **Behavioral Analysis Summary**")
    parts.append(f"🕒 Last updated: {last_update}")
    if last_behavior_ingest:
        parts.append(f"📊 Last behavioral data: {last_behavior_ingest}")
    parts.append("")

    # Candidate info
    candidate_info = state_info["candidate_info"]
    if candidate_info.get("candidate_id"):
        parts.append(f"👤 **Candidate**: {candidate_info['candidate_id']}")
        if candidate_info.get("session_id"):
            parts.append(f"📋 **Session**: {candidate_info['session_id']}")
        parts.append("")

    # Current behavioral state
    metadata = current_behavior.get("metadata", {})
    if metadata:
        duration = metadata.get("duration_sec", 0)
        parts.append(f"⏱️ **Current Analysis Period**: {duration} seconds")
        parts.append("")

    # Behavioral profile analysis
    behavior_profile = current_behavior.get("behavior_profile", {})
    if behavior_profile:
        confidence = behavior_profile.get("confidence_level", 0)
        engagement = behavior_profile.get("engagement_level", 0)
        stress = behavior_profile.get("stress_level", 0)
        valence = behavior_profile.get("emotional_valence", "unknown")

        parts.append("📈 **Behavioral Metrics**:")
        parts.append(f"   🎯 **Confidence Level**: {confidence:.2f}")
        parts.append(f"   🔥 **Engagement Level**: {engagement:.2f}")
        parts.append(f"   😰 **Stress Level**: {stress:.2f}")
        parts.append(f"   💭 **Emotional State**: {valence.title()}")
        parts.append("")

        # Add behavioral insights
        if confidence > 0.7:
            parts.append("💡 **Insight**: High confidence indicates strong self-assurance")
        elif confidence < 0.4:
            parts.append("💡 **Insight**: Low confidence suggests nervousness or uncertainty")
        
        if stress > 0.6:
            parts.append("⚠️ **Alert**: Elevated stress levels detected")
        
        if engagement < 0.5:
            parts.append("📉 **Note**: Engagement could be improved")

    # Notable observations
    observations = behavior_profile.get("notable_observations", [])
    if observations:
        parts.append("🔍 **Key Observations**:")
        for obs in observations[:3]:  # Show top 3 observations
            parts.append(f"   • {obs}")
        parts.append("")

    # Facial expressions analysis
    video_features = current_behavior.get("video_features", {})
    facial_expressions = video_features.get("facial_expressions", [])
    if facial_expressions:
        parts.append("😊 **Recent Facial Expressions**:")
        for expr in facial_expressions[-3:]:
            time_sec = expr.get("time_sec", 0)
            expression = expr.get("expression", "unknown")
            confidence = expr.get("confidence", 0)
            parts.append(f"   {time_sec:.1f}s: {expression} ({confidence:.2f})")
        parts.append("")

    # Speech analysis
    audio_features = current_behavior.get("audio_features", {})
    speech_segments = audio_features.get("speech_segments", [])
    if speech_segments:
        parts.append("🎤 **Recent Speech**:")
        for segment in speech_segments[-2:]:
            start = segment.get("start_sec", 0)
            text = segment.get("text", "")[:60]
            parts.append(f"   {start:.1f}s: \"{text}...\"")
        parts.append("")

    # Data statistics
    parts.append("📊 **Analysis Statistics**:")
    parts.append(f"   📝 Behavioral data points: {behavioral_data_count}")
    if state_info["alerts_count"] > 0:
        parts.append(f"   🚨 Behavioral alerts: {state_info['alerts_count']}")

    return "\n".join(parts)

def generate_behavioral_state_response(state_info):
    """Generate a detailed behavioral state response"""
    current_behavior = state_info["current_behavior"]
    last_update = state_info["last_update"]
    behavioral_data_count = state_info["behavioral_data_count"]
    
    response_parts = []
    response_parts.append(f"📊 **Current Behavioral State**")
    response_parts.append(f"🕒 **Last Updated**: {last_update}")
    response_parts.append(f"📥 **Total Behavioral Data Points**: {behavioral_data_count}")
    response_parts.append("")
    response_parts.append("**Current Behavioral Profile**:")
    response_parts.append("```json")
    response_parts.append(json.dumps(current_behavior, indent=2))
    response_parts.append("```")
    
    return "\n".join(response_parts)

def extract_update_intent(user_input):
    """Extract update intent from natural language"""
    # Patterns for detecting update requests - more comprehensive
    update_patterns = [
        # "update my _id to test456"
        r"(?:update|change|modify|set)\s+(?:my\s+)?(?:the\s+)?(?:value\s+of\s+)?(\w+)\s+(?:to|as|=)\s+['\"]?([^'\"]+)['\"]?",
        # "set _id to test456"
        r"(?:set|change)\s+(?:my\s+)?(\w+)\s+(?:to|=)\s+['\"]?([^'\"]+)['\"]?",
        # "_id should be test456"
        r"(?:my\s+)?(\w+)\s+(?:should\s+be|is\s+now|equals|=)\s+['\"]?([^'\"]+)['\"]?",
        # "update _id with test456"
        r"update\s+(?:my\s+)?(\w+)\s+with\s+['\"]?([^'\"]+)['\"]?",
        # "change _id to test456"
        r"change\s+(?:my\s+)?(\w+)\s+to\s+['\"]?([^'\"]+)['\"]?",
        # "modify _id to test456"
        r"modify\s+(?:my\s+)?(\w+)\s+to\s+['\"]?([^'\"]+)['\"]?"
    ]
    
    for pattern in update_patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            return {
                "key": match.group(1),
                "value": match.group(2).strip(),
                "intent": "update"
            }
    
    return None

def conversational_response(user_input, session_state):
    """RAG Agentic System - Analyzes context and current state to provide intelligent responses"""
    user_input_lower = user_input.lower().strip()
    state_info = extract_state_info(session_state)
    
    # ===== CONTEXT ANALYSIS =====
    # Analyze current behavioral context for better responses
    has_data = state_info["has_data"]
    behavioral_data_count = state_info["behavioral_data_count"]
    last_update = state_info["last_update"]
    
    # ===== INTENT CLASSIFICATION WITH CONTEXT =====

    # 1. Behavioral Analysis Intents
    behavioral_keywords = [
        "analyze", "behavior", "behavioral", "confidence", "engagement", "stress",
        "emotional", "facial", "expression", "gaze", "posture", "body language",
        "prosody", "voice", "tone", "sentiment", "valence", "mood", "emotion"
    ]

    if any(keyword in user_input_lower for keyword in behavioral_keywords):
        if "confidence" in user_input_lower:
            return "🎯 **Confidence Analysis**: Let me analyze the candidate's confidence patterns from the behavioral data."
        elif "stress" in user_input_lower or "anxiety" in user_input_lower:
            return "😰 **Stress Analysis**: Analyzing stress indicators from facial expressions, voice patterns, and body language."
        elif "engagement" in user_input_lower:
            return "🔥 **Engagement Analysis**: Evaluating candidate engagement through gaze tracking and interaction patterns."
        elif "emotional" in user_input_lower or "emotion" in user_input_lower:
            return "💭 **Emotional Analysis**: Examining emotional valence and mood patterns throughout the interview."
        else:
            return "🤖 **Behavioral Analysis**: I'll provide a comprehensive analysis of the candidate's behavioral patterns."

    # 2. JSON Processing Intent (with context awareness)
    json_keywords = [
        "process", "save", "add", "store", "input", "json", "data", "update with",
        "process this", "save this", "add this", "store this", "input this"
    ]
    
    json_patterns = [
        r'\{.*\}',  # Contains curly braces
        r'\[.*\]',  # Contains square brackets
        r'"[^"]*"\s*:',  # Contains key-value pairs
        r'process.*json',  # Contains "process" and "json"
        r'save.*json',     # Contains "save" and "json"
    ]
    
    has_json_content = any(re.search(pattern, user_input, re.IGNORECASE) for pattern in json_patterns)
    has_json_keywords = any(keyword in user_input_lower for keyword in json_keywords)
    
    if has_json_content or has_json_keywords:
        json_match = re.search(r'(\{.*\})', user_input, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                json.loads(json_str)
                # Context-aware response before execution
                if has_data:
                    return f"EXECUTE_JSON_PROCESSING:{json_str}"
                else:
                    return f"EXECUTE_JSON_PROCESSING:{json_str}"
            except json.JSONDecodeError:
                return "❌ I found what looks like JSON data, but it's not in valid JSON format. Please check the syntax and try again."
        else:
            return "🔄 I understand you want to process JSON data. Please provide the JSON data you'd like to process."
    
    # 2. Summary Intent (context-aware)
    summary_keywords = [
        "summary", "summarize", "summarise", "overview", "current state", 
        "what's in", "what is in", "show me", "tell me about", "give me summary",
        "summarize my", "summarise my", "current status", "state summary"
    ]
    
    if any(keyword in user_input_lower for keyword in summary_keywords):
        if not has_data:
            return "📋 **Current State Summary**: Your state is currently empty. No data has been processed yet."
        # Attach session_state for deeper behavior summary usage
        enriched_info = dict(state_info)
        enriched_info["session_state"] = session_state
        return generate_summary_response(enriched_info)
    
    # 3. Behavioral Data Access Intent (context-aware)
    access_keywords = [
        "access data", "show data", "display data", "full data", 
        "detailed data", "complete data", "all data", "show all",
        "what data", "current data", "data details", "detailed view"
    ]
    
    if any(keyword in user_input_lower for keyword in access_keywords):
        if not has_data:
            return "📊 **Current State Details**: Your state is currently empty. Process some JSON data to get started!"
        return generate_state_access_response(state_info)
    
    # 4. Update Intent (enhanced with context)
    update_intent = extract_update_intent(user_input)
    if update_intent:
        key = update_intent["key"]
        value = update_intent["value"]
        
        # Behavioral analysis doesn't need template updates
        return f"❌ Behavioral analysis system doesn't support manual state updates. Use 'simulate json' to ingest behavioral data."
    
    # 5. Behavioral Data Structure Intent
    structure_keywords = [
        "template", "schema", "structure", "format", "what keys", 
        "available keys", "supported keys", "what fields", "data structure"
    ]
    
    if any(keyword in user_input_lower for keyword in structure_keywords):
        return f"📋 **Behavioral Data Structure**:\nThis system processes behavioral analysis JSON with:\n• **metadata**: candidate info, timestamps\n• **video_features**: facial expressions, gaze tracking\n• **audio_features**: speech segments, voice tone\n• **behavior_profile**: confidence, engagement, stress levels\n\nUse 'simulate json' to see the complete structure."
    
    # 6. Help Intent (context-aware)
    help_keywords = [
        "help", "what can you do", "how to", "commands", "available", 
        "capabilities", "features", "what do you do", "assist me"
    ]
    
    if any(keyword in user_input_lower for keyword in help_keywords):
        help_response = """🤖 **I can help you with behavioral analysis! Here's what I can do:**

📊 **Behavioral Analysis**: Analyze candidate behavior and emotions
   - "analyze behavior"
   - "show insights"
   - "confidence level"
   - "stress analysis"

📈 **Dashboard & Visualization**: View behavioral data
   - "show dashboard"
   - "emotional timeline"
   - "debug state"

📋 **Data Ingestion**: Load behavioral data
   - "simulate json"
   - "simulate event"

💡 **Natural Language**: I understand various ways to ask for behavioral analysis!"""
        
        if has_data:
            help_response += f"\n\n📊 **Current Status**: You have {behavioral_data_count} behavioral data points in your session."
        else:
            help_response += "\n\n📊 **Current Status**: Your session is empty. Try 'simulate json' to load behavioral data!"
            
        return help_response
    
    # 7. Greeting Intent
    greeting_keywords = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(keyword in user_input_lower for keyword in greeting_keywords):
        if has_data:
            return f"👋 Hello! I see you have behavioral data in your session ({behavioral_data_count} data points processed). How can I help you analyze the candidate's behavior today?"
        else:
            return "👋 Hello! I'm here to help you analyze candidate behavior. Your session is currently empty - would you like to ingest some behavioral data to get started?"
    
    # 8. Behavior summary request
    behavior_keywords = ["recent behavior", "behavior", "behaviour", "emotion spans", "timeline summary"]
    if any(keyword in user_input_lower for keyword in behavior_keywords):
        return _generate_behavior_summary_from_state(session_state)

    # 9. Context-aware default response
    if not has_data:
        return "💡 **Getting Started**: Your session is currently empty. Here are some things you can do:\n\n• **Ingest Behavioral Data**: Use 'simulate json' to load behavioral data\n• **Learn More**: 'What can you do?' or 'Help me'\n• **Analyze Behavior**: 'analyze behavior' or 'show insights'"
    
    # 10. Intelligent fallback with context
    return f"🤔 **I understand you're asking about behavioral analysis**, but I'm not sure exactly what you need. Based on your current session ({behavioral_data_count} behavioral data points), here are some helpful options:\n\n• **📋 Behavioral Analysis**: 'analyze behavior' or 'show insights'\n• **📊 Dashboard**: 'show dashboard' or 'emotional timeline'\n• **❓ Help**: 'What can you do?' or 'Help me'\n\n💡 **You can also ask for specific metrics like 'confidence level' or 'stress analysis'."

# Create the conversational agent
conversational_agent = Agent(
    name="conversational_agent",
    model="gemini-2.0-flash",  # Use API for enhanced responses
    instruction="""You are an advanced conversational AI assistant for a state management system. Your role is to:

1. **Understand Natural Language**: Interpret user queries in natural language, including variations, spelling mistakes, and different phrasings.

2. **Provide Direct Answers**: Instead of telling users what commands to use, directly provide the information they're asking for.

3. **Handle State Operations**: 
   - Generate summaries of current state
   - Provide detailed state information
   - Execute state updates directly
   - Explain the system template

4. **Be Conversational**: Use natural, helpful language and provide context-aware responses.

5. **Error Handling**: Gracefully handle unclear requests and provide helpful suggestions.

**Key Capabilities:**
- State summaries and detailed views
- Natural language state updates with direct execution
- Template explanations
- Help and guidance
- Context-aware responses
- JSON processing with natural language

**Response Style:**
- Use markdown formatting for better readability
- Include emojis for visual appeal
- Provide clear, actionable information
- Be conversational and helpful
- Use the EXECUTE_JSON_PROCESSING: and EXECUTE_STATE_UPDATE: markers for direct actions

**Direct Action Markers:**
- For JSON processing: Return "EXECUTE_JSON_PROCESSING: followed by the JSON string"
- For state updates: Return "EXECUTE_STATE_UPDATE:key=value"

Remember: You have access to the current session state and should provide direct, useful responses rather than just explaining what commands exist.""",
    tools=[]  # No tools needed as we handle everything in the response function
)

def handle_conversational_query(user_input, session_state):
    """Handle conversational queries and return appropriate responses"""
    return conversational_response(user_input, session_state)

def extract_action_from_response(response):
    """Extract action command from conversational response"""
    if "Process this JSON:" in response:
        # Extract the command from the response
        import re
        match = re.search(r'`Process this JSON: (.*?)`', response)
        if match:
            return f"Process this JSON: {match.group(1)}"
    elif "Update state:" in response:
        # Extract the command from the response
        import re
        match = re.search(r'`Update state: (.*?)`', response)
        if match:
            return f"Update state: {match.group(1)}"
    return None

# Deterministic handler so the agent summarizes from state without relying on LLM behavior
async def handle_message(context):
    try:
        query = None
        if hasattr(context, "user_content") and context.user_content and getattr(context.user_content, "parts", None):
            first = context.user_content.parts[0]
            if hasattr(first, "text"):
                query = first.text
        if query is None and hasattr(context, "message"):
            query = context.message
        if query is None:
            query = ""

        # Fix: Properly extract session state from context
        session_state = {}
        if hasattr(context, "state") and context.state:
            session_state = context.state
        elif hasattr(context, "session") and context.session and hasattr(context.session, "state"):
            session_state = context.session.state
        elif hasattr(context, "session_state"):
            session_state = context.session_state
        
        # Use our deterministic conversational response (includes behavior summary from alerts/timeline)
        return handle_conversational_query(query, session_state)
    except Exception as e:
        return f"Error handling message: {e}"
