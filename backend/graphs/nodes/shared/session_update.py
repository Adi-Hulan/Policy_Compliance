"""
Shared Session Update Node

Save conversation to database.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any
from db.repositories.chat_repository import ChatRepository
from graphs.nodes.models import SessionUpdateNodeInput, SessionUpdateNodeOutput


def session_update_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save conversation to database.

    Args:
        state: Current graph state

    Returns:
        Empty dict (side effects only)

    Streams:
        - on_chain_end: Session update completed
    """


def get_chat_repository(state) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository
    if repo:
        return repo
    # Fallback
    return ChatRepository()


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
        repo.save_message(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            metadata=None
        )

        print(f"[SESSION_UPDATE_NODE] ✓ Saved conversation")

    except Exception as e:
        print(f"[SESSION_UPDATE_NODE] ✗ Save failed: {e}")

    # Return validated output (empty)
    output_data = SessionUpdateNodeOutput()
    return output_data.model_dump()