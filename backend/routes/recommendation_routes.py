from flask import Blueprint, request, jsonify
from agents.recommendation_agent import RecommendationAgent
from middleware.auth import require_auth

recommendation_bp = Blueprint("recommendations", __name__)
recommendation_agent = RecommendationAgent()

@recommendation_bp.route("/generate", methods=["POST"])
@require_auth
def generate_recommendations():
    """
    Generate recommendations based on violation data
    
    Expected input:
    {
        "violations": [
            {
                "type": "Violation",
                "title": "...",
                "description": "...",
                "severity": "high|medium|low"
            }
        ],
        "session_id": "optional-session-id"
    }
    """
    try:
        print("Received recommendation request inside backend")
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        violations = data.get("violations", [])
        session_id = data.get("session_id")
        
        if not violations:
            return jsonify({
                "agent": "RecommendationAgent",
                "status": "success",
                "message": "No violations provided, no recommendations needed",
                "recommendations": [],
                "confidence": 1.0,
                "reasoning": "No compliance violations identified"
            })
        
        # Generate recommendations
        result = recommendation_agent.generate_recommendations(violations)
        
        # Add summary if successful
        if result["status"] == "success":
            recommendations = result["recommendations"]
            print(f"Generated recommendations: {recommendations}")
            result["summary"] = recommendation_agent.get_recommendation_summary(recommendations)
        
        print(f"Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "agent": "RecommendationAgent",
            "status": "error",
            "result": str(e)
        }), 500

@recommendation_bp.route("/summary", methods=["POST"])
@require_auth
def get_recommendation_summary():
    """
    Get a summary of recommendations
    
    Expected input:
    {
        "recommendations": [
            {
                "violation_id": "...",
                "recommendation": "...",
                "priority": "high|medium|low",
                "timeline": "immediate|short-term|long-term",
                "resources_needed": "...",
                "expected_outcome": "..."
            }
        ]
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recommendations = data.get("recommendations", [])
        
        if not recommendations:
            return jsonify({"error": "No recommendations provided"}), 400
        
        summary = recommendation_agent.get_recommendation_summary(recommendations)
        return jsonify({
            "agent": "RecommendationAgent",
            "status": "success",
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({
            "agent": "RecommendationAgent",
            "status": "error",
            "result": str(e)
        }), 500