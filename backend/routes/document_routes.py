from flask import Blueprint, request, jsonify
import requests
from utils.supabase_client import supabase
import os
import tempfile
from orchestrator.controller import Orchestrator

document_bp = Blueprint("documents", __name__)
orchestrator = Orchestrator()

@document_bp.route("/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    file_path = f"./uploads/{file.filename}"
    print(f"Saving file to: {file_path}")
    file.save(file_path)

    # Use the orchestrator to process the document
    result = orchestrator.route({"document": file_path})
    return jsonify(result)

@document_bp.route("/upload/temp", methods=["POST"])
def upload_temp_document():
    print("Processing temporary document upload")
    data = request.get_json()
    
    if not data or "fileUrl" not in data:
        return jsonify({"error": "fileUrl missing"}), 400
    
    if "query" not in data:
        return jsonify({"error": "Query not provided"}), 400

    file_path = data["fileUrl"]  # e.g. "uploads/169375-file.pdf"
    query = data["query"]
    
    try:
        # 1. Download file from Supabase Storage
        resbefore = requests.get(file_path)
        res = resbefore.content  

        # 2. Save temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_file_path = tmp.name

        print(f"Temporary file saved at: {tmp_file_path}")
        
        # 3. Use the orchestrator to process both document and query
        response = orchestrator.route({
            "document": tmp_file_path,
            "query": query
        })

        # 4. Clean up temp file
        os.remove(tmp_file_path)

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    