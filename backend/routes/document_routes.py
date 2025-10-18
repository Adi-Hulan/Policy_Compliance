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
from fastapi import APIRouter, HTTPException, Query
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
router = APIRouter()
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

@router.get("/retrieve-citation")
def retrieve_citation(
    file_path: str = Query(..., description="Path to the document file"),
    char_start: int = Query(..., description="Start character index of the citation"),
    char_end: int = Query(..., description="End character index of the citation")
):
    """
    Retrieve a citation from a document based on character range.

    Args:
        file_path (str): Path to the document file.
        char_start (int): Start character index of the citation.
        char_end (int): End character index of the citation.

    Returns:
        dict: Extracted citation text.
    """
    try:
        # Validate file existence
        document = Path(file_path)
        if not document.exists():
            raise HTTPException(status_code=404, detail="Document not found")

        # Read the document content
        with document.open("r", encoding="utf-8") as file:
            content = file.read()

        # Validate character range
        if char_start < 0 or char_end > len(content) or char_start >= char_end:
            raise HTTPException(status_code=400, detail="Invalid character range")

        # Extract the citation text
        citation_text = content[char_start:char_end]
        return {"citation_text": citation_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

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
