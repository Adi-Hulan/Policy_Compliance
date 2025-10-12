from flask import Blueprint, request, jsonify
from agents.document_processor import DocumentProcessor
import os
import tempfile
import requests
from agents.policy_analyze_document_processor import AnalyzeDocumentProcessorTemp
from agents.policy_analyze_chunk_retriever import PolicyAnalyzeRetriever
from agents.international_policy_retriever import InternationalPolicyRetriever
from google import genai
from middleware.auth import require_auth
from agents.international_policy_processor import InternationalPolicyProcessor

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()
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
            top_k=3
        )

        # Map back attached chunks to matching policies
        paired_contexts = []
        if retrieval_results["status"] == "success":
            for idx, matches in retrieval_results["results"].items():
                attached_chunk = chunk_embeddings[int(idx)]["chunk"]
                for match in matches:
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
                    top_k=3
                )
                
                if int_policy_results["status"] == "success":
                    for idx, matches in int_policy_results["results"].items():
                        attached_chunk = chunk_embeddings[int(idx)]["chunk"]
                        for match in matches:
                            paired_contexts.append({
                                "attached_chunk": attached_chunk,
                                "matching_policy": match["content"],
                                "distance": match["distance"],
                                "policy_type": f"international_policy_{policy}"
                            })

        print(f"Total paired contexts: {paired_contexts}")
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

        print("Violations found:", violations)
        return jsonify(violations)

    finally:
        os.remove(tmp_file_path)

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