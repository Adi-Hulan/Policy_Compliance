from flask import Blueprint, request, jsonify
import requests
from agents.document_processor import DocumentProcessor
from agents.temp_doc_processor import DocumentProcessorTemp
from utils.supabase_client import supabase
import os
import tempfile
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever
from agents.chunk_retriever_temp_doc import TempRetriever
from agents.temp_query_analyzer import TempQueryAnalyzer

analyzer = QueryAnalyzer()
retriever = Retriever()
temp_retriever = TempRetriever()
temp_analyzer = TempQueryAnalyzer()

document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()
temp_processor = DocumentProcessorTemp()


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

@document_bp.route("/upload/temp", methods=["POST"])
def upload_temp_document():
    
    print("inside upload/temp")
    data = request.get_json()
    print(f"data received: {data}")
    if not data or "fileUrl" not in data:
        return jsonify({"error": "filePath missing"}), 400

    file_path = data["fileUrl"]  # e.g. "uploads/169375-file.pdf"
    print(f"file_path: {file_path}")

    try:
        # 1. Download file from Supabase Storage
        resbefore = requests.get(file_path)
        res = resbefore.content  

        # 2. Save temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_file_path = tmp.name

        print(f"Temporary file saved at: {tmp_file_path}")
        # 3. Pass to your processor
        result = temp_processor.process(tmp_file_path)

        # 4. Clean up temp file
        os.remove(tmp_file_path)

        data = request.json
        if not data or "query" not in data:
            return jsonify({"error": "Query not provided"}), 400

        relevent_chunks = retriever.retrieve_chunks(data["query"])
        relevent_chunks_from_temp = temp_retriever.retrieve_chunks(data["query"])
        print("going to analyzer")
        response = temp_analyzer.process(
            data["query"],
            policy_chunks=relevent_chunks,
            temp_chunks=relevent_chunks_from_temp
        )

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    