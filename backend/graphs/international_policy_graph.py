"""
International Policy Graph Module

Defines the LangGraph workflow for international policy queries.
Handles document processing, international policy retrieval, and response generation.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from utils.prompts import MAIN_PROMPT
from db.repositories.chat_repository import ChatRepository
import os
import tempfile
import requests
from db.connection import get_db

# Import Pydantic models
from .nodes.models import InternationalPolicyState

# Import shared nodes
from .nodes.shared.input import input_node
from .nodes.shared.history import history_node
from .nodes.shared.llm import llm_node
from .nodes.shared.session_update import session_update_node
from .nodes.shared.output import output_node
# LLM node for international policies moved into the international nodes package
from .nodes.international.llm import international_policy_llm_node

# Note: For international policies we bypass the RAG pipeline and call the LLM directly.

# Import prompts
from utils.prompts import MAIN_PROMPT

# Import Pydantic models
from graphs.nodes.models import InternationalPolicyState


# Note: international_policy_llm_node moved to `graphs/nodes/international/llm.py`


# --- Graph Construction ---


# --- State Definition ---


# --- Helper Functions ---
def get_chat_repository(state: InternationalPolicyState) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository
    if repo:
        return repo
    # Fallback
    return ChatRepository()


def serialize_messages(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """Convert LangChain messages to serializable dicts."""
    return [{"type": type(msg).__name__, "content": msg.content} for msg in messages]


# --- Routing Functions ---
def route_after_history_international(state: InternationalPolicyState) -> str:
    """
    Route after history node based on document presence.

    Returns:
        "with_doc": New document URL provided, needs download/processing
        "has_doc": Existing temp table found, skip to retrieval
        "no_doc": No document, skip document pipeline
    """

    safe_session_id = state.safe_session_id
    document_url = state.document_url


    # Check if temp table exists
    has_temp = False
    if safe_session_id:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT to_regclass(%s)", (f"public.temp_documents_{safe_session_id}",))
            exists_row = cur.fetchone()
            cur.close()
            conn.close()
            has_temp = bool(exists_row and exists_row[0])
        except Exception as e:
            pass  # Exception ignored for temp table check

    if has_temp:
        return "has_doc"
    if document_url:
        return "with_doc"
    return "no_doc"


def route_after_policy_international(state: InternationalPolicyState) -> str:
    """
    Route after policy retrieval based on document availability.

    Returns:
        "need_doc": Temp table exists, retrieve document context
        "no_doc_needed": No temp table, skip to context combination
    """

    safe_session_id = state.safe_session_id

    # Check if temp table exists
    has_temp = False
    if safe_session_id:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT to_regclass(%s)", (f"public.temp_documents_{safe_session_id}",))
            exists_row = cur.fetchone()
            cur.close()
            conn.close()
            has_temp = bool(exists_row and exists_row[0])
        except Exception as e:
            pass  # Exception ignored for temp table check

    if has_temp:
        return "need_doc"
    else:
        return "no_doc_needed"


# --- Graph Construction ---
def build_international_policy_graph():
    """
    Build and compile the international policy graph.
    
    Returns:
        Compiled LangGraph instance
    """
    # Building international policy graph
    print("[INTERNATIONAL_POLICY_GRAPH] Building international policy graph")

    graph = StateGraph(InternationalPolicyState)

    # Add nodes. For international policies we skip retrieval nodes and call the LLM directly.
    graph.add_node("input", input_node)
    graph.add_node("history", history_node)
    graph.add_node("llm", international_policy_llm_node)
    # No claim validation for international policy flow; update session directly from LLM output
    graph.add_node("session_update", session_update_node)
    graph.add_node("output", output_node)

    # Linear flow: START → input → history
    graph.add_edge(START, "input")
    graph.add_edge("input", "history")

    # Direct flow for international policies: history -> llm -> session_update -> output
    graph.add_edge("history", "llm")
    graph.add_edge("llm", "session_update")
    graph.add_edge("session_update", "output")
    graph.add_edge("output", END)

    print("[INTERNATIONAL_POLICY_GRAPH] ✓ International policy graph compiled")
    return graph.compile()
# --- Legacy Function (for backwards compatibility) ---
def run_international_policy(session_id: str, message: str, document_url: str = None, user_id: str = None, intent: str = None) -> str:
    """
    Run the international policy graph synchronously (legacy interface).

    Args:
        session_id: Session identifier
        message: User message
        document_url: Optional document URL
        user_id: Optional user identifier

    Returns:
        Response text
    """
    # Debug: Start of run_international_policy
    print(f"[RUN_INTERNATIONAL_POLICY] Starting synchronous execution")
    print(f"[RUN_INTERNATIONAL_POLICY] Session: {session_id}")
    print(f"[RUN_INTERNATIONAL_POLICY] Message: {message[:100]}...")

    try:
        app = build_international_policy_graph()
        # Ensure required fields for state validation
        import uuid as _uuid
        resolved_user_id = user_id or str(_uuid.uuid4())
        resolved_intent = intent or "international_policy"

        initial_state: InternationalPolicyState = {
            "session_id": session_id,
            "message": message,
            "document_url": document_url,
            "user_id": resolved_user_id,
            "intent": resolved_intent,
            "chat_repository": ChatRepository(),
        }

        # Debug: Invoking graph (prefer async invocation because LLM node is async)
        print("[RUN_INTERNATIONAL_POLICY] Invoking graph...")
        try:
            # If the compiled graph supports async invocation, use it
            import asyncio
            if hasattr(app, "ainvoke"):
                final_state = asyncio.run(app.ainvoke(initial_state))
            else:
                final_state = app.invoke(initial_state)
        except Exception:
            # Second-chance: try synchronous invoke
            final_state = app.invoke(initial_state)

        # Extract response
        content = final_state.content or final_state.response or ""

        print(f"[RUN_INTERNATIONAL_POLICY] ✓ Response length: {len(content)} chars")
        return content

    except Exception as e:
        print(f"[RUN_INTERNATIONAL_POLICY] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing request: {str(e)}"