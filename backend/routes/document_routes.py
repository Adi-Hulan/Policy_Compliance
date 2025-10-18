from flask import Blueprint, request, jsonify
from agents.document_processor import DocumentProcessor, DocumentProcessorV2
import os
import tempfile
import requests
from agents.policy_analyze_document_processor import AnalyzeDocumentProcessorTemp
from agents.policy_analyze_chunk_retriever import PolicyAnalyzeRetriever
from agents.chunk_retriever_v2 import RetrieverV2
from google import genai
from middleware.auth import require_auth
from pathlib import Path
from agents.international_policy_retriever import InternationalPolicyRetriever
from google import genai
from middleware.auth import require_auth
from agents.international_policy_processor import InternationalPolicyProcessor

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()
processor_v2 = DocumentProcessorV2()
retriever_v2 = RetrieverV2()
doc_processor = AnalyzeDocumentProcessorTemp()
policyAnalyzeRetriever = PolicyAnalyzeRetriever()
internationalPolicyRetriever = InternationalPolicyRetriever()
int_processor = InternationalPolicyProcessor()

@document_bp.route("/upload", methods=["POST"])
@require_auth
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


# same route different table --tetsing purposes
@document_bp.route("/upload_v2", methods=["POST"])
@require_auth
def upload_document_v2():
    """Test endpoint for the enhanced document processor with citation support."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    # Ensure uploads directory exists
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    result = processor_v2.process(file_path)
    return jsonify(result)

@document_bp.route("/query_v2", methods=["POST"])
@require_auth
def query_documents_v2():
    """Test endpoint for enhanced retrieval with citation support."""
    data = request.json
    question = data.get("question")
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    top_k = data.get("top_k", 5)
    print(f"[DEBUG] /query_v2 called with question={question!r} top_k={top_k}")
    result = retriever_v2.retrieve_chunks_with_citations(question, top_k)
    return jsonify(result)

@document_bp.route("/analyze", methods=["POST"])
@require_auth
def analyze_document():
    data = request.json
    document_url = data.get("document_url")
    session_id = data.get("session_id")
    selected_policies = data.get("selected_policies", [])
    safe_session_id = session_id.replace("-", "_")

    if not document_url:
        return jsonify({"error": "No document URL provided"}), 400

    # Download file
    res = requests.get(document_url).content
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(res)
        tmp_file_path = tmp.name

    try:
        # Process into chunks + embeddings
        vector_store = doc_processor.process(tmp_file_path, safe_session_id)
        chunk_embeddings = vector_store["chunk_embeddings"]

        retrieval_results = policyAnalyzeRetriever.retrieve_for_embeddings(
            [c["embedding"] for c in chunk_embeddings],
            safe_session_id,
            top_k=1
        )

        # Map back attached chunks to matching policies
        paired_contexts = []
        if retrieval_results["status"] == "success":
            for idx, matches in retrieval_results["results"].items():
                attached_chunk = chunk_embeddings[int(idx)]["chunk"]
                for match in matches:
                    if match["distance"] < 0.4:
                        paired_contexts.append({
                            "attached_chunk": attached_chunk,
                            "matching_policy": match["content"],
                            "distance": match["distance"],
                            "policy_type": "company_policy"
                        })
                    
        # Process international policies if selected
        if selected_policies:
            document_embeddings = [c["embedding"] for c in chunk_embeddings]
            
            for policy in selected_policies:
                int_policy_results = internationalPolicyRetriever.retrieve_for_embeddings(
                    document_embeddings,
                    safe_session_id,
                    policy,
                    top_k=1
                )
                
                if int_policy_results["status"] == "success":
                    for idx, matches in int_policy_results["results"].items():
                        attached_chunk = chunk_embeddings[int(idx)]["chunk"]
                        for match in matches:
                            if match["distance"] < 0.4:
                                paired_contexts.append({
                                    "attached_chunk": attached_chunk,
                                    "matching_policy": match["content"],
                                    "distance": match["distance"],
                                    "policy_type": f"international_policy_{policy}"
                                })

        print(f"Total paired contexts: {len(paired_contexts)}")
        # Prompt Gemini
        prompt = f"""
        You are a compliance analyzer. Compare attached document clauses with both company policies and international regulations. 
        Identify violations, explain them, and return only a JSON array of objects in this format:

        [
          {{
            "type": "Violation",
            "title": "...",
            "description": "...",
            "severity": "high|medium|low",
            "policy_type": "..."  # either 'Company Policy' or 'International Policy - [policy_name]'
          }}
        ]

        Note that each paired context includes a policy_type field indicating whether it's a company policy or an international policy (like GDPR, HIPAA, etc).

        Here are the pairs of context:
        {paired_contexts}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        import json
        import re

        raw_text = response.text

        # Remove ```json or ``` code block if present
        cleaned_text = re.sub(r"^```json\s*|```$", "", raw_text.strip())

        try:
            violations = json.loads(cleaned_text)
        except json.JSONDecodeError:
            violations = {"error": "Failed to parse LLM response", "raw": raw_text}

        print("Violations found:", len(violations))
        return jsonify(violations)

    finally:
        os.remove(tmp_file_path)

@document_bp.route('/retrieve-citation', methods=['GET'])
@require_auth
def retrieve_citation_flask():
    """Flask endpoint to retrieve a citation by character range from a file on disk.

    Query params:
      - file_path: full path to the file (or filename in ./uploads)
      - char_start: start index
      - char_end: end index
    """
    file_path = request.args.get('file_path')
    char_start = request.args.get('char_start')
    char_end = request.args.get('char_end')

    print(f"[DEBUG] /documents/retrieve-citation called with file_path={file_path} char_start={char_start} char_end={char_end}")

    if not file_path or char_start is None or char_end is None:
        return jsonify({'error': 'file_path, char_start and char_end are required'}), 400

    try:
        char_start = int(char_start)
        char_end = int(char_end)
    except ValueError:
        return jsonify({'error': 'char_start and char_end must be integers'}), 400

    # Support either an absolute path or a filename inside ./uploads
    doc_path = Path(file_path)
    if not doc_path.is_absolute():
        upload_dir = Path(os.path.abspath('./uploads'))
        doc_path = upload_dir.joinpath(os.path.basename(file_path))

    if not doc_path.exists():
        return jsonify({'error': 'file not found'}), 404

    try:
        with doc_path.open('r', encoding='utf-8') as f:
            content = f.read()

        if char_start < 0 or char_end > len(content) or char_start >= char_end:
            return jsonify({'error': 'invalid character range'}), 400

        citation_text = content[char_start:char_end]
        return jsonify({'citation_text': citation_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@document_bp.route('/text', methods=['GET'])
@require_auth
def get_document_text():
    """
    Return the plain text of a document stored in ./uploads by filename.
    Query params:
      - filename: the filename under ./uploads (required)

    Security: only files under ./uploads are returned to avoid path traversal.
    """
    filename = request.args.get('filename')
    print(f"[DEBUG] /documents/text called with filename={filename}")
    if not filename:
        return jsonify({'error': 'filename query parameter required'}), 400

    # Normalize filename to avoid path traversal
    safe_name = os.path.basename(filename)
    upload_dir = os.path.abspath('./uploads')
    file_path = os.path.join(upload_dir, safe_name)

    if not os.path.exists(file_path):
        return jsonify({'error': 'file not found'}), 404

    try:
        # If the file is a PDF, use our PDF parser to extract text
        _, ext = os.path.splitext(file_path)
        ext = (ext or '').lower()
        if ext == '.pdf':
            from utils.pdf_parser import extract_text_from_pdf
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        return jsonify({'filename': safe_name, 'text': content})
    except Exception as e:
        print(f"[ERROR] get_document_text failed for {file_path}: {e}")
        return jsonify({'error': 'failed to read document text', 'details': str(e)}), 500

@document_bp.route("/upload/international", methods=["POST"])
def upload_international_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
# Ensure uploads directory exists
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    result = int_processor.process(file_path)
    return jsonify(result)
