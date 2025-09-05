from flask import Flask
from flask_cors import CORS
from routes.document_routes import document_bp
from routes.query_routes import query_bp
from middleware.auth_middleware import register_auth_middleware

def create_app():
    app = Flask(__name__)

    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],  # Add Authorization
            "expose_headers": ["Authorization"]
        }
    })

    # Register blueprints
    app.register_blueprint(document_bp, url_prefix="/documents")
    app.register_blueprint(query_bp, url_prefix="/queries")

    # Register auth middleware
    register_auth_middleware(app)  # Remove the public_endpoints parameter

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)