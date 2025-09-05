from flask import Blueprint, request, jsonify
from orchestrator.controller import Orchestrator

query_bp = Blueprint("queries", __name__)
orchestrator = Orchestrator()

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query not provided"}), 400

    print(f"Query received: {data}")
    
    # Use the orchestrator to process the query
    response = orchestrator.route(data)
    
    return jsonify(response)
