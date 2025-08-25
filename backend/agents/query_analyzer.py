import google.generativeai as genai
from db.connection import get_db

class QueryAnalyzer:
    def process(self, query):
        return {
            "agent": "QueryAnalyzer",
            "status": "success",
            "result": f"Analyzed query: {query}"
        }
