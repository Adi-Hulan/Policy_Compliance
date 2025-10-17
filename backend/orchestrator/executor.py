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
    print(f"[ASYNC_STREAM_GENERATOR] Creating async stream generator")
    print(f"[ASYNC_STREAM_GENERATOR] Session: {initial_state.get('session_id')}")
    print(f"[ASYNC_STREAM_GENERATOR] Message: {initial_state.get('message', '')[:100]}...")
    print(f"[ASYNC_STREAM_GENERATOR] Intent: {initial_state.get('intent')}")

    event_count = 0
    payload_count = 0

    try:
        # Use LangGraph's native async event streaming
        async for event in graph.astream_events(initial_state, version="v2"):
            event_count += 1
            event_type = event.get('event', 'unknown')
            event_name = event.get('name', 'unknown')

            print(f"[ASYNC_STREAM_GENERATOR] Event #{event_count}: {event_type} from {event_name}")

            # Format event for UI
            payloads = format_event_for_ui(event, initial_state)
            print(f"[ASYNC_STREAM_GENERATOR] → Generated {len(payloads)} UI payloads")

            # Serialize and yield each payload
            for payload in payloads:
                print(f"[ASYNC_STREAM_GENERATOR] → Yielding payload: {payload}")
                try:
                    sse_line = serialize_payload_for_sse(payload)
                    print(f"[ASYNC_STREAM_GENERATOR] → SSE line: {sse_line[:100]}...")
                    yield sse_line
                    payload_count += 1

                except Exception as e:
                    print(f"[ASYNC_STREAM_GENERATOR] ⚠ Serialization error: {e}")
                    # Fallback for serialization issues
                    raw = str(payload)[:200].replace("\n", "\\n")
                    safe_payload = {"type": "event", "raw": raw}
                    yield f"data: {json.dumps(safe_payload)}\n\n"
                    payload_count += 1

        print(f"[ASYNC_STREAM_GENERATOR] ✓ Completed")
        print(f"[ASYNC_STREAM_GENERATOR] Total events: {event_count}")
        print(f"[ASYNC_STREAM_GENERATOR] Total payloads: {payload_count}")

    except Exception as e:
        print(f"[ASYNC_STREAM_GENERATOR] ✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type':'error', 'category': 'content', 'error': str(e)})}\n\n"

    finally:
        # Send end signal
        print(f"[ASYNC_STREAM_GENERATOR] Sending end signal")
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