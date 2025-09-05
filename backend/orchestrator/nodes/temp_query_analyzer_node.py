from agents.temp_query_analyzer import TempQueryAnalyzer
from orchestrator.schemas.models import QueryAnalyzerInput, QueryAnalyzerOutput
from typing import Dict, Any, List

# Initialize the agent
temp_analyzer = TempQueryAnalyzer()

def temp_query_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that wraps the TempQueryAnalyzer agent.
    
    Args:
        state: The current state containing the query, policy chunks, and temp chunks information.
        
    Returns:
        Updated state with analysis results.
    """
    # Extract the query and chunks from the state
    query = state.get("query")
    policy_chunks = state.get("chunks", {"chunks": []})
    temp_chunks = state.get("temp_chunks", {"chunks": []})
    
    # Validate input
    if not query:
        return {"status": "error", "message": "No query provided"}
    
    if not policy_chunks.get("chunks") and not temp_chunks.get("chunks"):
        return {"status": "error", "message": "No chunks provided for analysis"}
    
    # Call the temp analyzer agent
    result = temp_analyzer.process(query, policy_chunks, temp_chunks)
    
    # Process the result
    if result["status"] == "success":
        return {
            "status": "success",
            "agent": result["agent"],
            "result": result["result"],
            "policy_chunks": policy_chunks.get("chunks", []),
            "temp_chunks": temp_chunks.get("chunks", [])
        }
    else:
        return {
            "status": "error",
            "agent": result.get("agent", "TempQueryAnalyzer"),
            "message": result.get("result", "Unknown error in temp query analyzer")
        }
