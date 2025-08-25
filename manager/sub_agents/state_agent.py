from google.adk.agents import Agent
import datetime
import json

state_agent = Agent(
    name="state_agent",
    model="gemini-2.0-flash",
    description="State agent that manages a template-based state, updates it with matching JSON keys, and allows modifications/summaries.",
    instruction="""
You are the **state agent** managing a template-based state system with direct execution capabilities.

Your role is to:
1. **Handle Direct Commands**: Process exact command syntax like "Process this JSON:" and "Update state:"
2. **Execute State Operations**: Perform actual state updates and JSON processing
3. **Provide Direct Responses**: Give immediate feedback on operations
4. **Manage Template**: Handle template-based state management

**Direct Command Handling:**
- "Process this JSON: {...}" → Execute JSON processing
- "Update state: key=value" → Execute state update
- "summary" → Generate and return state summary
- "access state" → Return detailed state information
- "show template" → Display template structure

**Response Style:**
- Be direct and actionable
- Provide immediate feedback
- Use clear, concise language
- Include relevant state information

**State Template:**
- `_id`: Unique identifier
- `user_id`: User identification
- `jwt`: JSON Web Token

Remember: You handle the actual state operations, not just explanations. Provide direct, actionable responses.
""",
    tools=[],
)

def initialize_default_template():
    """Initialize the default template with empty values"""
    return {
        "_id": "",
        "user_id": "",
        "jwt": ""
    }

def generate_summary(state):
    """Generate a summary of the current state"""
    current_state = state.get("current_state", {})
    if not current_state:
        return "No state data yet. Template not initialized."
    
    summary = "📋 Current State Summary:\n"
    summary += f"🕒 Last Updated: {state.get('last_update', 'Never')}\n\n"
    
    for key, value in current_state.items():
        if value:
            summary += f"✅ {key}: {value}\n"
        else:
            summary += f"⏳ {key}: [Empty - waiting for data]\n"
    
    return summary

# Note: The ADK agent will use the instruction to handle responses
# The handle_message function is not needed as the LLM will process the instructions
