"""
Context Combination Node

Combines policy and document context into a single prompt.
Specific to company policy graph.
"""

from typing import Dict, Any, List
from graphs.nodes.models import ContextCombinationNodeInput, ContextCombinationNodeOutput


def context_combination_node(state) -> Dict[str, Any]:
    """
    Combine retrieved chunks with conversation history.

    Args:
        state: Current graph state

    Returns:
        Dict with combined_context (formatted context string) and chunk_metadata

    Streams:
        - context_combination_start: Context combination initiated
        - context_combination_progress: Context combination progress updates
        - context_combination_complete: Context combination finished
    """
    # Validate inputs using Pydantic model
    try:
        input_data = ContextCombinationNodeInput(
            message=state.message,
            policy_context=state.policy_context or [],
            doc_context=state.doc_context or [],
            history=state.history or []
        )
    except Exception as e:
        raise ValueError(f"Context combination input validation failed: {e}")

    policy_context = input_data.policy_context
    doc_context = input_data.doc_context
    chat_history = input_data.history

    print(f"[CONTEXT_COMBINATION_NODE] Combining {len(policy_context)} policy chunks, {len(doc_context)} doc chunks with {len(chat_history)} history items")

    try:
        # Track chunk metadata for clickable links
        chunk_metadata = []

        # Format policy context
        policy_parts = []
        for i, chunk in enumerate(policy_context):
            if chunk:
                chunk_id = f"policy_chunk_{i+1}"
                policy_parts.append(f"Policy Chunk {i+1} (ID: {chunk_id}):\n{chunk}\n")

                # Store metadata for UI links
                chunk_metadata.append({
                    "id": chunk_id,
                    "type": "policy",
                    "index": i+1,
                    "content": chunk,
                    "source": "Company Policy Database"
                })

        # Format document context
        doc_parts = []
        for i, chunk in enumerate(doc_context):
            if chunk:
                chunk_id = f"document_chunk_{i+1}"
                doc_parts.append(f"Document Chunk {i+1} (ID: {chunk_id}):\n{chunk}\n")

                # Store metadata for UI links
                chunk_metadata.append({
                    "id": chunk_id,
                    "type": "document",
                    "index": i+1,
                    "content": chunk,
                    "source": state.tmp_file_path or "Uploaded Document"
                })

        # Format chat history
        history_parts = []
        for msg in chat_history[-5:]:  # Last 5 messages
            if hasattr(msg, 'type'):  # LangChain message
                role = msg.type
                content = msg.content
            else:  # Dict format
                role = msg.get("role", "")
                content = msg.get("content", "")
            if role and content:
                history_parts.append(f"{role.title()}: {content}")

        # Combine everything
        combined_context = "\n\n".join([
            f"USER QUESTION: {input_data.message}",
            "",
            "RETRIEVED POLICY CONTEXT:",
            "\n".join(policy_parts),
            "RETRIEVED DOCUMENT CONTEXT:",
            "\n".join(doc_parts),
            "CONVERSATION HISTORY:",
            "\n".join(history_parts)
        ])

        print(f"[CONTEXT_COMBINATION_NODE] ✓ Combined context length: {len(combined_context)}")
        print(f"[CONTEXT_COMBINATION_NODE] ✓ Tracked {len(chunk_metadata)} chunks with metadata")

        # Return validated output with metadata
        output_data = ContextCombinationNodeOutput(
            full_user_message=combined_context,
            chunk_metadata=chunk_metadata
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[CONTEXT_COMBINATION_NODE] ✗ Context combination failed: {e}")
        return {}