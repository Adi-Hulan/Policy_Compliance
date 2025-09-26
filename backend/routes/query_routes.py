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
from backend.orchestrator.graph import run_case1
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
