from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever
from utils.prompts import MAIN_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from utils.supabase_client import supabase
from agents.attached_document_processor import DocumentProcessorTemp
import os
from agents.chunk_retriever_temp import TempRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from orchestrator.graph import run_case1
from orchestrator.graph import run_case1, build_case1_graph
import asyncio
import threading
import queue as _queue
import json
from flask import Response
load_dotenv()
import tempfile
import requests

query_bp = Blueprint("queries", __name__)

@query_bp.route("/analyze", methods=["POST"])
def analyze():
    try:
        print("=" * 50)
        print("ROUTE ANALYZE CALLED - THIS SHOULD BE VISIBLE")
        print("=" * 50)
        print("[ROUTE] /analyze endpoint called")
        data = request.json
        print(f"[ROUTE] Request data keys: {list(data.keys())}")
        session_id = data["session_id"]
        msg = data["message"]
        document_url = data.get("document_url")
        print(f"[ROUTE] Session ID: {session_id}")
        print(f"[ROUTE] Message: {msg[:100]}...")
        if document_url:
            print(f"[ROUTE] Document URL provided: {document_url}")
            print("[ROUTE] Will process document through orchestrator")
        else:
            print("[ROUTE] No document URL provided")
            print("[ROUTE] Will use policy context only")
        
        print("[ROUTE] Calling unified orchestrator...")
        # Unified graph handles both cases based on presence of document_url
        result = run_case1(session_id=session_id, message=msg, document_url=document_url)
        print(f"[ROUTE] unified run_case1 returned type: {type(result)}")
        print(f"[ROUTE] Result length: {len(result) if isinstance(result, str) else 'N/A'}")
        print(f"[ROUTE] Result preview: {repr(result[:100]) if isinstance(result, str) else repr(result)}")
        
        # Ensure we return just a string like the old analyzeold route
        if isinstance(result, str):
            response_content = result
        else:
            # Fallback: extract content from object if needed
            response_content = str(result.get('content', result) if hasattr(result, 'get') else str(result))
        
        print(f"[ROUTE] Final response type: {type(response_content)}")
        print("[ROUTE] Returning string result directly (same as analyzeold)")
        return jsonify(response_content)
        
    except Exception as e:
        print(f"[ROUTE] ERROR: {str(e)}")
        print(f"[ROUTE] ERROR TYPE: {type(e)}")
        import traceback
        print(f"[ROUTE] TRACEBACK: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@query_bp.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    """Stream events from the orchestrator graph as Server-Sent Events (SSE).

    This preserves the logic of the existing `/analyze` route but exposes
    intermediate events emitted by the graph's `astream_events` API so the
    client can render streaming updates.
    """
    try:
        data = request.json
        session_id = data["session_id"]
        msg = data["message"]
        document_url = data.get("document_url")

        # Queue for passing SSE lines from the async producer to the Flask generator
        q: _queue.Queue = _queue.Queue()

        def _truncate(text, limit=140):
            if text is None:
                return ""
            text = str(text)
            return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

        def _safe_session(value: str) -> str:
            return (value or "").replace("-", "_")

        def _extract_text(blob):
            if blob is None:
                return ""
            if isinstance(blob, str):
                return blob
            if isinstance(blob, dict):
                for key in ("content", "text", "response"):
                    if key in blob:
                        return _extract_text(blob[key])
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

        def _extract_count(value):
            if isinstance(value, (list, tuple, set, dict)):
                return len(value)
            return None

        def _build_stage_payload(node: str, message: str, **extra):
            payload = {"type": "stage", "node": node, "message": message}
            if extra:
                payload.update({k: v for k, v in extra.items() if v is not None})
            return payload

        def _extract_token(data_section):
            if not isinstance(data_section, dict):
                return ""
            chunk = data_section.get("chunk") or data_section.get("delta")
            if chunk is None:
                return ""
            if isinstance(chunk, str):
                return chunk
            if isinstance(chunk, dict):
                content = chunk.get("content")
                if isinstance(content, list):
                    return "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                if isinstance(content, str):
                    return content
                if "text" in chunk:
                    return str(chunk["text"])
            if hasattr(chunk, "content"):
                return _extract_text(chunk.content)
            if hasattr(chunk, "text"):
                return str(chunk.text)
            return _extract_text(chunk)

        def _maybe_get_state(data_section: dict):
            if not isinstance(data_section, dict):
                return {}
            for key in ("state", "new_state", "updated_state"):
                state = data_section.get(key)
                if isinstance(state, dict):
                    return state
            return {}

        async def async_producer(initial_state: dict):
            # Run the compiled graph's async event stream and push serialised
            # SSE payloads into the queue as they arrive.
            try:
                graph = build_case1_graph()
                # astream_events is an async generator of event dicts
                events = graph.astream_events(initial_state, version="v2")

                async for event in events:
                    payloads = []
                    try:
                        node_name = (event.get("name") or "").lower()
                        ev_type = event.get("event")
                        data_section = event.get("data") or {}
                        state_snapshot = _maybe_get_state(data_section)
                        output_section = data_section.get("output") if isinstance(data_section, dict) else None

                        if ev_type == "on_chat_model_stream":
                            token = _extract_token(data_section)
                            if token:
                                payloads.append({"type": "llm_stream", "node": node_name, "content": token})

                        elif ev_type == "on_chat_model_end":
                            final_text = _extract_text(output_section or data_section)
                            if final_text:
                                payloads.append({"type": "llm_final", "node": node_name, "content": final_text})

                        elif node_name in ("input", "input_node"):
                            if ev_type == "on_chain_start":
                                payloads.append(
                                    _build_stage_payload(
                                        "input",
                                        "Validating session & user input…",
                                        session=_safe_session(initial_state.get("session_id")),
                                        user_message=_truncate(initial_state.get("message"), 120),
                                    )
                                )
                            elif ev_type == "on_chain_end":
                                safe_id = None
                                if isinstance(output_section, dict):
                                    safe_id = output_section.get("safe_session_id")
                                if not safe_id:
                                    safe_id = _safe_session(initial_state.get("session_id"))
                                payloads.append(
                                    _build_stage_payload(
                                        "input",
                                        "Session validated",
                                        session=safe_id,
                                    )
                                )

                        elif node_name in ("history", "session_history_node") and ev_type == "on_chain_end":
                            history = None
                            if isinstance(output_section, dict):
                                history = output_section.get("history")
                            if history is None and state_snapshot:
                                history = state_snapshot.get("history")
                            count = _extract_count(history) or 0
                            payloads.append(
                                _build_stage_payload(
                                    "history",
                                    f"Fetched {count} messages from history",
                                    count=count,
                                )
                            )

                        elif node_name in ("doc_download", "document_download_node"):
                            if ev_type == "on_chain_start":
                                url = initial_state.get("document_url") or state_snapshot.get("document_url")
                                if url:
                                    payloads.append(
                                        _build_stage_payload(
                                            "doc_download",
                                            f"Downloading document from URL {_truncate(url, 100)}",
                                        )
                                    )
                            elif ev_type == "on_chain_end":
                                tmp_path = None
                                if isinstance(output_section, dict):
                                    tmp_path = output_section.get("tmp_file_path")
                                if not tmp_path and state_snapshot:
                                    tmp_path = state_snapshot.get("tmp_file_path")
                                size_bytes = None
                                if tmp_path and os.path.exists(tmp_path):
                                    try:
                                        size_bytes = os.path.getsize(tmp_path)
                                    except OSError:
                                        size_bytes = None
                                payloads.append(
                                    _build_stage_payload(
                                        "doc_download",
                                        "Document downloaded",
                                        bytes=size_bytes,
                                        temp_path=_truncate(tmp_path, 80) if tmp_path else None,
                                    )
                                )

                        elif node_name in ("doc_process", "document_processing_node"):
                            if ev_type == "on_chain_start":
                                payloads.append(
                                    _build_stage_payload(
                                        "doc_process",
                                        "Processing downloaded document…",
                                    )
                                )
                            elif ev_type == "on_chain_end":
                                payloads.append(
                                    _build_stage_payload(
                                        "doc_process",
                                        "Document chunks prepared for retrieval",
                                    )
                                )

                        elif node_name in ("policy_retriever", "policy_retriever_node") and ev_type == "on_chain_end":
                            policy_chunks = None
                            if isinstance(output_section, dict):
                                policy_chunks = output_section.get("policy_context")
                            if policy_chunks is None and state_snapshot:
                                policy_chunks = state_snapshot.get("policy_context")
                            count = _extract_count(policy_chunks) or 0
                            payloads.append(
                                _build_stage_payload(
                                    "policy_retriever",
                                    f"Retrieved {count} policy chunks",
                                    count=count,
                                    sample=_truncate(policy_chunks[0] if count else "", 160)
                                    if isinstance(policy_chunks, list)
                                    else None,
                                )
                            )

                        elif node_name in ("doc_retriever", "document_retriever_node") and ev_type == "on_chain_end":
                            doc_chunks = None
                            if isinstance(output_section, dict):
                                doc_chunks = output_section.get("doc_context")
                            if doc_chunks is None and state_snapshot:
                                doc_chunks = state_snapshot.get("doc_context")
                            count = _extract_count(doc_chunks) or 0
                            payloads.append(
                                _build_stage_payload(
                                    "doc_retriever",
                                    f"Retrieved {count} document chunks",
                                    count=count,
                                    sample=_truncate(doc_chunks[0] if count else "", 160)
                                    if isinstance(doc_chunks, list)
                                    else None,
                                )
                            )

                        elif node_name in ("context_combine", "context_combination_node") and ev_type == "on_chain_end":
                            full_message = None
                            if isinstance(output_section, dict):
                                full_message = output_section.get("full_user_message")
                            if not full_message and state_snapshot:
                                full_message = state_snapshot.get("full_user_message")
                            payloads.append(
                                _build_stage_payload(
                                    "context_combine",
                                    "Combining policy and document context",
                                    preview=_truncate(full_message, 200) if full_message else None,
                                )
                            )

                        elif node_name in ("llm", "llm_node") and ev_type == "on_chain_start":
                            payloads.append(
                                _build_stage_payload(
                                    "llm",
                                    "Generating response with LLM…",
                                )
                            )

                        elif node_name in ("session_update", "session_update_node") and ev_type == "on_chain_end":
                            payloads.append(
                                _build_stage_payload(
                                    "session_update",
                                    "Appending messages to session history",
                                )
                            )

                        elif node_name in ("output", "output_node") and ev_type == "on_chain_end":
                            final_text = ""
                            if isinstance(output_section, dict):
                                final_text = _extract_text(output_section.get("content") or output_section)
                                if not final_text:
                                    final_text = output_section.get("response", "")
                            if not final_text:
                                final_text = _extract_text(data_section)
                            payloads.append({"type": "final", "node": node_name, "content": final_text})

                        elif ev_type in ("on_chain_start", "on_chain_end") and node_name:
                            # Fallback generic progress event
                            verb = "Starting" if ev_type == "on_chain_start" else "Finished"
                            payloads.append(
                                _build_stage_payload(
                                    node_name,
                                    f"{verb} node '{node_name}'",
                                )
                            )

                    except Exception as e:
                        payloads = [{"type": "error", "error": str(e)}]

                    for payload in payloads:
                        try:
                            q.put(f"data: {json.dumps(payload)}\n\n")
                        except Exception:
                            raw = str(payload)[:200].replace("\n", "\\n")
                            safe_payload = {"type": "event", "raw": raw}
                            q.put(f"data: {json.dumps(safe_payload)}\n\n")

            except Exception as e:
                q.put(f"data: {json.dumps({'type':'error','error': str(e)})}\n\n")
            finally:
                try:
                    q.put(f"data: {json.dumps({'type':'end'})}\n\n")
                except Exception:
                    q.put("data: {\"type\": \"end\"}\n\n")
                q.put(None)

        def start_background_loop(initial_state: dict):
            # Thread target that runs the async producer
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(async_producer(initial_state))
            loop.close()

        def stream_generator():
            initial_state = {"session_id": session_id, "message": msg, "document_url": document_url}

            # Start background thread that will populate the queue
            t = threading.Thread(target=start_background_loop, args=(initial_state,))
            t.start()

            # Yield items as they arrive from the async producer
            while True:
                item = q.get()
                if item is None:
                    break
                yield item

        # Return a Flask Response streaming SSE
        return Response(stream_generator(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({"error": str(e)}), 500
