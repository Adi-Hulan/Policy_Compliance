from langgraph.graph import StateGraph
from typing import Dict, Any, TypedDict

from orchestrator.nodes.document_processor_node import document_processor_node

class DocumentState(TypedDict):
    file_path: str
    status: str
    agent: str
    result: str
    chunks_count: int

def build_document_process_pipeline() -> StateGraph:
    """
    Builds a LangGraph pipeline for processing documents.
    
    The pipeline:
    1. Takes a document file path
    2. Processes the document (extract, chunk, embed, store)
    
    Returns:
        A LangGraph StateGraph that can be executed with a file path.
    """
    # Define the workflow graph
    workflow = StateGraph(DocumentState)
    
    # Add nodes to the graph
    workflow.add_node("document_processor", document_processor_node)
    
    # Set the entry point
    workflow.set_entry_point("document_processor")
    
    # Return the compiled workflow
    return workflow.compile()

# Create a function to execute the pipeline with input validation
def execute_document_pipeline(file_path: str) -> Dict[str, Any]:
    """
    Executes the document processing pipeline with the given file path.
    
    Args:
        file_path: Path to the document file to process.
        
    Returns:
        The final state after pipeline execution.
    """
    # Initialize the pipeline
    pipeline = build_document_process_pipeline()
    
    # Prepare the initial state
    initial_state = {
        "file_path": file_path,
        "status": "pending"
    }
    
    # Execute the pipeline
    try:
        result = pipeline.invoke(initial_state)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Pipeline execution failed: {str(e)}"
        }
