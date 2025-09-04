# from flask import Blueprint, request, jsonify
# from agents.query_analyzer import QueryAnalyzer
# from agents.chuck_retriever import Retriever

# query_bp = Blueprint("queries", __name__)
# analyzer = QueryAnalyzer()
# retriever = Retriever()

# @query_bp.route("/analyze", methods=["POST"])
# def analyze_query():
#     data = request.json
#     if not data or "query" not in data:
#         return jsonify({"error": "Query not provided"}), 400

#     print(f"query recived : {data}")
#     relevent_chunks = retriever.retrieve_chunks(data["query"])
#     response = analyzer.process(data["query"],relevent_chunks)
#     return jsonify(response)


from flask import Blueprint, request, jsonify
from agents.temp_doc_processor import DocumentProcessor
from supabase_client import supabase
import os
import tempfile

document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()



@document_bp.route("/upload/temp", methods=["POST"])
def upload_temp_document():
    
    print("inside upload/temp")
    data = request.get_json()
    if not data or "fileUrl" not in data:
        return jsonify({"error": "filePath missing"}), 400

    file_path = data["fileUrl"]  # e.g. "uploads/169375-file.pdf"

    try:
        # 1. Download file from Supabase Storage
        res = supabase.storage.from_("uploads").download(file_path)

        # 2. Save temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(res)
            tmp_file_path = tmp.name

        print(f"Temporary file saved at: {tmp_file_path}")
        # 3. Pass to your processor
        result = processor.process(tmp_file_path)

        # 4. Clean up temp file
        os.remove(tmp_file_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
