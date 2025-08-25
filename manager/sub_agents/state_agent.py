from google.adk.agents import Agent
import datetime
import json

state_agent = Agent(
    name="state_agent",
    model="gemini-1.5-flash",
    description="State agent that manages a template-based state, updates it with matching JSON keys, and allows modifications/summaries.",
    instruction="""
You are the **state agent** managing a template-based state system.

Your role is to respond to user queries about state management. The actual state updates are handled by the system automatically.

When users ask about:
- JSON processing: Explain what would happen
- State updates: Explain the process
- Summaries: Describe what information would be shown
- State access: Explain what would be displayed

Be helpful and informative, but note that the actual state management is handled by the system.
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
