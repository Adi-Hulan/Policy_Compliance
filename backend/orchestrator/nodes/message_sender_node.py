"""
Supabase Message Sender Node for LangGraph Pipeline.
This node sends the AI response back to the Supabase messages table.
"""
import uuid
from datetime import datetime
from typing import Dict, Any

from utils.supabase_client import supabase

def message_sender_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends the analysis result back to the Supabase messages table as a new message.
    
    Args:
        state: The current state of the pipeline including the result from the analyzer
        
    Returns:
        The updated state with information about the sent message
    """
    try:
        # Check if we have a result to send
        if not state.get("result"):
            return {
                **state,
                "message_status": "error",
                "message_error": "No result to send as message"
            }
        
        # Generate a UUID for the message
        message_id = str(uuid.uuid4())
        
        # Create timestamp
        created_at = datetime.utcnow().isoformat()
        
        # Prepare message data
        message_data = {
            "id": message_id,
            "content": state["result"],
            "username": "agent",
            "room": "my-chat-room",
            "created_at": created_at
        }
        
        # Insert the message into Supabase
        result = supabase.table("messages").insert(message_data).execute()
        
        # Check for errors
        if hasattr(result, 'error') and result.error:
            return {
                **state,
                "message_status": "error",
                "message_error": str(result.error)
            }
        
        # Return success state
        return {
            **state,
            "message_status": "success",
            "message_id": message_id,
            "message_created_at": created_at
        }
        
    except Exception as e:
        # Handle any exceptions
        return {
            **state,
            "message_status": "error",
            "message_error": str(e)
        }
