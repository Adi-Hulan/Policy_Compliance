from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever
from utils.prompts import MAIN_PROMPT
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()
retriever = Retriever()
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

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    
    data = request.json
    # if not data or "query" not in data or "session_id" not in data:
    #     return jsonify({"error": "Query or session_id not provided"}), 400

    session_id = data["session_id"]
    msg = data["message"]

    context = retriever.retrieve_chunks(msg)

    fullMsg = "User Message : " + msg + "Context : " + str(context)

    print(f"Retrived Question : {fullMsg}")

    return jsonify(handle_user_message(session_id, fullMsg))
