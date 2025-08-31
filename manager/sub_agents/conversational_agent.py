from google.adk.agents import Agent
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import litellm

# Enhanced RAG function for behavioral analysis
def rag_retrieve(query, session_state):
    """Retrieve behavioral context for analysis."""
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
    keywords_to_check = ["analyze", "behavior", "insights", "summary", "patterns"]
    
    if state_info["has_data"] and any(keyword in user_input_lower for keyword in keywords_to_check):
        return generate_enhanced_behavioral_analysis(state_info)
    
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
        return "🤖 No behavioral data available yet. Please ingest some behavioral data first using 'simulate json'."

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
    model="gemini-2.0-flash",  # Use API for enhanced responses
    instruction="""You are an advanced conversational AI assistant for behavioral analysis. Your role is to:

1. **Understand Natural Language**: Interpret user queries about behavioral analysis, including variations and different phrasings.

2. **Provide Behavioral Insights**: Analyze candidate behavior, emotions, and patterns from multimodal data.

3. **Handle Behavioral Analysis**: 
   - Generate behavioral summaries
   - Provide pattern recognition insights
   - Analyze confidence, stress, and engagement levels
   - Track emotional transitions

4. **Be Conversational**: Use natural, helpful language and provide context-aware responses.

5. **Error Handling**: Gracefully handle unclear requests and provide helpful suggestions.

**Key Capabilities:**
- Behavioral pattern recognition
- Real-time behavioral analysis
- Confidence, stress, and engagement tracking
- Emotional transition analysis
- Behavioral timeline visualization

**Response Style:**
- Use markdown formatting for better readability
- Include emojis for visual appeal
- Provide clear, actionable behavioral insights
- Be conversational and helpful

Remember: You have access to the current session state and should provide direct, useful behavioral analysis responses.""",
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
