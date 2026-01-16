"""
Company Policy Graph Module

Defines the LangGraph workflow for company policy queries.
Handles document processing, policy retrieval, and response generation.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from utils.prompts import MAIN_PROMPT
from agents.chuck_retriever import Retriever
from agents.chunk_retriever_temp import TempRetriever
from agents.attached_document_processor import DocumentProcessorTemp
from langchain_google_genai import ChatGoogleGenerativeAI
from db.repositories.chat_repository import ChatRepository
import os
import tempfile
import requests
from db.connection import get_db

# Import Pydantic models
from .nodes.models import CompanyPolicyState

# Import shared nodes
from .nodes.shared.input import input_node
from .nodes.shared.history import history_node
from .nodes.shared.llm import llm_node
from .nodes.shared.session_update import session_update_node
from .nodes.shared.output import output_node
from .nodes.shared.claim_validator import claim_validator_node

# Import company policy specific nodes
from .nodes.company_policy.policy_retriever import policy_retriever_node
from .nodes.company_policy.document_download import document_download_node
from .nodes.company_policy.document_processing import document_processing_node
from .nodes.company_policy.document_retriever import document_retriever_node
from .nodes.company_policy.context_combination import context_combination_node

# Import prompts
from utils.prompts import MAIN_PROMPT

# Import Pydantic models
from graphs.nodes.models import CompanyPolicyState


# --- Node Wrappers ---
async def company_policy_llm_node(state):
    """Wrapper for LLM node with company policy prompt."""
    from .nodes.shared.llm import llm_node
    # Add honesty instruction: tell model to admit when attached document content
    honesty_instruction = (
        "\n\nHONESTY INSTRUCTION: If the user asks about an uploaded or attached document but you cannot find any attached document content in the provided context, be explicit: say you cannot identify or access the uploaded document content for this session and ask the user to re-upload or clarify. Do NOT guess or invent document-specific facts if the attached document is not present."
    )
    system_prompt = f"{MAIN_PROMPT}{honesty_instruction}"
    return await llm_node(state, system_prompt, "full_user_message")


# --- Graph Construction ---


# --- State Definition ---


# --- Helper Functions ---
def get_chat_repository(state: CompanyPolicyState) -> ChatRepository:
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
def route_after_history(state: CompanyPolicyState) -> str:
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


def route_after_policy(state: CompanyPolicyState) -> str:
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
def build_company_policy_graph():
    """
    Build and compile the company policy graph.
    
    Returns:
        Compiled LangGraph instance
    """
    # Building company policy graph
    
    graph = StateGraph(CompanyPolicyState)
    
    # Add all nodes
    graph.add_node("input", input_node)
    graph.add_node("history", history_node)
    graph.add_node("doc_download", document_download_node)
    graph.add_node("doc_process", document_processing_node)
    graph.add_node("policy_retriever", policy_retriever_node)
    graph.add_node("doc_retriever", document_retriever_node)
    graph.add_node("context_combine", context_combination_node)
    graph.add_node("llm", company_policy_llm_node)
    graph.add_node("claim_validator", claim_validator_node)
    graph.add_node("session_update", session_update_node)
    graph.add_node("output", output_node)
    
    # Linear flow: START → input → history
    graph.add_edge(START, "input")
    graph.add_edge("input", "history")
    
    # Conditional routing after history
    graph.add_conditional_edges(
        "history",
        route_after_history,
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
        route_after_policy,
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
    
    # Company policy graph compiled
    return graph.compile()


# --- Legacy Function (for backwards compatibility) ---
def run_company_policy(session_id: str, message: str, document_url: str = None, user_id: str = None) -> str:
    """
    Run the company policy graph synchronously (legacy interface).
    
    Args:
        session_id: Session identifier
        message: User message
        document_url: Optional document URL
        user_id: Optional user identifier
        
    Returns:
        Response text
    """
    # Debug: Start of run_company_policy
    # print(f"[RUN_COMPANY_POLICY] Starting synchronous execution")
    # print(f"[RUN_COMPANY_POLICY] Session: {session_id}")
    # print(f"[RUN_COMPANY_POLICY] Message: {message[:100]}...")
    
    try:
        app = build_company_policy_graph()
        initial_state: CompanyPolicyState = {
            "session_id": session_id,
            "message": message,
            "document_url": document_url,
            "user_id": user_id,
            "chat_repository": ChatRepository(),
        }

        # Debug: Invoking graph
        # print("[RUN_COMPANY_POLICY] Invoking graph...")
        final_state = app.invoke(initial_state)

        # Debug: Check citations in final_state before extracting content
        if hasattr(final_state, 'citations'):
            print(f"[DEBUG] Citations in final_state: {final_state.citations}")
        else:
            print("[DEBUG] No citations attribute in final_state")

        # Extract response
        content = final_state.content or final_state.response or ""

        # Debug: Check for citations in content
        if hasattr(final_state, 'citations'):
            print(f"[DEBUG] Citations passed to output: {final_state.citations}")
        else:
            print("[DEBUG] No citations attribute in final_state at output")

        # print(f"[RUN_COMPANY_POLICY] ✓ Response length: {len(content)} chars")
        return content

    except Exception as e:
        # print(f"[RUN_COMPANY_POLICY] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing request: {str(e)}"