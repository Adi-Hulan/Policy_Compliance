from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()
retriever = Retriever()

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query not provided"}), 400

    result = retriever.retrieve_chunks(data["query"])
    return jsonify(result)
