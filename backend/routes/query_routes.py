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
load_dotenv()
import tempfile
import requests

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()
retriever = Retriever()
tempRetriever = TempRetriever()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", 
                             temperature=0,
                             google_api_key=os.getenv("GEMINI_API_KEY")
)

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
    safe_session_id = session_id.replace("-", "_")
    
    # Process new document if provided
    if document_url and session_id not in DOCUMENT_CONTEXTS:
        print("Processing new document for context")
        print(f"Document URL: {document_url}")
        resbefore = requests.get(document_url)
        res = resbefore.content
        print(f"Downloaded document size: {len(res)} bytes") 
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_file_path = tmp.name
        
        print(f"Temporary file saved at: {tmp_file_path}")

        vector_store = doc_processor.process(tmp_file_path, safe_session_id)
        os.remove(tmp_file_path)  # Clean up temp file
        if vector_store:
            DOCUMENT_CONTEXTS[session_id] = session_id
    
    # Retrieve context from both sources
    policy_context = retriever.retrieve_chunks(msg)
    doc_context = []
    
    if session_id in DOCUMENT_CONTEXTS:
        print("Retrieving from temp document context")
        doc_results = tempRetriever.retrieve_chunks(msg, safe_session_id)
        doc_context = doc_results.get("chunks", [])
    
    # Combine contexts
    combined_context = f"""
    Policy Context: {str(policy_context)}
    Document Context: {str(doc_context)}
    """
    
    fullMsg = f"User Message: {msg}\nContext: {combined_context}"
    print(f"Retrieved Question: {fullMsg}")
    
    return jsonify(handle_user_message(session_id, fullMsg))
