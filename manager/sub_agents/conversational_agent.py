from google.adk.agents import Agent
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Enhanced RAG function for behavioral analysis using direct Gemini API
def rag_retrieve(query, session_state):
    """Retrieve behavioral context for analysis using direct Gemini API."""
    current_behavior = session_state.get("current_behavior", {})
    behavioral_data = session_state.get("behavioral_data", [])
    behavioral_insights = session_state.get("behavioral_insights", {})
    candidate_info = session_state.get("candidate_info", {})

    # Build comprehensive behavioral context
    behavioral_context = {
        "current_behavior": current_behavior,
        "behavioral_history": behavioral_data[-5:],  # Last 5 entries
        "insights": behavioral_insights,
        "candidate_info": candidate_info
    }

    # Build concise window summaries to help temporal reasoning
    windows_summary = []
    try:
        ws = behavioral_insights.get("windows_summary", [])
        for w in ws[-3:]:
            windows_summary.append({
                "id": w.get("id"),
                "start": w.get("start"),
                "end": w.get("end"),
                "duration_sec": w.get("duration_sec"),
                "avg_confidence": w.get("avg_confidence"),
                "avg_engagement": w.get("avg_engagement"),
                "avg_stress": w.get("avg_stress"),
                "emotion_start": w.get("emotion_start"),
                "emotion_end": w.get("emotion_end"),
            })
    except Exception:
        windows_summary = []

    # Create intelligent behavioral analysis prompt
    rag_prompt = f"""You are an expert behavioral analyst. Analyze this behavioral data and answer the user's query: "{query}"

Current Behavior (latest): {json.dumps(current_behavior, indent=2)}

Recent History (last 5): {json.dumps(behavioral_data[-5:], indent=2)}

Computed Insights: {json.dumps(behavioral_insights, indent=2)}

Window Summaries (recent): {json.dumps(windows_summary, indent=2)}

Instructions:
1) Understand the user's intent (no keyword matching; infer meaning)
2) Use timestamps and window summaries to reason about answer periods
3) Summarize how confidence, stress, and engagement changed within the latest window
4) Compare latest window vs previous window if helpful
5) Be concise, natural, and specific; avoid dumping raw JSON
6) If data is insufficient, say what is missing and proceed with best effort
"""

    try:
        # Use direct Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(rag_prompt)
        return response.text
    except Exception as e:
        # Intelligent fallback - analyze the data ourselves
        return generate_intelligent_fallback_analysis(query, behavioral_context)

def generate_intelligent_fallback_analysis(query, behavioral_context):
    """Generate intelligent analysis when Gemini API fails."""
    current_behavior = behavioral_context.get("current_behavior", {})
    behavioral_insights = behavioral_context.get("insights", {})
    
    # Extract key behavioral metrics
    behavior_profile = current_behavior.get("behavior_profile", {})
    confidence = behavior_profile.get("confidence_level", 0)
    engagement = behavior_profile.get("engagement_level", 0)
    stress = behavior_profile.get("stress_level", 0)
    valence = behavior_profile.get("emotional_valence", "neutral")
    
    # Produce context-aware analysis without keyword reliance
    # Summarize latest window if available
    insights = behavioral_context.get("insights", {})
    windows = insights.get("windows_summary", [])
    latest_win = windows[-1] if windows else None
    prev_win = windows[-2] if len(windows) >= 2 else None

    parts = []
    if latest_win:
        parts.append("🪟 Latest answer window:")
        parts.append(f"- Duration: {latest_win.get('duration_sec', 0)}s")
        parts.append(f"- Avg Confidence {latest_win.get('avg_confidence', 0):.2f}, Engagement {latest_win.get('avg_engagement', 0):.2f}, Stress {latest_win.get('avg_stress', 0):.2f}")
        parts.append(f"- Emotion: {latest_win.get('emotion_start', 'neutral')} → {latest_win.get('emotion_end', 'neutral')}")
    else:
        parts.append("No answer windows detected yet; summarizing current behavior.")

    if prev_win and latest_win:
        dc = (latest_win.get('avg_confidence', 0) - prev_win.get('avg_confidence', 0))
        ds = (latest_win.get('avg_stress', 0) - prev_win.get('avg_stress', 0))
        de = (latest_win.get('avg_engagement', 0) - prev_win.get('avg_engagement', 0))
        parts.append("📊 Change vs previous window:")
        parts.append(f"- ΔConfidence {dc:+.2f}, ΔEngagement {de:+.2f}, ΔStress {ds:+.2f}")

    # Always include current snapshot
    parts.append("📈 Current snapshot:")
    parts.append(f"- Confidence {confidence:.2f}, Engagement {engagement:.2f}, Stress {stress:.2f}, Emotion {valence}")

    return "\n".join(parts)

def conversational_response(user_input, session_state):
    """Intelligent conversational response without static keywords."""
    state_info = extract_state_info(session_state)
    
    # Check if we have behavioral data
    if not state_info["has_data"]:
        return "🤖 No behavioral data available yet. Please start the JSON producer to receive real-time behavioral data."
    
    # Use intelligent RAG retrieval with Gemini API
    try:
        intelligent_response = rag_retrieve(user_input, session_state)
        return f"🤖 **Intelligent Behavioral Analysis**: {intelligent_response}"
    except Exception as e:
        # Fallback to intelligent analysis
        return generate_intelligent_fallback_analysis(user_input, {
            "current_behavior": state_info["current_behavior"],
            "insights": state_info["behavioral_insights"]
        })

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

def _generate_behavior_summary_from_state(session_state: Dict[str, Any], max_items: int = 6) -> List[str]:
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

def generate_enhanced_behavioral_analysis(state_info):
    """Generate enhanced behavioral analysis with pattern recognition."""
    last_update = state_info["last_update"]
    last_behavior_ingest = state_info.get("last_behavior_ingest")
    current_behavior = state_info["current_behavior"]
    behavioral_data_count = state_info["behavioral_data_count"]

    if not state_info["has_data"]:
        return "🤖 No behavioral data available yet. Please start the JSON producer to receive real-time behavioral data."

    parts: List[str] = []
    parts.append("🤖 **Enhanced Behavioral Analysis with Pattern Recognition**")
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

    behavior_profile = current_behavior.get("behavior_profile", {})
    if behavior_profile:
        confidence = behavior_profile.get("confidence_level", 0)
        engagement = behavior_profile.get("engagement_level", 0)
        stress = behavior_profile.get("stress_level", 0)
        valence = behavior_profile.get("emotional_valence", "unknown")

        parts.append("📈 **Current Behavioral Metrics**:")
        parts.append(f"   🎯 **Confidence**: {confidence:.2f}")
        parts.append(f"   🔥 **Engagement**: {engagement:.2f}")
        parts.append(f"   😰 **Stress**: {stress:.2f}")
        parts.append(f"   💭 **Emotional State**: {valence.title()}")
        parts.append("")

    # Enhanced Behavioral Insights with Pattern Recognition
    behavioral_insights = state_info["behavioral_insights"]
    if behavioral_insights:
        parts.append("💡 **Pattern Recognition Insights**:")
        
        # Pattern Summary
        if "pattern_summary" in behavioral_insights:
            parts.append(f"   📊 **Pattern Summary**: {behavioral_insights['pattern_summary']}")
            parts.append("")
        
        # Confidence Analysis
        if "confidence_pattern" in behavioral_insights:
            pattern = behavioral_insights["confidence_pattern"]
            avg_confidence = behavioral_insights.get("avg_confidence", 0)
            parts.append(f"   🎯 **Confidence Analysis**:")
            parts.append(f"      • Trend: {pattern.title()}")
            parts.append(f"      • Average: {avg_confidence:.2f}")
            
            if "confidence_spikes" in behavioral_insights and behavioral_insights["confidence_spikes"]:
                spikes = behavioral_insights["confidence_spikes"]
                parts.append(f"      • Notable fluctuations: {len(spikes)} detected")
            parts.append("")
        
        # Stress Analysis
        if "stress_pattern" in behavioral_insights:
            pattern = behavioral_insights["stress_pattern"]
            avg_stress = behavioral_insights.get("avg_stress", 0)
            parts.append(f"   😰 **Stress Analysis**:")
            parts.append(f"      • Trend: {pattern.title()}")
            parts.append(f"      • Average: {avg_stress:.2f}")
            
            if "stress_spikes" in behavioral_insights and behavioral_insights["stress_spikes"]:
                spikes = behavioral_insights["stress_spikes"]
                parts.append(f"      • Stress spikes: {len(spikes)} detected")
            parts.append("")
        
        # Engagement Analysis
        if "engagement_pattern" in behavioral_insights:
            pattern = behavioral_insights["engagement_pattern"]
            avg_engagement = behavioral_insights.get("avg_engagement", 0)
            parts.append(f"   🔥 **Engagement Analysis**:")
            parts.append(f"      • Trend: {pattern.title()}")
            parts.append(f"      • Average: {avg_engagement:.2f}")
            parts.append("")
        
        # Emotional Transitions
        if "emotional_transitions" in behavioral_insights and behavioral_insights["emotional_transitions"]:
            transitions = behavioral_insights["emotional_transitions"]
            parts.append(f"   💭 **Emotional Transitions**:")
            for transition in transitions[-2:]:  # Show last 2 transitions
                parts.append(f"      • {transition['from']} → {transition['to']}")
            parts.append("")
        
        # Behavioral Timeline
        if "behavioral_timeline" in behavioral_insights:
            timeline = behavioral_insights["behavioral_timeline"]
            if timeline:
                parts.append(f"   📅 **Recent Behavioral Timeline**:")
                for entry in timeline[-3:]:  # Show last 3 entries
                    timestamp = entry.get("timestamp", "")[:19]  # Truncate timestamp
                    confidence = entry.get("confidence", 0)
                    engagement = entry.get("engagement", 0)
                    stress = entry.get("stress", 0)
                    valence = entry.get("emotional_valence", "neutral")
                    parts.append(f"      • {timestamp}: Conf({confidence:.2f}) Eng({engagement:.2f}) Stress({stress:.2f}) {valence.title()}")
    else:
        # If no behavioral insights, generate them on-the-fly
        parts.append("💡 **Pattern Recognition Insights**:")
        parts.append("   🔄 **Generating real-time pattern analysis...**")
        parts.append("")
        
        # Generate basic pattern analysis from available data
        behavioral_data = state_info["full_session_state"].get("behavioral_data", [])
        if behavioral_data:
            # Extract confidence values
            confidence_values = []
            for entry in behavioral_data:
                behavior_profile = entry.get("behavior_data", {}).get("behavior_profile", {})
                conf = behavior_profile.get("confidence_level", 0)
                if conf > 0:
                    confidence_values.append(conf)
            
            if confidence_values:
                avg_confidence = sum(confidence_values) / len(confidence_values)
                parts.append(f"   🎯 **Confidence Analysis**:")
                parts.append(f"      • Average: {avg_confidence:.2f}")
                parts.append(f"      • Data points: {len(confidence_values)}")
                
                if len(confidence_values) >= 2:
                    if confidence_values[-1] > confidence_values[0] + 0.1:
                        parts.append(f"      • Trend: Increasing")
                    elif confidence_values[-1] < confidence_values[0] - 0.1:
                        parts.append(f"      • Trend: Decreasing")
                    else:
                        parts.append(f"      • Trend: Stable")
                parts.append("")

    return "\n".join(parts)

# Create the conversational agent
conversational_agent = Agent(
    name="conversational_agent",
    model="gemini-2.0-flash-live-001",  # Use API for enhanced responses
    instruction="""You are an advanced conversational AI assistant for behavioral analysis. Your role is to:

1. **Natural Language Understanding**: Interpret ANY user query about behavioral analysis, regardless of phrasing or keywords. Understand intent, not just specific words.

2. **Intelligent Behavioral Analysis**: 
   - Analyze candidate behavior, emotions, and patterns from multimodal data
   - Provide context-aware insights based on the user's actual question
   - Generate behavioral summaries and pattern recognition
   - Track confidence, stress, engagement, and emotional transitions

3. **Conversational Intelligence**: 
   - Use natural, helpful language
   - Provide context-aware responses
   - Ask clarifying questions when needed
   - Be conversational and engaging

4. **Intent Recognition**: 
   - Understand what the user is actually asking about
   - Provide relevant information based on context
   - Handle variations in how questions are phrased
   - No keyword matching - true understanding

5. **Behavioral Expertise**: 
   - Interpret behavioral metrics meaningfully
   - Identify patterns and trends
   - Provide actionable insights
   - Explain behavioral data in human terms

**Key Capabilities:**
- Natural language understanding without static keywords
- Real-time behavioral pattern recognition
- Confidence, stress, and engagement analysis
- Emotional transition tracking
- Behavioral timeline visualization
- Context-aware responses

**Response Style:**
- Use markdown formatting for readability
- Include emojis for visual appeal
- Provide clear, actionable behavioral insights
- Be conversational and helpful
- Answer the user's actual question, not just match keywords

**Important**: You have access to the current session state and should provide direct, useful behavioral analysis responses. Understand the user's intent naturally, don't rely on keyword matching.""",
    tools=[]  # No tools needed as we handle everything in the response function
)

def handle_conversational_query(user_input, session_state):
    """Handle conversational queries and return appropriate responses"""
    return conversational_response(user_input, session_state)

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
