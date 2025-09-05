from agents.chunk_retriever_temp_doc import TempRetriever
from orchestrator.schemas.models import RetrieverInput, RetrieverOutput, Chunk
from typing import Dict, Any

# Initialize the agent
temp_retriever = TempRetriever()

def temp_retriever_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that wraps the TempRetriever agent.
    
    Args:
        state: The current state containing the query information.
        
    Returns:
        Updated state with retrieval results from temporary documents.
    """
    # Extract the query from the state
    query = state.get("query")
    top_k = state.get("top_k", 5)
    
    # Validate input
    if not query:
        return {"status": "error", "message": "No query provided"}
    
    # Call the retriever agent
    result = temp_retriever.retrieve_chunks(query, top_k)
    
    # Process the result
    if result["status"] == "success":
        # Convert to Pydantic models for type safety
        chunks = [
            Chunk(id=chunk["id"], content=chunk["content"], distance=chunk["distance"])
            for chunk in result["chunks"]
        ]
        
        # Update the state with temp retriever output
        return {
            "status": "success",
            "temp_chunks": [chunk.dict() for chunk in chunks]
        }
    else:
        return {
            "status": "error",
            "message": result.get("message", "Unknown error in temp retriever")
        }
