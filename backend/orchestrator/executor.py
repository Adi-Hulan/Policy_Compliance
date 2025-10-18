"""
Graph Execution Module

Handles asynchronous execution of LangGraph graphs and streaming of events
to the client via Server-Sent Events (SSE) using LangGraph's native streaming.
"""

import json
from typing import Dict, Any, AsyncGenerator
from .event_formatter import format_event_for_ui, serialize_payload_for_sse


async def create_async_stream_generator(graph, initial_state: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """
    Create an async generator that yields SSE events directly from LangGraph's native streaming.

    This function uses LangGraph's astream_events() method to stream events asynchronously,
    eliminating the need for threading and queues.

    Args:
        graph: Compiled LangGraph instance
        initial_state: Initial state dict for the graph

    Yields:
        SSE-formatted strings (data: {...}\n\n)
    """
    event_count = 0
    payload_count = 0

    try:
        # Use LangGraph's native async event streaming
        async for event in graph.astream_events(initial_state, version="v2"):
            event_count += 1
            event_type = event.get('event', 'unknown')
            event_name = event.get('name', 'unknown')

            # Format event for UI
            payloads = format_event_for_ui(event, initial_state)

            # Serialize and yield each payload
            for payload in payloads:
                try:
                    sse_line = serialize_payload_for_sse(payload)
                    yield sse_line
                    payload_count += 1

                except Exception as e:
                    # Fallback for serialization issues
                    raw = str(payload)[:200].replace("\n", "\\n")
                    safe_payload = {"type": "event", "raw": raw}
                    yield f"data: {json.dumps(safe_payload)}\n\n"
                    payload_count += 1

    except Exception as e:
        yield f"data: {json.dumps({'type':'error', 'category': 'content', 'error': str(e)})}\n\n"

    finally:
        # Send end signal
        yield f"data: {json.dumps({'type':'end', 'category': 'control'})}\n\n"


# Legacy function for backwards compatibility (can be removed after migration)
def create_stream_generator(graph, initial_state: Dict[str, Any]):
    """
    Legacy synchronous generator - DEPRECATED

    This function is kept for backwards compatibility but should not be used.
    Use create_async_stream_generator() instead.
    """
    raise DeprecationWarning(
        "create_stream_generator() is deprecated. "
        "Use create_async_stream_generator() for native LangGraph streaming."
    )