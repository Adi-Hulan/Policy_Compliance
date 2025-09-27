from flask import Flask
from flask_cors import CORS
from routes.document_routes import document_bp
from routes.query_routes import query_bp
from routes.recommendation_routes import recommendation_bp
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Enable CORS only for React frontend
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)

    # Register blueprints
    app.register_blueprint(document_bp, url_prefix="/documents")
    app.register_blueprint(query_bp, url_prefix="/queries")
    app.register_blueprint(recommendation_bp, url_prefix="/recommendations")

    # Test endpoint to verify CORS
    @app.route("/test-cors", methods=["GET", "OPTIONS"])
    def test_cors():
        from flask import jsonify
        return jsonify({"status": "CORS working", "message": "Backend is accessible from frontend"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
