"""
Shared Output Node

Prepares final output for client.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any, List
import re
from langchain_core.callbacks import BaseCallbackHandler
from db.repositories.chat_repository import ChatRepository
from graphs.nodes.models import OutputNodeInput, OutputNodeOutput


def parse_citations_from_response(response_text: str, chunk_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse citation markers from LLM response and link them to chunk metadata.

    Looks for patterns like [SOURCE:policy_chunk_1] or [SOURCE:document_chunk_2]
    """
    citations = []

    # Pattern to match citation markers
    citation_pattern = r'\[SOURCE:([a-zA-Z_]+_chunk_\d+)\]'

    for match in re.finditer(citation_pattern, response_text):
        chunk_id = match.group(1)

        # Find the corresponding chunk metadata
        chunk_info = None
        for chunk in chunk_metadata:
            if chunk.get('id') == chunk_id:
                chunk_info = chunk
                break

        if chunk_info:
            citations.append({
                'text': match.group(0),  # The full [SOURCE:...] text
                'chunk_id': chunk_id,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'chunk_content': chunk_info.get('content', ''),
                'chunk_type': chunk_info.get('type', ''),
                'source': chunk_info.get('source', '')
            })

    return citations


class OutputCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for history serialization."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[OUTPUT_CALLBACK] History retriever started")

    def on_retriever_end(self, documents, **kwargs):
        print("[OUTPUT_CALLBACK] History retriever ended")


def get_chat_repository(state) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository
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
    print(f"[OUTPUT_NODE] Is final result: {getattr(state, 'final', False)}")

    # Check if this is a streaming token (not final) - just pass it through
    if not getattr(state, 'final', False):
        print("[OUTPUT_NODE] Streaming token - passing through without processing")
        return {"response": getattr(state, 'response', '')}

    # This is the final result - process citations and history
    print("[OUTPUT_NODE] Processing final result with citations")

    # Validate inputs using Pydantic model
    try:
        input_data = OutputNodeInput(
            session_id=state.session_id,
            response=state.response,
            chat_repository=get_chat_repository(state)
        )
    except Exception as e:
        raise ValueError(f"Output input validation failed: {e}")

    print("[OUTPUT_NODE] Preparing final output")

    response_text = input_data.response
    session_id = input_data.session_id
    chunk_metadata = getattr(state, 'chunk_metadata', []) or []

    # Parse citations from the response
    citations = parse_citations_from_response(response_text, chunk_metadata)
    print(f"[OUTPUT_NODE] Found {len(citations)} citations in response")

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
    print(f"[OUTPUT_NODE] ✓ Citations: {len(citations)}")

    # Return validated output with citations and chunk metadata
    output_data = OutputNodeOutput(
        content=response_text,
        history=history_serialized,
        citations=citations,
        chunk_metadata=chunk_metadata
    )
    return output_data.model_dump()