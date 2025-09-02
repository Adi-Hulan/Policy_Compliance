from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query not provided"}), 400

    result = analyzer.process(data["query"])
    return jsonify(result) 
