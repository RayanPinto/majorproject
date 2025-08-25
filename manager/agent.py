from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from .tools.tools import log_delegation
from .sub_agents.state_agent import state_agent
import datetime
import json

def classify_query(query: str):
    query_lower = query.lower()

    json_triggers = ["process json", "save json", "update state", "summary", "provide summary", "access state"]
    if any(trigger in query_lower for trigger in json_triggers):
        return "state"
    else:
        return "general"

state_manager_agent = Agent(
    name="state_manager",
    model="gemini-1.5-flash",  # Can upgrade to a more advanced model if needed
    description="Manager agent that routes queries to the state agent for handling JSON-structured outputs and state management.",
    instruction="""
===========================================
🔧 ROLE OVERVIEW — Stateful JSON Manager
===========================================
You are the **core routing agent** for managing JSON-structured outputs in a stateful system.

Your job is to:
1. Understand the user's query
2. If it involves processing JSON, saving to state, updating state, or requesting summaries, route to the `state_agent`
3. Call the `log_delegation` tool when routing
4. Focus on efficient state management only

===========================================
📤 TASK CLASSIFICATION & ROUTING STRATEGY
===========================================

➡️ Route to `state_agent` if the query:
- Includes: "process json", "save json", "update state with json"
- Requests: "provide summary", "access state", "summarize json"
- Involves real-time state updates or JSON collection

❓ If the query is ambiguous:
- Ask a **clarifying question** before routing

===========================================
🧠 STATE MEMORY MANAGEMENT
===========================================

✅ Focus on these core state fields:
- `state["json_inputs"]`: Store raw JSON data
- `state["current_state"]`: Template with values
- `state["last_update"]`: Timestamp of last update

===========================================
🎯 EXAMPLES FOR CLARITY
===========================================

**User Query:** "Process this JSON: {'key': 'value'}"  
➡️ Route to: `state_agent`  

**User Query:** "Provide a summary of the stored JSON"  
➡️ Route to: `state_agent`  

**User Query:** "Update state: _id=newvalue"  
➡️ Route to: `state_agent`

===========================================
🎨 STYLE & INTERACTION RULES
===========================================
- Always respond clearly and precisely
- Use JSON formatting and markdown where appropriate
- Be friendly, professional, and encouraging
- Focus on state management efficiency
""",
    sub_agents=[state_agent],
    tools=[
        AgentTool(state_agent),
    ],
)

async def handle_message(context):
    query = context.user_content.parts[0].text
    state = context.state

    classification = classify_query(query)

    if classification == "state":
        # Log delegation manually
        log_delegation("state_agent", query)
        return await context.delegate_to(state_agent)
    else:
        return "This query doesn't seem related to state management. How can I assist?"
