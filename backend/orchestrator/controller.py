from agents.document_processor import DocumentProcessor
from agents.query_analyzer import QueryAnalyzer
from agents.recommendation_agent import RecommendationAgent

class Orchestrator:
    def __init__(self):
        self.document_agent = DocumentProcessor()
        self.query_agent = QueryAnalyzer()
        self.recommendation_agent = RecommendationAgent()

    def route(self, data):
        query = data.get("query")
        doc_path = data.get("document")
        action = data.get("action")

        # Handle recommendation first (priority case)
        if action == "recommend" and query:
            return self.recommendation_agent.process(query, data.get("violations"))

        if doc_path:
            return self.document_agent.process(doc_path)
        elif query:
            return self.query_agent.process(query)
        return {"error": "No input provided"}
        
        