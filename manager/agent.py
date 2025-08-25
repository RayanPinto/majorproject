from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from .tools.tools import log_delegation, transfer_to_state_agent, transfer_to_conversational_agent
from .sub_agents.state_agent import state_agent
from .sub_agents.conversational_agent import conversational_agent, handle_conversational_query
import datetime
import json

# ... (imports unchanged)

def classify_query(query: str):
    query_lower = query.lower()
    
    # Direct command patterns (exact syntax)
    direct_commands = [
        "process this json:", "update state:", "summary", "access state",
        "show template", "simulate json", "show my state", "display state"
    ]
    
    # JSON processing patterns (natural language)
    json_patterns = [
        "add this json", "process this json", "save this json", "store this json",
        "input this json", "add json", "process json", "save json", "store json",
        "append", "add this", "save this", "store this", "process this"
    ]
    
    # State update patterns (natural language)
    update_patterns = [
        "update my", "change my", "modify my", "set my", "update the", "change the",
        "modify the", "set the", "update user_id", "change user_id", "update _id", "change _id"
    ]
    
    # Help and capability inquiry patterns (more specific)
    help_patterns = [
        "help", "what can you do", "how do i", "how to", "explain", "guide", "assist",
        "what are your capabilities", "what can you help with", "how does this work",
        "what can you", "how do you", "explain to me"
    ]
    
    # Information request patterns (more specific, avoiding overlap with help)
    info_patterns = [
        "give me", "show me", "tell me", "what's in", "what is in", "summarize", "summarise", 
        "overview", "current state", "my state", "describe", "what's my", "what is my"
    ]
    
    # Greeting patterns
    greeting_patterns = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening"
    ]

    # Check patterns in order of specificity (more specific patterns first)
    if any(command in query_lower for command in direct_commands):
        return "state"
    if any(pattern in query_lower for pattern in json_patterns):
        return "conversational"
    if any(pattern in query_lower for pattern in update_patterns):
        return "conversational"
    if any(pattern in query_lower for pattern in help_patterns):
        return "conversational"
    if any(pattern in query_lower for pattern in greeting_patterns):
        return "conversational"
    if any(pattern in query_lower for pattern in info_patterns):
        return "conversational"
    
    return "conversational"  # Default to conversational for flexibility


state_manager_agent = Agent(
    name="state_manager",
    model="gemini-2.0-flash",  # Can upgrade to a more advanced model if needed
    description="Manager agent that routes queries to appropriate sub-agents for state management and conversational interactions.",
    instruction="""
===========================================
🔧 ROLE OVERVIEW — Multi-Agent Orchestrator
===========================================
You are the **central manager agent** for a sophisticated state management system with multiple specialized sub-agents.

Your job is to:
1. Analyze user queries intelligently
2. Route to the most appropriate sub-agent(s)
3. Coordinate multi-agent responses when needed
4. Ensure optimal task delegation and execution

===========================================
📤 ADVANCED TASK CLASSIFICATION & ROUTING
===========================================

🎯 **Route to `state_agent` for:**
- Direct command syntax: "Process this JSON:", "Update state:", "summary", "access state"
- Exact command matching
- Low-level state operations
- Template management

🎯 **Route to `conversational_agent` for:**
- Natural language queries: "give me summary", "show me state", "what's in my data"
- Conversational patterns: "tell me", "how to", "explain", "help"
- JSON processing with natural language: "add this json", "process this data"
- State updates with natural language: "update my _id", "change user_id to"
- Greetings and general conversation: "hi", "hello", "hey"
- Spelling mistakes and variations
- Context-aware responses

🎯 **Multi-Agent Coordination:**
- For complex queries requiring multiple agents
- When both state operations and conversational responses are needed
- Coordinated responses from multiple sub-agents

===========================================
🧠 INTELLIGENT DELEGATION STRATEGY
===========================================

✅ **Smart Routing Logic:**
- Analyze query intent and context
- Consider current state and user history
- Choose the most appropriate agent(s)
- Handle edge cases and ambiguities

✅ **State Context Awareness:**
- `state["json_inputs"]`: Track processed JSON data
- `state["current_state"]`: Monitor current values
- `state["last_update"]`: Consider timing context

===========================================
🎯 EXAMPLES FOR CLARITY
===========================================

**User Query:** "Process this JSON: {'key': 'value'}"  
➡️ Route to: `state_agent` (exact command)

**User Query:** "Give me a summary"  
➡️ Route to: `conversational_agent` (natural language)

**User Query:** "Update state: _id=newvalue"  
➡️ Route to: `state_agent` (exact command)

**User Query:** "What's in my current state?"  
➡️ Route to: `conversational_agent` (natural language)

**User Query:** "add this json {'id': '123'}"  
➡️ Route to: `conversational_agent` (natural language JSON processing)

**User Query:** "update my _id to test456"  
➡️ Route to: `conversational_agent` (natural language update)

**User Query:** "hi"  
➡️ Route to: `conversational_agent` (greeting)

===========================================
🎨 STYLE & INTERACTION RULES
===========================================
- Always respond clearly and precisely
- Use JSON formatting and markdown where appropriate
- Be friendly, professional, and encouraging
- Focus on intelligent delegation and coordination
- Provide context-aware routing decisions
""",
    sub_agents=[state_agent, conversational_agent],
    tools=[
        FunctionTool(func=transfer_to_state_agent),
        FunctionTool(func=transfer_to_conversational_agent),
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
    elif classification == "conversational":
        # Log delegation manually
        log_delegation("conversational_agent", query)
        return await context.delegate_to(conversational_agent)
    else:
        # Default to conversational for natural language
        log_delegation("conversational_agent", query)
        return await context.delegate_to(conversational_agent)
