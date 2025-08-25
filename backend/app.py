from flask import Flask
from routes.document_routes import document_bp
from routes.query_routes import query_bp
from routes.chat_routes import chat_bp
import threading
import asyncio
from utils.listener import listen_new_messages

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(document_bp, url_prefix="/documents")
    app.register_blueprint(query_bp, url_prefix="/queries")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    # Start listener after first request
    @app.before_request
    def start_listener():
        def run_listener():
            asyncio.run(listen_new_messages())
        threading.Thread(target=run_listener, daemon=True).start()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
