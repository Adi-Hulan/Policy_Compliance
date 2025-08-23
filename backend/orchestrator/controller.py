class Orchestrator:
    def __init__(self):
        pass

    def route(self, data):
        query = data.get("query")
        doc = data.get("document")
        # Simple logic (expand later)
        if doc:
            return {"agent": "DocumentProcessor", "result": f"Processed document: {doc}"}
        elif query:
            return {"agent": "QueryAnalyzer", "result": f"Analyzed query: {query}"}
        return {"error": "No input provided"}