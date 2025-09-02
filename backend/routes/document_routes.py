from flask import Blueprint, request, jsonify
from agents.document_processor import DocumentProcessor

document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()

@document_bp.route("/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    file_path = f"./uploads/{file.filename}"
    print(file_path)
    file.save(file_path)

    result = processor.process(file_path)
    return jsonify(result)

@document_bp.route("/test", methods=["GET"])
def test():
    print("Test endpoint hit")
