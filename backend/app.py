
from flask import Flask
from flask_cors import CORS
from routes.document_routes import document_bp
from routes.query_routes import query_bp
from routes.recommendation_routes import recommendation_bp 

def create_app():
    app = Flask(__name__)
    
# Enable Cross-Origin Resource Sharing
    CORS(app)

    print("Creating app and registering blueprints")

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

    # Register blueprints
    app.register_blueprint(document_bp, url_prefix="/documents")
    app.register_blueprint(query_bp, url_prefix="/queries")
    app.register_blueprint(recommendation_bp, url_prefix="/recommendations")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)