from agents.query_analyzer import QueryAnalyzer
from orchestrator.schemas.models import QueryAnalyzerInput, QueryAnalyzerOutput
from typing import Dict, Any, List

# Initialize the agent
analyzer = QueryAnalyzer()

def query_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that wraps the QueryAnalyzer agent.
    
    Args:
        state: The current state containing the query and chunks information.
        
    Returns:
        Updated state with analysis results.
    """
    # Extract the query and chunks from the state
    query = state.get("query")
    chunks = state.get("chunks", [])
    
    # Validate input
    if not query:
        return {"status": "error", "message": "No query provided"}
    
    if not chunks:
        return {"status": "error", "message": "No chunks provided for analysis"}
    
    # Extract content from chunks for the analyzer
    chunk_contents = [chunk["content"] for chunk in chunks]
    
    # Call the analyzer agent
    result = analyzer.process(query, chunk_contents)
    
    # Process the result
    if result["status"] == "success":
        return {
            "status": "success",
            "agent": result["agent"],
            "result": result["result"],
            "source_chunks": chunks  # Include source chunks for reference
        }
    else:
        return {
            "status": "error",
            "agent": result.get("agent", "MainQueryAnalyzer"),
            "message": result.get("result", "Unknown error in query analyzer")
        }
