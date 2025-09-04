from flask import request, jsonify
from utils.auth import verify_jwt

def register_auth_middleware(app):
    @app.before_request
    def authenticate():
        # Allow public endpoints
        if request.endpoint in ["auth_bp.login", "auth_bp.register"]:
            return
        
        # Require Authorization header
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        # Verify JWT
        token = auth_header.split(" ")[1]
        decoded = verify_jwt(token)
        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Attach user info for downstream use
        request.user = decoded
