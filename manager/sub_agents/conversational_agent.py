from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import litellm

# Add RAG function
def rag_retrieve(query, session_state):
    # Simple RAG: Retrieve from session state (internal knowledge base)
    current_state = session_state.get("current_state", {})
    json_inputs = session_state.get("json_inputs", [])
    
    # Augment with external API (mock example; replace with real API)
    # Using LiteLLM for LLM API call to enhance retrieval
    rag_prompt = f"Retrieve relevant info for: {query}. State: {json.dumps(current_state)}"
    response = litellm.completion(
        model="gemini/gemini-2.0-flash",  # Or any LLM API
        messages=[{"role": "user", "content": rag_prompt}]
    )
    retrieved = response.choices[0].message.content  # Augmented context
    return retrieved

def conversational_response(user_input, session_state):
    user_input_lower = user_input.lower().strip()
    state_info = extract_state_info(session_state)
    
    # RAG-augmented LLM call for better intent handling
    retrieved_context = rag_retrieve(user_input, session_state)
    llm_prompt = f"Context: {retrieved_context}\nQuery: {user_input}\nRespond naturally and handle intent."
    llm_response = litellm.completion(  # Use LLM API via LiteLLM
        model="gemini/gemini-2.0-flash",
        messages=[{"role": "user", "content": llm_prompt}]
    ).choices[0].message.content
    
    # Process LLM response for actions (e.g., if it suggests an update)
    if "update" in llm_response.lower():
        # Extract and execute (improved from regex)
        update_intent = extract_update_intent(llm_response)
        if update_intent:
            return f"EXECUTE_STATE_UPDATE:{update_intent['key']}={update_intent['value']}"
    
    # Handle simple intents directly with RAG enhancement
    if "show my state" in user_input_lower or "access state" in user_input_lower:
        return generate_state_access_response(state_info) + f"\n(Enhanced with: {retrieved_context})"
    
    # ... (other intents unchanged, but add LLM response as fallback)
    return llm_response  # Use LLM-generated response for better handling

# ... (rest unchanged)

def extract_state_info(session_state):
    """Extract current state information from session, including real-time fields."""
    current_state = session_state.get("current_state", {})
    json_inputs = session_state.get("json_inputs", [])
    last_update = session_state.get("last_update", "Never")
    last_ingest_at = session_state.get("last_ingest_at", None)
    timeline = session_state.get("timeline", [])
    alerts = session_state.get("alerts", [])
    aggregates = session_state.get("aggregates", {})
    
    return {
        "current_state": current_state,
        "json_inputs_count": len(json_inputs),
        "last_update": last_update,
        "last_ingest_at": last_ingest_at,
        "has_data": any(value for value in current_state.values()) or bool(timeline),
        "timeline_len": len(timeline),
        "alerts_count": len(alerts),
        "aggregates": aggregates,
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
    """Generate a natural language summary of the current state and behavior timeline."""
    last_update = state_info["last_update"]
    last_ingest_at = state_info.get("last_ingest_at")
    
    if not state_info["has_data"]:
        return "Your state is currently empty. No data has been processed yet."
    
    parts: List[str] = []
    header = f"📋 **Current State Summary** (Last updated: {last_update})"
    if last_ingest_at:
        header += f" | Last ingest: {last_ingest_at}"
    parts.append(header)
    parts.append("")
    
    # Behavior timeline summary
    behavior = _generate_behavior_summary_from_state(state_info.get("session_state", {})) if "session_state" in state_info else ""
    if not behavior:
        # If not provided, pass the full session state to generator
        behavior = _generate_behavior_summary_from_state(state_info.get("full_session_state", {})) if "full_session_state" in state_info else ""
    # Fallback: try to use current global session_state structure passed to this function
    if not behavior:
        # We don't have the full session here; advise minimal line
        behavior = "Behavior spans are tracked; ask for 'summarize recent behavior' to view."
    parts.append("**Recent Behavior**:")
    parts.append(behavior)
    
    return "\n".join(parts)

def generate_state_access_response(state_info):
    """Generate a detailed state access response"""
    current_state = state_info["current_state"]
    last_update = state_info["last_update"]
    json_inputs_count = state_info["json_inputs_count"]
    
    response_parts = []
    response_parts.append(f"📊 **Current State Details**")
    response_parts.append(f"🕒 **Last Updated**: {last_update}")
    response_parts.append(f"📥 **Total JSON Inputs Processed**: {json_inputs_count}")
    response_parts.append("")
    response_parts.append("**Current Values**:")
    response_parts.append("```json")
    response_parts.append(json.dumps(current_state, indent=2))
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
    # Analyze current state context for better responses
    current_state = state_info["current_state"]
    has_data = state_info["has_data"]
    json_inputs_count = state_info["json_inputs_count"]
    last_update = state_info["last_update"]
    
    # ===== INTENT CLASSIFICATION WITH CONTEXT =====
    
    # 1. JSON Processing Intent (with context awareness)
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
    
    # 3. State Access Intent (context-aware)
    access_keywords = [
        "access state", "show state", "display state", "full state", 
        "detailed state", "complete state", "all data", "show all",
        "what data", "current data", "state details", "detailed view"
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
        
        template_keys = ["_id", "user_id", "jwt"]
        if key in template_keys:
            # Context-aware update response
            current_value = current_state.get(key, "[Empty]")
            return f"EXECUTE_STATE_UPDATE:{key}={value}"
        else:
            return f"❌ I can't update '{key}' as it's not part of the state template. Available keys are: {', '.join(template_keys)}"
    
    # 5. Template Intent
    template_keywords = [
        "template", "schema", "structure", "format", "what keys", 
        "available keys", "supported keys", "what fields", "data structure"
    ]
    
    if any(keyword in user_input_lower for keyword in template_keywords):
        template = {
            "_id": "",
            "user_id": "",
            "jwt": ""
        }
        return f"📋 **State Template Structure**:\n```json\n{json.dumps(template, indent=2)}\n```\n\nThis template defines the expected keys for state management."
    
    # 6. Help Intent (context-aware)
    help_keywords = [
        "help", "what can you do", "how to", "commands", "available", 
        "capabilities", "features", "what do you do", "assist me"
    ]
    
    if any(keyword in user_input_lower for keyword in help_keywords):
        help_response = """🤖 **I can help you with state management! Here's what I can do:**

📋 **Get Summaries**: Ask me to summarize your current state
   - "Give me a summary"
   - "Summarize my current state"
   - "What's in my state?"

📊 **Access State**: Get detailed state information
   - "Show me my state"
   - "Access my current state"
   - "Display all data"

🔄 **Update State**: Change specific values
   - "Update user_id to john123"
   - "Change _id to abc123"
   - "Set jwt to new_token"
   - "Update my _id to test456"

📋 **View Template**: See the data structure
   - "Show me the template"
   - "What keys are available?"
   - "Data structure"

💡 **Natural Language**: I understand various ways to ask for the same thing, including spelling mistakes and different phrasings!"""
        
        if has_data:
            help_response += f"\n\n📊 **Current Status**: You have {json_inputs_count} JSON inputs and data in your state."
        else:
            help_response += "\n\n📊 **Current Status**: Your state is empty. Try processing some JSON data!"
            
        return help_response
    
    # 7. Greeting Intent
    greeting_keywords = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(keyword in user_input_lower for keyword in greeting_keywords):
        if has_data:
            return f"👋 Hello! I see you have data in your state ({json_inputs_count} JSON inputs processed). How can I help you manage it today?"
        else:
            return "👋 Hello! I'm here to help you manage your state. Your state is currently empty - would you like to process some JSON data to get started?"
    
    # 8. Behavior summary request
    behavior_keywords = ["recent behavior", "behavior", "behaviour", "emotion spans", "timeline summary"]
    if any(keyword in user_input_lower for keyword in behavior_keywords):
        return _generate_behavior_summary_from_state(session_state)

    # 9. Context-aware default response
    if not has_data:
        return "💡 **Getting Started**: Your state is currently empty. Here are some things you can do:\n\n• **Process JSON**: feed model outputs directly; ingestion is automatic.\n• **Learn More**: 'What can you do?' or 'Help me'\n• **See Structure**: 'Show me the template'"
    
    # 10. Intelligent fallback with context
    return f"🤔 **I understand you're asking about your state**, but I'm not sure exactly what you need. Based on your current state ({json_inputs_count} JSON inputs), here are some helpful options:\n\n• **📋 Summaries**: 'Give me a summary' or 'Summarize recent behavior'\n• **📊 Details**: 'Show me my state' or 'Access state'\n• **❓ Help**: 'What can you do?' or 'Help me'\n\n💡 **You can also ask for 'emotion spans' or 'timeline summary'."

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

        session_state = context.state if hasattr(context, "state") else {}
        # Use our deterministic conversational response (includes behavior summary from alerts/timeline)
        return handle_conversational_query(query, session_state)
    except Exception as e:
        return f"Error handling message: {e}"
