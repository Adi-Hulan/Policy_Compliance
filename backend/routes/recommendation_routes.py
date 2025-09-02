from flask import Blueprint, request, jsonify
from agents.recommendation_agent import RecommendationAgent

recommendation_bp = Blueprint("recommendations", __name__)

@recommendation_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Query not provided"}), 400

    # Initialize agent here, so environment variables are loaded
    try:
        agent = RecommendationAgent()
    except Exception as e:
        return jsonify({"error": f"Agent initialization failed: {str(e)}"}), 500

    violations = data.get("violations")  # Optional from violation detector
    result = agent.process(data["query"], violations)
    return jsonify(result)
