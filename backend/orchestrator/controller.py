from agents.document_processor import DocumentProcessor
from agents.query_analyzer import QueryAnalyzer

class Orchestrator:
    def __init__(self):
        self.document_agent = DocumentProcessor()
        self.query_agent = QueryAnalyzer()

    def route(self, data):
        query = data.get("query")
        doc_path = data.get("document")

        if doc_path:
            return self.document_agent.process(doc_path)
        elif query:
            return self.query_agent.process(query)
        return {"error": "No input provided"}