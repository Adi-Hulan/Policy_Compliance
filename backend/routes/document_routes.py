from flask import Blueprint, request, jsonify, Flask
from flask_cors import cross_origin, CORS
from agents.document_processor import DocumentProcessor
from agents.policy_analyze_document_processor import AnalyzeDocumentProcessorTemp
from agents.policy_analyze_chunk_retriever import PolicyAnalyzeRetriever
import os
import tempfile
import requests
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes and methods

document_bp = Blueprint("documents", __name__)
processor = DocumentProcessor()
doc_processor = AnalyzeDocumentProcessorTemp()
policyAnalyzeRetriever = PolicyAnalyzeRetriever()

# Allow CORS for React frontend
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

@document_bp.route("/upload", methods=["POST", "OPTIONS"])
@cross_origin(origins=CORS_ORIGINS)
def upload_document():
    if request.method == "OPTIONS":
        # Preflight request
        return jsonify({"status": "ok"}), 200

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    # Ensure uploads directory exists
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    result = processor.process(file_path)
    return jsonify(result), 200


@document_bp.route('/documents/analyze', methods=['POST', 'OPTIONS'])
@cross_origin()
def analyze_document():
    if request.method == "OPTIONS":
        # Preflight request
        return jsonify({"status": "ok"}), 200

    data = request.json
    document_url = data.get("document_url")
    session_id = data.get("session_id")
    safe_session_id = session_id.replace("-", "_") if session_id else "default_session"

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
        chunk_embeddings = vector_store.get("chunk_embeddings", [])

        retrieval_results = policyAnalyzeRetriever.retrieve_for_embeddings(
            [c["embedding"] for c in chunk_embeddings],
            safe_session_id,
            top_k=3
        )

        # Map back attached chunks to matching policies
        paired_contexts = []
        if retrieval_results.get("status") == "success":
            for idx, matches in retrieval_results["results"].items():
                attached_chunk = chunk_embeddings[int(idx)]["chunk"]
                for match in matches:
                    paired_contexts.append({
                        "attached_chunk": attached_chunk,
                        "matching_policy": match["content"],
                        "distance": match["distance"]
                    })

        # Prepare prompt for Gemini
        prompt = f"""
        You are a compliance analyzer. Compare attached document clauses with company policies. 
        Identify violations, explain them, and return only a JSON array of objects in this format:

        [
          {{
            "type": "Violation",
            "title": "...",
            "description": "...",
            "severity": "high|medium|low"
          }}
        ]

        Here are the pairs of context:
        {paired_contexts}
        """

        response = genai.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        import json, re
        raw_text = response.text
        cleaned_text = re.sub(r"^```json\s*|```$", "", raw_text.strip())

        try:
            violations = json.loads(cleaned_text)
        except json.JSONDecodeError:
            violations = {"error": "Failed to parse LLM response", "raw": raw_text}

        # Generate recommendations if violations exist
        if isinstance(violations, list) and violations:
            from agents.recommendation_agent import RecommendationAgent
            recommendation_agent = RecommendationAgent()
            recommendation_result = recommendation_agent.generate_recommendations(violations, paired_contexts)

            return jsonify({
                "violations": violations,
                "recommendations": recommendation_result,
                "paired_contexts": paired_contexts
            }), 200
        else:
            return jsonify({
                "violations": violations,
                "recommendations": {
                    "agent": "RecommendationAgent",
                    "status": "success",
                    "message": "No violations found, no recommendations needed",
                    "recommendations": [],
                    "confidence": 1.0,
                    "reasoning": "Document is compliant with company policies"
                },
                "paired_contexts": paired_contexts
            }), 200

    finally:
        os.remove(tmp_file_path)
