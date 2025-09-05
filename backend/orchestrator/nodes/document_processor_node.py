from agents.document_processor import DocumentProcessor
from orchestrator.schemas.models import DocumentProcessorInput, DocumentProcessorOutput
from typing import Dict, Any

# Initialize the agent
document_processor = DocumentProcessor()

def document_processor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node function that wraps the DocumentProcessor agent.
    
    Args:
        state: The current state containing the file path information.
        
    Returns:
        Updated state with document processing results.
    """
    # Extract the file path from the state
    file_path = state.get("file_path")
    
    # Validate input
    if not file_path:
        return {"status": "error", "message": "No file path provided"}
    
    # Call the document processor agent
    result = document_processor.process(file_path)
    
    # Process the result
    if result["status"] == "success":
        # Parse the result to extract the number of chunks
        result_text = result.get("result", "")
        chunks_count = 0
        
        # Try to extract the number of chunks from the result message
        if "chunks" in result_text:
            try:
                chunks_count = int(result_text.split("into ")[1].split(" chunks")[0])
            except (IndexError, ValueError):
                pass
        
        return {
            "status": "success",
            "agent": result["agent"],
            "result": result["result"],
            "chunks_count": chunks_count
        }
    else:
        return {
            "status": "error",
            "agent": result.get("agent", "DocumentProcessor"),
            "message": result.get("result", "Unknown error in document processor")
        }
