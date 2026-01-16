"""
Context Combination Node

Combines policy and document context into a single prompt.
Specific to company policy graph.
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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
            history=state.history or [],
            policy_chunks_with_metadata=getattr(state, 'policy_chunks_with_metadata', []) or [],
            doc_chunks_with_metadata=getattr(state, 'doc_chunks_with_metadata', []) or []
        )
    except Exception as e:
        raise ValueError(f"Context combination input validation failed: {e}")

    policy_context = input_data.policy_context
    doc_context = input_data.doc_context
    chat_history = input_data.history
    policy_chunks_with_metadata = input_data.policy_chunks_with_metadata
    doc_chunks_with_metadata = input_data.doc_chunks_with_metadata

    print(f"[CONTEXT_COMBINATION_NODE] Combining {len(policy_context)} policy chunks, {len(doc_context)} doc chunks with {len(chat_history)} history items")
    print(f"[CONTEXT_COMBINATION_NODE] Policy chunks with metadata: {len(policy_chunks_with_metadata)}, Doc chunks with metadata: {len(doc_chunks_with_metadata)}")

    try:
        # Track chunk metadata for clickable links
        chunk_metadata = []

        # Format policy context
        policy_parts = []
        for i, chunk in enumerate(policy_context):
            if chunk:
                chunk_id = f"policy_chunk_{i+1}"
                
                # Check if we have citation metadata for this chunk
                citation_info = ""
                if i < len(policy_chunks_with_metadata) and policy_chunks_with_metadata[i].get('citation'):
                    citation = policy_chunks_with_metadata[i]['citation']
                    citation_info = f" [Page {citation.get('page', 'N/A')}, chars {citation.get('char_start', 0)}-{citation.get('char_end', 0)}]"
                
                policy_parts.append(f"🏢 COMPANY POLICY - Chunk {i+1} (ID: {chunk_id}){citation_info}:\n{chunk}\n")

                # Store metadata for UI links with citation info
                metadata_entry = {
                    "id": chunk_id,
                    "type": "policy",
                    "index": i+1,
                    "content": chunk,
                    "source": "Company Policy Database"
                }
                
                # Add citation metadata if available
                if i < len(policy_chunks_with_metadata):
                    chunk_meta = policy_chunks_with_metadata[i]
                    if chunk_meta.get('citation'):
                        metadata_entry["citation"] = chunk_meta['citation']
                    if chunk_meta.get('id'):
                        metadata_entry["chunk_db_id"] = chunk_meta['id']
                
                chunk_metadata.append(metadata_entry)

        # Format document context
        doc_parts = []
        for i, chunk in enumerate(doc_context):
            if chunk:
                chunk_id = f"document_chunk_{i+1}"
                
                # Check if we have citation metadata for this chunk
                citation_info = ""
                if i < len(doc_chunks_with_metadata) and doc_chunks_with_metadata[i].get('citation'):
                    citation = doc_chunks_with_metadata[i]['citation']
                    citation_info = f" [Page {citation.get('page', 'N/A')}, chars {citation.get('char_start', 0)}-{citation.get('char_end', 0)}]"
                
                doc_parts.append(f"📄 ATTACHED DOCUMENT - Chunk {i+1} (ID: {chunk_id}){citation_info}:\n{chunk}\n")

                # Store metadata for UI links with citation info
                metadata_entry = {
                    "id": chunk_id,
                    "type": "document",
                    "index": i+1,
                    "content": chunk,
                    "source": state.tmp_file_path or "Uploaded Document"
                }
                
                # Add citation metadata if available
                if i < len(doc_chunks_with_metadata):
                    chunk_meta = doc_chunks_with_metadata[i]
                    if chunk_meta.get('citation'):
                        metadata_entry["citation"] = chunk_meta['citation']
                    if chunk_meta.get('id'):
                        metadata_entry["chunk_db_id"] = chunk_meta['id']
                
                chunk_metadata.append(metadata_entry)

        # Format chat history
        history_parts = []
        for msg in chat_history[-5:]:  # Last 5 messages
            role = None
            content = None
            # Prefer LangChain message classes when available
            if isinstance(msg, HumanMessage):
                role = 'user'
                content = msg.content
            elif isinstance(msg, AIMessage):
                role = 'assistant'
                content = msg.content
            elif isinstance(msg, SystemMessage):
                role = 'system'
                content = msg.content
            else:
                # Dict-like fallback
                try:
                    role = msg.get("role", None)
                    content = msg.get("content", None)
                except Exception:
                    # Generic object fallback
                    role = getattr(msg, 'type', None) or getattr(msg, 'role', None)
                    content = getattr(msg, 'content', None)

            if role and content:
                history_parts.append(f"{role.title()}: {content}")

        # Decide whether to force preference for attached document
        preference_instruction = ""
        try:
            # If any attached document chunks exist for this session, prefer them.
            # If the user's message explicitly references the document, force strict adherence.
            lower_msg = (input_data.message or "").lower()
            doc_indicators = ["this document", "uploaded", "attached", "the document", "pdf", "file"]
            if len(doc_parts) > 0:
                # Default preference when docs exist
                preference_instruction = (
                    "NOTE: This session has an uploaded/attached document. "
                    "Prefer answering from the 'ATTACHED DOCUMENT' section below."
                )
                # If user explicitly references the document, make instruction stronger
                if any(ind in lower_msg for ind in doc_indicators):
                    preference_instruction = (
                        "IMPORTANT: The user asked specifically about an uploaded/attached document. "
                        "Answer using ONLY the 'ATTACHED DOCUMENT' section below. Do NOT use COMPANY POLICY or other sources unless the user explicitly asks for cross-references."
                    )
                    print("[CONTEXT_COMBINATION_NODE] Enforcing attached-document-first instruction (strict)")
                else:
                    print("[CONTEXT_COMBINATION_NODE] Enforcing attached-document-first instruction (prefer docs)")
        except Exception:
            preference_instruction = ""

        # Combine everything
        combined_context = "\n\n".join([
            f"USER QUESTION: {input_data.message}",
            "",
            preference_instruction,
            "",
            "=== 🏢 COMPANY POLICY CONTEXT (from internal database) ===",
            "\n".join(policy_parts),
            "",
            "=== 📄 ATTACHED DOCUMENT CONTEXT (from uploaded file) ===",
            "\n".join(doc_parts),
            "",
            "=== 💬 CONVERSATION HISTORY ===",
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