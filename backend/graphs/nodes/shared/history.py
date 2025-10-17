"""
Shared History Node

Load conversation history from database.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler
from db.repositories.chat_repository import ChatRepository
from graphs.nodes.models import HistoryNodeInput, HistoryNodeOutput


class HistoryCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for history loading."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[HISTORY_CALLBACK] Retriever started")

    def on_retriever_end(self, documents, **kwargs):
        print("[HISTORY_CALLBACK] Retriever ended")


def get_chat_repository(state) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository
    if repo:
        return repo
    # Fallback
    return ChatRepository()


def history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load conversation history from database.

    Args:
        state: Current graph state

    Returns:
        Dict with history (list of BaseMessage objects)

    Streams:
        - on_retriever_start: Database retrieval started
        - on_retriever_end: Database retrieval completed
        - stage: History loading progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = HistoryNodeInput(
            session_id=state.session_id,
            chat_repository=get_chat_repository(state)
        )
    except Exception as e:
        raise ValueError(f"History input validation failed: {e}")

    print(f"[HISTORY_NODE] Loading history for session: {input_data.session_id}")

    # Emit retriever start event
    callback_handler = HistoryCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "history_retriever"},
        query=input_data.session_id
    )

    db_messages = input_data.chat_repository.get_messages(input_data.session_id)

    # Convert to LangChain messages
    history = []
    for msg in db_messages:
        if msg['role'] == 'user':
            history.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            history.append(AIMessage(content=msg['content']))

    # Add system message if history is empty
    if not history:
        history = [SystemMessage(content="You are a helpful assistant.")]

    # Emit retriever end event
    callback_handler.on_retriever_end(documents=history)

    print(f"[HISTORY_NODE] ✓ Loaded {len(history)} messages")

    # Return validated output
    output_data = HistoryNodeOutput(history=history)
    return output_data.model_dump()


def history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load conversation history from database.

    Args:
        state: Current graph state

    Returns:
        Dict with chat_history (list of messages)

    Streams:
        - on_chain_end: History loading completed
    """


def get_chat_repository(state) -> ChatRepository:
    """Extract ChatRepository from state or create new instance."""
    repo = state.chat_repository
    if repo:
        return repo
    # Fallback
    return ChatRepository()


def history_node(state) -> Dict[str, Any]:
    """
    Load conversation history from database.

    Args:
        state: Current graph state

    Returns:
        Dict with history (list of BaseMessage objects)

    Streams:
        - stage: History loading progress
    """
    # Validate inputs using Pydantic model
    try:
        # Handle both Pydantic models and dictionaries
        if hasattr(state, 'model_dump'):  # Pydantic model
            session_id = state.session_id
        else:  # Dictionary
            session_id = state["session_id"]

        input_data = HistoryNodeInput(
            session_id=session_id,
            chat_repository=get_chat_repository(state)
        )
    except Exception as e:
        raise ValueError(f"History input validation failed: {e}")

    print(f"[HISTORY_NODE] Loading history for session: {input_data.session_id}")

    db_messages = input_data.chat_repository.get_messages(input_data.session_id)

    # Convert to LangChain messages
    history = []
    for msg in db_messages:
        if msg['role'] == 'user':
            history.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            history.append(AIMessage(content=msg['content']))

    # Add system message if history is empty
    if not history:
        history = [SystemMessage(content="You are a helpful assistant.")]

    print(f"[HISTORY_NODE] ✓ Loaded {len(history)} messages")

    # Return history directly (preserve BaseMessage objects)
    return {"history": history}