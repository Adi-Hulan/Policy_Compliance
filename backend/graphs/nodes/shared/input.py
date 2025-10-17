"""
Shared Input Node

Validates required inputs and creates safe session ID.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any
from graphs.nodes.models import InputNodeInput, InputNodeOutput


def input_node(state) -> Dict[str, Any]:
    """
    Validate session ID and user input.

    Args:
        state: Current graph state (Pydantic model or dict)

    Returns:
        Dict with safe_session_id

    Streams:
        - on_chain_start: Input validation started
        - on_chain_end: Input validation completed
    """
    # Validate inputs using Pydantic model
    try:
        input_data = InputNodeInput(
            session_id=state.session_id,
            user_id=state.user_id,
            message=state.message,
            document_url=state.document_url,
            intent=state.intent
        )
    except Exception as e:
        raise ValueError(f"Input validation failed: {e}")

    print(f"[INPUT_NODE] Validating inputs")
    print(f"[INPUT_NODE] Session: {input_data.session_id}")
    print(f"[INPUT_NODE] User: {input_data.user_id}")
    print(f"[INPUT_NODE] Message: {input_data.message[:100]}...")

    safe_session_id = input_data.session_id.replace("-", "_")
    print(f"[INPUT_NODE] ✓ Validation passed, safe_session_id: {safe_session_id}")

    # Return validated output
    output_data = InputNodeOutput(safe_session_id=safe_session_id)
    return output_data.model_dump()