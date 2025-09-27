from flask import Blueprint, request, jsonify, Response
from orchestrator.graph import build_case1_graph
from orchestrator.executor import create_stream_generator
from dotenv import load_dotenv

load_dotenv()

query_bp = Blueprint("queries", __name__)


@query_bp.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    """Stream events from the orchestrator graph as Server-Sent Events (SSE).

    This preserves the logic of the existing `/analyze` route but exposes
    intermediate events emitted by the graph's `astream_events` API so the
    client can render streaming updates.
    """
    print("=" * 80)
    print("[ROUTE] /analyze/stream endpoint called")
    print("=" * 80)
    
    try:
        data = request.json
        session_id = data["session_id"]
        msg = data["message"]
        document_url = data.get("document_url")

        print(f"[ROUTE] Parsed request - Session: {session_id}, Message: {msg[:100]}...")
        if document_url:
            print(f"[ROUTE] Document URL provided: {document_url}")

        # Build the graph and create initial state
        print(f"[ROUTE] Building case1 graph...")
        graph = build_case1_graph()
        initial_state = {"session_id": session_id, "message": msg, "document_url": document_url}
        print(f"[ROUTE] Created initial state with keys: {list(initial_state.keys())}")

        # Create the stream generator using the new executor module
        print(f"[ROUTE] Creating stream generator...")
        stream_generator = create_stream_generator(graph, initial_state)
        print(f"[ROUTE] Stream generator created, returning SSE response")

        # Return a Flask Response streaming SSE
        return Response(stream_generator, mimetype='text/event-stream')

    except Exception as e:
        print(f"[ROUTE] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
