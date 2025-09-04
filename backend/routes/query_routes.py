from flask import Blueprint, request, jsonify
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever

query_bp = Blueprint("queries", __name__)
analyzer = QueryAnalyzer()
retriever = Retriever()

@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    print("🚀 QUERY ANALYZER ENDPOINT HIT!")
    
    data = request.json
    if not data or "query" not in data:
        print("❌ No query provided in request")
        return jsonify({"error": "Query not provided"}), 400

    query_text = data["query"]
    print(f"💬 Query received from chat: {query_text}")
    print(f"📦 Full payload: {data}")
    
    print("🔍 Retrieving relevant chunks...")
    relevent_chunks = retriever.retrieve_chunks(query_text)
    print(f"📚 Retrieved {len(relevent_chunks) if isinstance(relevent_chunks, list) else 'N/A'} chunks")
    
    print("🤖 Processing with QueryAnalyzer...")
    response = analyzer.process(query_text, relevent_chunks)
    print(f"✅ Analysis complete: {response}")
    
    return jsonify(response)
