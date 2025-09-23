from flask import Blueprint, request, jsonify
from agents.document_processor import DocumentProcessor
import os

document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()

@document_bp.route("/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
# Ensure uploads directory exists
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    result = processor.process(file_path)
    return jsonify(result)
