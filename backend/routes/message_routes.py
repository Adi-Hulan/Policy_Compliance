from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever
import logging
from datetime import datetime

# Create blueprint for message processing
messages_bp = Blueprint('messages', __name__)

# Create instances of analyzer and retriever
analyzer = QueryAnalyzer()
retriever = Retriever()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@messages_bp.route('/messages', methods=['POST'])
def process_message():
    """
    Process a message from the frontend after it's been inserted into Supabase.
    This endpoint receives the message and processes it through the agent pipeline.
    """
    try:
        # Get the message payload from frontend
        payload = request.get_json()
        
        if not payload:
            logger.error("No JSON payload received")
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # Extract message details
        message_id = payload.get('id')
        username = payload.get('username')
        content = payload.get('content')
        room = payload.get('room')
        created_at = payload.get('created_at')
        
        logger.info(f"📨 Processing message from {username}: {content[:50]}...")
        
        # Validate required fields
        if not content:
            logger.error("No content provided in message")
            return jsonify({"error": "Message content is required"}), 400
            
        if not username:
            logger.error("No username provided in message")
            return jsonify({"error": "Username is required"}), 400
        
        # Process only messages from "john_doe" (as per your requirement)
        if username != "john_doe":
            logger.info(f"⏭️ Skipping message from {username} (not john_doe)")
            return jsonify({
                "message": "Message received but not processed (user not john_doe)",
                "message_id": message_id,
                "username": username
            }), 200
        
        logger.info(f"🔄 Processing message from john_doe: {content}")
        
        # Process the message through the agent pipeline
        # Step 1: Retrieve relevant chunks
        retrieved = retriever.retrieve_chunks(content)
        if isinstance(retrieved, dict):
            chunks = retrieved.get("chunks", [])
        else:
            chunks = retrieved or []
        
        logger.info(f"📚 Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Analyze the query
        analysis_result = analyzer.process(content, chunks)
        
        logger.info(f"✅ Analysis complete: {analysis_result}")
        
        # Return success response
        return jsonify({
            "success": True,
            "message": "Message processed successfully",
            "data": {
                "message_id": message_id,
                "username": username,
                "content": content,
                "room": room,
                "processed_at": datetime.utcnow().isoformat(),
                "chunks_retrieved": len(chunks),
                "analysis_result": analysis_result
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@messages_bp.route('/messages/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the message processing service is running.
    """
    return jsonify({
        "status": "healthy",
        "service": "message_processor",
        "timestamp": datetime.utcnow().isoformat()
    }), 200
