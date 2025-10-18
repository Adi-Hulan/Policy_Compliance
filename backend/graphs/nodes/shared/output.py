"""
Shared Output Node

Prepares final output for client.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any, List
from langchain_core.callbacks import BaseCallbackHandler
from db.repositories.chat_repository import ChatRepository
from graphs.nodes.models import OutputNodeInput, OutputNodeOutput


class OutputCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for history serialization."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[OUTPUT_CALLBACK] History retriever started")

    def on_retriever_end(self, documents, **kwargs):
        print("[OUTPUT_CALLBACK] History retriever ended")


def get_chat_repository(state) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository if hasattr(state, 'chat_repository') else state.get('chat_repository')
    if repo:
        return repo
    # Fallback
    return ChatRepository()


def output_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare final output for client.

    Args:
        state: Current graph state

    Returns:
        Dict with content, history, citations, and chunk metadata

    Streams:
        - on_retriever_start: History retrieval started
        - on_retriever_end: History retrieval completed
        - final: Complete response with history
    """
    print(f"[OUTPUT_NODE] Processing state with response: {getattr(state, 'response', '')[:100]}...")
    print(f"[OUTPUT_NODE] Is final result: {state.get('final', False) if hasattr(state, 'get') else getattr(state, 'final', False)}")

    # Check if this is a streaming token (not final) - just pass it through
    final_flag = state.get('final', False) if hasattr(state, 'get') else getattr(state, 'final', False)
    if not final_flag:
        print("[OUTPUT_NODE] Streaming token - passing through without processing")
        return {"response": getattr(state, 'response', '')}

    # This is the final result - process citations and history
    print("[OUTPUT_NODE] Processing final result with citations")

    # Validate inputs using Pydantic model
    try:
        # Handle both object attributes and dict keys
        session_id = state.session_id if hasattr(state, 'session_id') else state.get('session_id')
        response = state.response if hasattr(state, 'response') else state.get('response')
        chat_repo = get_chat_repository(state)

        input_data = OutputNodeInput(
            session_id=session_id,
            response=response,
            chat_repository=chat_repo
        )
    except Exception as e:
        raise ValueError(f"Output input validation failed: {e}")

    print("[OUTPUT_NODE] Preparing final output")

    response_text = input_data.response
    session_id = input_data.session_id
    chunk_metadata = (state.get('chunk_metadata', []) if hasattr(state, 'get') else getattr(state, 'chunk_metadata', [])) or []

    # Get citation metadata from claim validator (if available)
    citation_metadata = state.get('citation_metadata', []) if hasattr(state, 'get') else getattr(state, 'citation_metadata', []) or []
    validation_recommendations = state.get('validation_recommendations', {}) if hasattr(state, 'get') else getattr(state, 'validation_recommendations', {}) or {}

    # Extract document_info from state
    document_info = state.get('document_info', None) if hasattr(state, 'get') else getattr(state, 'document_info', None)

    # Debug: Log document_info in the final output
    print(f"[DEBUG] Document Info: {document_info}")

    # Emit retriever start event for history serialization
    callback_handler = OutputCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "history_serializer"},
        query=session_id or "no_session"
    )

    # Serialize history for output
    history_serialized = []
    if session_id:
        db_messages = input_data.chat_repository.get_messages(session_id)
        history_serialized = [
            {"type": msg['role'], "content": msg['content']}
            for msg in db_messages
        ]

    # Emit retriever end event
    callback_handler.on_retriever_end(documents=history_serialized)

    print(f"[OUTPUT_NODE] ✓ Response length: {len(response_text)} chars")
    print(f"[OUTPUT_NODE] ✓ History: {len(history_serialized)} messages")
    print(f"[OUTPUT_NODE] ✓ Citations: {len(citation_metadata)} validated")

    # Return validated output with citations and chunk metadata
    output_data = OutputNodeOutput(
        content=response_text,
        history=history_serialized,
        chunk_metadata=chunk_metadata,
        citation_metadata=citation_metadata,
        validation_recommendations=validation_recommendations,
        document_info=document_info,  # Add document_info here
        final=True  # Explicitly mark as final
    )
    # Debug: Print the final JSON response sent to the frontend
    print(f"[OUTPUT_NODE] Final JSON response: {output_data.model_dump()}")
    return output_data.model_dump()