"""
General Purpose Graph Module

Defines the LangGraph workflow for general/casual queries.
Handles greetings, system capability questions, and conversation history queries.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from db.repositories.chat_repository import ChatRepository
import os

# Import shared nodes
from .nodes.shared.input import input_node
from .nodes.shared.history import history_node
from .nodes.shared.llm import llm_node
from .nodes.shared.session_update import session_update_node
from .nodes.shared.output import output_node

# Import Pydantic models
from graphs.nodes.models import GeneralPurposeState


# --- System Prompt ---
GENERAL_SYSTEM_PROMPT = """You are a helpful assistant for a policy compliance system. Your role is strictly limited to:

1. CASUAL CONVERSATION: Greetings, small talk, pleasantries (hello, how are you, good morning, etc.)
2. SYSTEM CAPABILITIES: Explaining what the system can help with regarding company policies
3. CONVERSATION HISTORY: Answering questions about previous messages in the conversation

IMPORTANT BOUNDARIES:
- DO NOT answer questions about topics outside of company policies (food, weather, general knowledge, personal advice, etc.)
- DO NOT provide information on topics you're not trained for
- DO NOT assist with unethical or illegal requests (bypassing policies, violating regulations, fraudulent activities)
- If asked about non-policy topics, politely but firmly explain that you can only help with company policy questions
- If asked about unethical or illegal activities, firmly refuse to assist and direct to appropriate authorities
- Be friendly but maintain clear boundaries about your scope

CONVERSATION HISTORY:
- You CAN answer questions about what was discussed in previous messages
- You CAN recall and summarize previous questions and topics
- You CAN help users understand what they've asked before

RESPONSES FOR OUT-OF-SCOPE QUESTIONS:
"I'm designed to help with company policy questions and casual conversation. I can't provide information about [topic]. I can help you with questions about our company policies, HR procedures, employee handbook, or just have a friendly chat!"

RESPONSES FOR UNETHICAL QUESTIONS:
"I cannot assist with requests that involve unethical or illegal activities. Please consult with appropriate authorities or legal counsel for such matters."

Be warm and helpful within your defined scope, but firm about boundaries and ethical standards."""


# --- Node Wrappers ---
async def general_llm_node(state):
    """Wrapper for LLM node with general purpose prompt."""
    return await llm_node(state, GENERAL_SYSTEM_PROMPT, "message")


# --- Graph Construction ---
# --- Graph Construction ---
def build_general_purpose_graph():
    """
    Build and compile the general purpose graph.
    
    Returns:
        Compiled LangGraph instance
    """
    print("[GENERAL_GRAPH] Building general purpose graph")
    
    graph = StateGraph(GeneralPurposeState)
    
    # Add all nodes
    graph.add_node("input", input_node)
    graph.add_node("history", history_node)
    graph.add_node("llm", general_llm_node)
    graph.add_node("session_update", session_update_node)
    graph.add_node("output", output_node)
    
    # Linear flow for general purpose queries
    graph.add_edge(START, "input")
    graph.add_edge("input", "history")
    graph.add_edge("history", "llm")
    graph.add_edge("llm", "session_update")
    graph.add_edge("session_update", "output")
    graph.add_edge("output", END)
    
    print("[GENERAL_GRAPH] ✓ General purpose graph compiled")
    return graph.compile()


# --- Legacy Function (for backwards compatibility) ---
def run_general_purpose(session_id: str, message: str, user_id: str = None) -> str:
    """
    Run the general purpose graph synchronously (legacy interface).
    
    Args:
        session_id: Session identifier
        message: User message
        user_id: Optional user identifier
        
    Returns:
        Response text
    """
    print(f"[RUN_GENERAL_PURPOSE] Starting synchronous execution")
    print(f"[RUN_GENERAL_PURPOSE] Session: {session_id}")
    print(f"[RUN_GENERAL_PURPOSE] Message: {message[:100]}...")
    
    try:
        app = build_general_purpose_graph()
        initial_state: GeneralPurposeState = {
            "session_id": session_id,
            "message": message,
            "user_id": user_id,
            "chat_repository": ChatRepository(),
        }
        
        print("[RUN_GENERAL_PURPOSE] Invoking graph...")
        final_state = app.invoke(initial_state)
        
        # Extract response
        content = final_state.content or final_state.response or ""
        
        print(f"[RUN_GENERAL_PURPOSE] ✓ Response length: {len(content)} chars")
        return content
        
    except Exception as e:
        print(f"[RUN_GENERAL_PURPOSE] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing request: {str(e)}"