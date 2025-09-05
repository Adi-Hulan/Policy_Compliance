from orchestrator.pipelines.query_pipeline import execute_query_pipeline
from orchestrator.pipelines.document_process_pipeline import execute_document_pipeline
from orchestrator.pipelines.document_query_pipeline import execute_document_query_pipeline

class Orchestrator:
    """
    Main orchestrator class that routes requests to the appropriate pipelines.
    """
    def __init__(self):
        # No need to initialize agents directly, they're handled in the pipelines
        pass

    def route(self, data):
        """
        Routes the request to the appropriate pipeline based on the input data.
        
        Args:
            data: Dictionary containing request parameters (query, document, etc.)
            
        Returns:
            The result from the appropriate pipeline.
        """
        query = data.get("query")
        file_path = data.get("document")

        # Case 1: Both document and query - analyze document against policies
        if file_path and query:
            return execute_document_query_pipeline(file_path, query)
        
        # Case 2: Document only - process and store the document
        elif file_path:
            return execute_document_pipeline(file_path)
        
        # Case 3: Query only - answer the query using stored policies
        elif query:
            return execute_query_pipeline(query)
        
        # Error case: No valid input
        return {"status": "error", "message": "No valid input provided"}