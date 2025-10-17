"""
Event Formatting Module

Converts raw LangGraph events into UI-friendly payloads for SSE streaming.
Uses a unified payload structure for consistency and simpler frontend integration.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional


# --- Utility Functions ---
def _truncate(text: Any, limit: int = 140) -> str:
    """Truncate text to a specified limit with ellipsis."""
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _safe_session(value: str) -> str:
    """Convert session ID to safe format (replace hyphens with underscores)."""
    return (value or "").replace("-", "_")


def _extract_text(blob: Any) -> str:
    """
    Extract text content from various data structures.
    Handles strings, dicts, lists, and objects with content attributes.
    """
    if blob is None:
        return ""
    if isinstance(blob, str):
        return blob
    if isinstance(blob, dict):
        # Try common content keys
        for key in ("content", "text", "response"):
            if key in blob:
                return _extract_text(blob[key])
        # Concatenate all values
        parts = []
        for val in blob.values():
            chunk = _extract_text(val)
            if chunk:
                parts.append(chunk)
        return "".join(parts)
    if isinstance(blob, (list, tuple)):
        return "".join(_extract_text(part) for part in blob)
    if hasattr(blob, "content"):
        return _extract_text(getattr(blob, "content"))
    return str(blob)


def _extract_count(value: Any) -> Optional[int]:
    """Extract count from collections (list, tuple, set, dict)."""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    return None


def _extract_token(data_section: Any) -> str:
    """
    Extract streaming token from LLM data section.
    Handles various response formats from different LLM providers.
    Removes citation markers for clean streaming display.
    """
    if isinstance(data_section, dict):
        # Get chunk or delta
        chunk = data_section.get("chunk") or data_section.get("delta")
        if chunk is None:
            print(f"[TOKEN_EXTRACT] ✗ No chunk/delta in data_section: {list(data_section.keys())}", flush=True)
            return ""

    # Handle string chunks
    if isinstance(chunk, str):
        # Remove citation markers for clean streaming
        clean_chunk = re.sub(r'\[SOURCE:[^\]]+\]', '', chunk)
        print(f"[TOKEN_EXTRACT] ✓ String chunk: '{chunk}' -> clean: '{clean_chunk}'")
        return clean_chunk

    # Handle dict chunks
    if isinstance(chunk, dict):
        content = chunk.get("content")

        # Handle list content (multi-part)
        if isinstance(content, list):
            token = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
            # Remove citation markers
            clean_token = re.sub(r'\[SOURCE:[^\]]+\]', '', token)
            print(f"[TOKEN_EXTRACT] ✓ List content chunk: '{token}' -> clean: '{clean_token}'")
            return clean_token

        # Handle string content
        if isinstance(content, str):
            # Remove citation markers
            clean_content = re.sub(r'\[SOURCE:[^\]]+\]', '', content)
            print(f"[TOKEN_EXTRACT] ✓ String content chunk: '{content}' -> clean: '{clean_content}'")
            return clean_content

        # Handle text field
        if "text" in chunk:
            token = str(chunk["text"])
            # Remove citation markers
            clean_token = re.sub(r'\[SOURCE:[^\]]+\]', '', token)
            print(f"[TOKEN_EXTRACT] ✓ Text field chunk: '{token}' -> clean: '{clean_token}'")
            return clean_token

    # Handle objects with content/text attributes
    if hasattr(chunk, "content"):
        token = _extract_text(chunk.content)
        # Remove citation markers
        clean_token = re.sub(r'\[SOURCE:[^\]]+\]', '', token)
        print(f"[TOKEN_EXTRACT] ✓ Object content: '{token}' -> clean: '{clean_token}'")
        return clean_token
    if hasattr(chunk, "text"):
        token = str(chunk.text)
        # Remove citation markers
        clean_token = re.sub(r'\[SOURCE:[^\]]+\]', '', token)
        print(f"[TOKEN_EXTRACT] ✓ Object text: '{token}' -> clean: '{clean_token}'")
        return clean_token

    token = _extract_text(chunk)
    # Remove citation markers
    clean_token = re.sub(r'\[SOURCE:[^\]]+\]', '', token)
    print(f"[TOKEN_EXTRACT] ✓ Fallback extraction: '{token}' -> clean: '{clean_token}'")
    return clean_token


def _maybe_get_state(data_section: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract state dict from data section.
    Tries common state keys.
    """
    if not isinstance(data_section, dict):
        return {}

    for key in ("state", "new_state", "updated_state"):
        state = data_section.get(key)
        if isinstance(state, dict):
            return state

    return {}


# --- Data Extraction Layer ---
def extract_event_data(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract basic data from LangGraph events.
    Returns normalized data structure for UI mapping.

    Args:
        event: Raw event dict from LangGraph.astream_events()

    Returns:
        Dict with normalized event data or None if unhandled
    """
    ev_type = event.get("event")
    node_name = (event.get("name") or "").lower()
    data_section = event.get("data") or {}

    # LLM streaming events
    if ev_type == "on_chat_model_stream":
        token = _extract_token(data_section)
        if token:
            print(f"[EVENT_EXTRACT] ✓ LLM STREAM: node={node_name}, token='{token}'", flush=True)
            return {
                "event_type": "llm_stream",
                "node": node_name,
                "token": token
            }
        else:
            print(f"[EVENT_EXTRACT] ✗ LLM STREAM: no token extracted from {data_section}", flush=True)

    elif ev_type == "on_chat_model_end":
        final_text = _extract_text(data_section.get("output") or data_section)
        if final_text:
            print(f"[EVENT_EXTRACT] ✓ LLM END: node={node_name}, content_length={len(final_text)}")
            return {
                "event_type": "llm_final",
                "node": node_name,
                "content": final_text
            }

    # Chain lifecycle events
    elif ev_type in ("on_chain_start", "on_chain_end"):
        output_section = data_section.get("output") if isinstance(data_section, dict) else None
        state_snapshot = _maybe_get_state(data_section)

        return {
            "event_type": "chain_lifecycle",
            "lifecycle_type": ev_type,
            "node": node_name,
            "output": output_section,
            "state": state_snapshot,
            "raw_data": data_section
        }

    return None


# --- UI Message Mapping Layer ---
UI_MESSAGES = {
    "input": {
        "start": "Validating session & user input…",
        "end": "Session validated"
    },
    "history": {
        "end": "Fetched {count} messages from history"
    },
    "doc_download": {
        "start": "Downloading document from {url}",
        "end": "Document downloaded"
    },
    "doc_process": {
        "start": "Processing downloaded document…",
        "end": "Document chunks prepared for retrieval"
    },
    "policy_retriever": {
        "end": "Retrieved {count} policy chunks"
    },
    "doc_retriever": {
        "end": "Retrieved {count} document chunks"
    },
    "context_combine": {
        "end": "Combining policy and document context"
    },
    "llm": {
        "start": "Generating response with LLM…",
    },
    "session_update": {
        "end": "Appending messages to session history"
    },
    "output": {
        "end": "Response ready"
    }
}

# Map node names to UI message keys
NODE_TO_UI_KEY = {
    "input": "input",
    "input_node": "input",
    "history": "history", 
    "session_history_node": "history",
    "doc_download": "doc_download",
    "document_download_node": "doc_download",
    "doc_process": "doc_process",
    "document_processing_node": "doc_process",
    "policy_retriever": "policy_retriever",
    "policy_retriever_node": "policy_retriever",
    "doc_retriever": "doc_retriever",
    "document_retriever_node": "doc_retriever",
    "context_combine": "context_combine",
    "context_combination_node": "context_combine",
    "llm": "llm",
    "llm_node": "llm",
    "session_update": "session_update",
    "session_update_node": "session_update",
    "output": "output",
    "output_node": "output"
}


def map_to_ui_payload(extracted_data: Dict[str, Any], initial_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Map extracted event data to UI-friendly payloads.
    Maintains exact same output format as original formatter.

    Args:
        extracted_data: Normalized data from extract_event_data()
        initial_state: Initial state used for the graph execution

    Returns:
        List of UI payloads compatible with frontend
    """
    payloads = []
    event_type = extracted_data["event_type"]
    node = extracted_data["node"]
    
    # Get UI message key (handles node name variants)
    ui_key = NODE_TO_UI_KEY.get(node, node)

    # LLM streaming
    if event_type == "llm_stream":
        token = extracted_data["token"]
        payload = {
            "type": "llm_stream",
            "category": "content",
            "content": token,
            "message": "Generating response..."
        }
        print(f"[UI_PAYLOAD] ✓ LLM STREAM payload: '{token}'")
        payloads.append(payload)

    elif event_type == "llm_final":
        content = extracted_data["content"]
        payload = {
            "type": "llm_final",
            "category": "content",
            "content": content,
            "message": "Response complete"
        }
        print(f"[UI_PAYLOAD] ✓ LLM FINAL payload: length={len(content)}")
        payloads.append(payload)

    # Chain lifecycle events
    elif event_type == "chain_lifecycle":
        lifecycle_type = extracted_data["lifecycle_type"]
        output = extracted_data["output"]
        state = extracted_data["state"]
        raw_data = extracted_data["raw_data"]

        # Get UI message template
        node_messages = UI_MESSAGES.get(ui_key, {})
        is_start = lifecycle_type == "on_chain_start"
        message_key = "start" if is_start else "end"
        template = node_messages.get(message_key)

        if template:
            # Format message with dynamic data
            message = template

            # Input node special handling
            if ui_key == "input":
                if is_start:
                    session = _safe_session(initial_state.get("session_id"))
                    user_msg = _truncate(initial_state.get("message"), 120)
                    payloads.append({
                        "type": "stage",
                        "category": "status",
                        "node": "input",
                        "message": message
                    })
                else:
                    payloads.append({
                        "type": "stage",
                        "category": "status",
                        "node": "input",
                        "message": message
                    })

            # History node
            elif ui_key == "history" and not is_start:
                history = output.get("history") if isinstance(output, dict) else None
                if history is None:
                    history = state.get("history")
                count = _extract_count(history) or 0
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": "history",
                    "message": message.format(count=count)
                })

            # Document download node
            elif ui_key == "doc_download":
                if is_start:
                    url = initial_state.get("document_url") or state.get("document_url")
                    if url:
                        payloads.append({
                            "type": "stage",
                            "category": "status",
                            "node": "doc_download",
                            "message": message.format(url=_truncate(url, 100))
                        })
                else:
                    payloads.append({
                        "type": "stage",
                        "category": "status",
                        "node": "doc_download",
                        "message": message
                    })

            # Document processing node
            elif ui_key == "doc_process":
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": "doc_process",
                    "message": message
                })

            # Retriever nodes
            elif ui_key in ("policy_retriever", "doc_retriever") and not is_start:
                context_key = "policy_context" if ui_key == "policy_retriever" else "doc_context"
                chunks = output.get(context_key) if isinstance(output, dict) else None
                if chunks is None:
                    chunks = state.get(context_key)

                count = _extract_count(chunks) or 0
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": ui_key,
                    "message": message.format(count=count)
                })

            # Context combination node
            elif ui_key == "context_combine" and not is_start:
                full_message = output.get("full_user_message") if isinstance(output, dict) else None
                if not full_message:
                    full_message = state.get("full_user_message")

                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": "context_combine",
                    "message": message
                })

            # LLM node
            elif ui_key == "llm" and is_start:
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": "llm",
                    "message": message
                })

            # Session update node
            elif ui_key == "session_update" and not is_start:
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": "session_update",
                    "message": message
                })

            # Output node
            elif ui_key == "output" and not is_start:
                final_text = ""
                citations = []
                chunk_metadata = []

                if isinstance(output, dict):
                    final_text = _extract_text(output.get("content") or output)
                    if not final_text:
                        final_text = output.get("response", "")
                    # Extract citations and chunk metadata
                    citations = output.get("citations", [])
                    chunk_metadata = output.get("chunk_metadata", [])

                if not final_text:
                    final_text = _extract_text(raw_data)

                payload = {
                    "type": "final",
                    "category": "content",
                    "node": node,
                    "content": final_text,
                    "citations": citations,
                    "chunk_metadata": chunk_metadata
                }

                print(f"[UI_PAYLOAD] ✓ FINAL payload: content_length={len(final_text)}, citations={len(citations)}")
                payloads.append(payload)

            # Generic fallback for other nodes
            else:
                verb = "Starting" if is_start else "Finished"
                payloads.append({
                    "type": "stage",
                    "category": "status",
                    "node": node,
                    "message": f"{verb} node '{node}'"
                })

    return payloads


# --- Main Formatting Function (Backwards Compatible) ---
def format_event_for_ui(event: Dict[str, Any], initial_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a raw LangGraph event into UI-friendly payloads.

    Args:
        event: Raw event dict from LangGraph.astream_events()
        initial_state: Initial state used for the graph execution

    Returns:
        List of UI payloads to send to the client
    """
    try:
        # Extract data using separated logic
        extracted_data = extract_event_data(event)
        if extracted_data:
            return map_to_ui_payload(extracted_data, initial_state)
        return []

    except Exception as e:
        print(f"[EVENT_FORMATTER] ✗ Error processing event: {e}")
        import traceback
        traceback.print_exc()
        return [{"type": "error", "category": "content", "error": str(e)}]


def serialize_payload_for_sse(payload: Dict[str, Any]) -> str:
    """
    Serialize a payload dict for Server-Sent Events format.

    Args:
        payload: Payload dict to serialize

    Returns:
        SSE-formatted string: "data: {...}\n\n"
    """
    try:
        sse_line = f"data: {json.dumps(payload)}\n\n"
        return sse_line
    except Exception as e:
        print(f"[SERIALIZER] ✗ Serialization error: {e}")
        # Fallback for serialization issues
        raw = str(payload)[:200].replace("\n", "\\n")
        safe_payload = {"type": "event", "raw": raw}
        return f"data: {json.dumps(safe_payload)}\n\n"