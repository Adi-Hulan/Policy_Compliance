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

    # Step 1: Analyze the query
    analysis_result = analyzer.process(data["query"])

    # Step 2: Retrieve relevant chunks
    retrieved_chunks = retriever.retrieve_chunks(data["query"])

    # Step 3: Combine both results in a single response
    response = {
        "analysis": analysis_result,
        "retrieved_chunks": retrieved_chunks
    }

    return jsonify(response)
