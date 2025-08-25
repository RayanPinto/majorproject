import json
import datetime

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
