"""
Shared Session Update Node

Save conversation to database.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any
from db.repositories.chat_repository import ChatRepository
from graphs.nodes.models import SessionUpdateNodeInput, SessionUpdateNodeOutput
from .output import get_chat_repository


def session_update_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save conversation to database.

    Args:
        state: Current graph state

    Returns:
        Empty dict (update happens as side effect)

    Streams:
        - stage: Session update progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = SessionUpdateNodeInput(
            session_id=state.session_id,
            user_id=state.user_id,
            message=state.message,
            response=state.response,
            chat_repository=get_chat_repository(state)
        )
    except Exception as e:
        raise ValueError(f"Session update input validation failed: {e}")

    session_id = input_data.session_id
    user_id = input_data.user_id
    user_message = input_data.message
    ai_response = input_data.response

    # Grab citation metadata early so we can persist it with the assistant message
    citation_metadata = getattr(state, 'citation_metadata', None)
    documents = getattr(state, 'documents', None)

    print(f"[SESSION_UPDATE_NODE] Saving to database")
    print(f"[SESSION_UPDATE_NODE] Session: {session_id}")

    try:
        repo = input_data.chat_repository

        # Ensure session exists
        repo.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            title=user_message[:50] if user_message else "New Chat"
        )

        # Save user message
        repo.save_message(
            session_id=session_id,
            role='user',
            content=user_message,
            metadata=None
        )

        # Save assistant response
        # Persist citation metadata (if present) with the assistant message so
        # it survives page refreshes and can be retrieved later.
        assistant_metadata = None
        if citation_metadata:
            assistant_metadata = {
                'citation_metadata': citation_metadata,
            }
            # include documents if available for easier frontend lookup
            if documents:
                assistant_metadata['documents'] = documents

        print(f"[SESSION_UPDATE_NODE] Saving assistant message, citations={len(citation_metadata) if citation_metadata else 0}")
        repo.save_message(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            metadata=assistant_metadata
        )

        print(f"[SESSION_UPDATE_NODE] ✓ Saved conversation")

    except Exception as e:
        print(f"[SESSION_UPDATE_NODE] ✗ Save failed: {e}")

    # Return validated output (empty) but preserve all state fields
    output_data = SessionUpdateNodeOutput()
    result = output_data.model_dump()
    
    # Debug: Check citations in state before forwarding
    citation_metadata = getattr(state, 'citation_metadata', None)
    print(f"[SESSION_UPDATE_NODE] Citations in state: {len(citation_metadata) if citation_metadata else 0}")
    
    # Preserve only the fields needed by the output_node
    result.update({
        'session_id': state.session_id,
        'response': state.response,
        'chat_repository': state.chat_repository,
        'citation_metadata': citation_metadata,
        'validation_recommendations': getattr(state, 'validation_recommendations', None),
        'chunk_metadata': getattr(state, 'chunk_metadata', None),
        'final': True,  # Always set final=True for output processing
    })
    
    # Ensure the final flag is set to True
    result['final'] = True
    
    # Extract document_info from state if available
    document_info = getattr(state, 'document_info', None)

    # Update result with document_info
    result.update({
        'document_info': document_info,
    })
    
    print(f"[SESSION_UPDATE_NODE] Forwarding citations to output: {len(result.get('citation_metadata', []))}")
    
    return result