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

load_dotenv()

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()
retriever = Retriever()
TempRetriever = TempRetriever()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# pretend DB
SESSIONS = {}  # {session_id: [BaseMessage, ...]}

def get_history(session_id: str):
    return SESSIONS.setdefault(session_id, [SystemMessage(content=MAIN_PROMPT)])

def handle_user_message(session_id: str, text: str) -> str:
    history = get_history(session_id)
    history.append(HumanMessage(content=text))
    response = llm.invoke(history)       # pass full history
    history.append(response)
    return response.content

doc_processor = DocumentProcessorTemp()
DOCUMENT_CONTEXTS = {}  # Store document contexts per session

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    data = request.json
    session_id = data["session_id"]
    msg = data["message"]
    document_url = data.get("document_url")

    print(f"Session ID: {session_id}, Message: {msg}, Document URL: {document_url} inside the /analyze route")
    
    # Process new document if provided
    if document_url and session_id not in DOCUMENT_CONTEXTS:
        print(f"Processing document for session {session_id}")
        vector_store = doc_processor.process(document_url, session_id)
        if vector_store:
            DOCUMENT_CONTEXTS[session_id] = session_id
    
    # Retrieve context from both sources
    print(f"Retrieving from documents table")
    policy_context = retriever.retrieve_chunks(msg)
    print(f"Policy Context: {policy_context} to check for the error")
    doc_context = []
    
    if session_id in DOCUMENT_CONTEXTS:
        print(f"Retrieving from temp_documents_{session_id}")
        doc_results = TempRetriever.retrieve_chunks(msg, session_id)
        doc_context = doc_results.get("chunks", [])
    
    # Combine contexts
    combined_context = f"""
    Policy Context: {str(policy_context)}
    Document Context: {str(doc_context)}
    """
    
    fullMsg = f"User Message: {msg}\nContext: {combined_context}"
    print(f"Retrieved Question: {fullMsg}")
    
    return jsonify(handle_user_message(session_id, fullMsg))
