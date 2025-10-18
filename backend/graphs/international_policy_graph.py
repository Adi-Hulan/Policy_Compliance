"""
International Policy Graph Module

Defines the LangGraph workflow for international policy queries.
Handles document processing, international policy retrieval, and response generation.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from utils.prompts import MAIN_PROMPT
from agents.international_policy_retriever import InternationalPolicyRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
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
from .nodes.shared.claim_validator import claim_validator_node

# Import international policy specific nodes
from .nodes.international.policy_retriever import international_policy_retriever_node
from .nodes.international.document_download import international_document_download_node
from .nodes.international.document_processing import international_document_processing_node
from .nodes.international.document_retriever import international_document_retriever_node
from .nodes.international.context_combination import international_context_combination_node

# Import prompts
from utils.prompts import MAIN_PROMPT

# Import Pydantic models
from graphs.nodes.models import InternationalPolicyState


# --- Node Wrappers ---
async def international_policy_llm_node(state):
    """Wrapper for LLM node with international policy prompt."""
    from .nodes.shared.llm import llm_node

    # Create a specialized prompt for international policy
    INTERNATIONAL_POLICY_PROMPT = f"""{MAIN_PROMPT}

You are an expert compliance consultant specializing in international regulations and standards. Your expertise includes:

INTERNATIONAL REGULATIONS:
- GDPR (General Data Protection Regulation) - EU data protection
- HIPAA (Health Insurance Portability and Accountability Act) - US healthcare data
- SOX (Sarbanes-Oxley Act) - US financial reporting
- ISO 27001 - Information security management
- CCPA (California Consumer Privacy Act) - US state privacy law
- And other international compliance frameworks

When answering questions about international policies:
1. Always cite the specific regulation and relevant sections
2. Explain requirements clearly and practically
3. Note any regional variations or exceptions
4. Suggest implementation approaches when appropriate
5. Reference related policies or standards when relevant

Be precise, authoritative, and focused on compliance requirements."""

    return await llm_node(state, INTERNATIONAL_POLICY_PROMPT, "full_user_message")


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

    # Add all nodes
    graph.add_node("input", input_node)
    graph.add_node("history", history_node)
    graph.add_node("doc_download", international_document_download_node)
    graph.add_node("doc_process", international_document_processing_node)
    graph.add_node("policy_retriever", international_policy_retriever_node)
    graph.add_node("doc_retriever", international_document_retriever_node)
    graph.add_node("context_combine", international_context_combination_node)
    graph.add_node("llm", international_policy_llm_node)
    graph.add_node("claim_validator", claim_validator_node)
    graph.add_node("session_update", session_update_node)
    graph.add_node("output", output_node)

    # Linear flow: START → input → history
    graph.add_edge(START, "input")
    graph.add_edge("input", "history")

    # Conditional routing after history
    graph.add_conditional_edges(
        "history",
        route_after_history_international,
        {
            "with_doc": "doc_download",      # New document, download it
            "has_doc": "policy_retriever",   # Existing document, skip to policy
            "no_doc": "policy_retriever",    # No document, skip to policy
        },
    )

    # Document processing flow
    graph.add_edge("doc_download", "doc_process")
    graph.add_edge("doc_process", "policy_retriever")

    # Conditional routing after policy retrieval
    graph.add_conditional_edges(
        "policy_retriever",
        route_after_policy_international,
        {
            "need_doc": "doc_retriever",           # Retrieve from temp document
            "no_doc_needed": "context_combine",    # Skip document retrieval
        },
    )

    # Linear flow: doc_retriever → context_combine → llm → claim_validator → session_update → output → END
    graph.add_edge("doc_retriever", "context_combine")
    graph.add_edge("context_combine", "llm")
    graph.add_edge("llm", "claim_validator")
    graph.add_edge("claim_validator", "session_update")
    graph.add_edge("session_update", "output")
    graph.add_edge("output", END)

    print("[INTERNATIONAL_POLICY_GRAPH] ✓ International policy graph compiled")
    return graph.compile()
# --- Legacy Function (for backwards compatibility) ---
def run_international_policy(session_id: str, message: str, document_url: str = None, user_id: str = None) -> str:
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
        initial_state: InternationalPolicyState = {
            "session_id": session_id,
            "message": message,
            "document_url": document_url,
            "user_id": user_id,
            "chat_repository": ChatRepository(),
        }

        # Debug: Invoking graph
        print("[RUN_INTERNATIONAL_POLICY] Invoking graph...")
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