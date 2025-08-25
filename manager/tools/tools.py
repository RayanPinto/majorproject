import json
import datetime
from google.adk.tools.tool_context import ToolContext

def log_delegation(delegated_to: str, query: str):
    """
    Log delegation events to track routing decisions.
    
    Args:
        delegated_to: The name of the agent being delegated to
        query: The user query that triggered the delegation
    """
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "delegated_to": delegated_to,
        "query": query,
        "event_type": "delegation"
    }
    
    # In a real implementation, this would be logged to a file or database
    # For now, we'll just return the log entry
    return f"Delegated to {delegated_to} at {timestamp} for query: {query}"

def transfer_to_state_agent(tool_context: ToolContext) -> None:
    """Transfer to the state agent for direct state operations."""
    tool_context.actions.transfer_to_agent = "state_agent"

def transfer_to_conversational_agent(tool_context: ToolContext) -> None:
    """Transfer to the conversational agent for natural language processing."""
    tool_context.actions.transfer_to_agent = "conversational_agent"
