from langgraph.graph import StateGraph
from typing import Dict, Any, TypedDict

from orchestrator.nodes.temp_document_processor_node import temp_document_processor_node
from orchestrator.nodes.retriever_node import retriever_node
from orchestrator.nodes.temp_retriever_node import temp_retriever_node
from orchestrator.nodes.temp_query_analyzer_node import temp_query_analyzer_node

class DocumentQueryState(TypedDict):
    file_path: str
    query: str
    status: str
    agent: str
    result: str
    chunks: list
    temp_chunks: list
    policy_chunks: list

def build_document_query_pipeline() -> StateGraph:
    """
    Builds a LangGraph pipeline for analyzing a temporary document against policies.
    
    The pipeline:
    1. Takes a document file path and a query
    2. Processes the temporary document
    3. Retrieves relevant policy chunks
    4. Retrieves relevant chunks from the temporary document
    5. Analyzes the query against both sets of chunks
    
    Returns:
        A LangGraph StateGraph that can be executed with a file path and query.
    """
    # Define the workflow graph
    workflow = StateGraph(DocumentQueryState)
    
    # Add nodes to the graph
    workflow.add_node("temp_document_processor", temp_document_processor_node)
    workflow.add_node("policy_retriever", retriever_node)
    workflow.add_node("temp_retriever", temp_retriever_node)
    workflow.add_node("analyzer", temp_query_analyzer_node)
    
    # Add edges - both processors run in parallel, then analyzer
    workflow.add_edge("temp_document_processor", "temp_retriever")
    workflow.add_edge("temp_document_processor", "policy_retriever")
    
    # Define conditional edges from processors to analyzer
    workflow.add_conditional_edges(
        "temp_retriever",
        lambda state: "analyzer" if state["status"] == "success" else None
    )
    
    workflow.add_conditional_edges(
        "policy_retriever",
        lambda state: "analyzer" if state["status"] == "success" else None
    )
    
    # Set the entry point
    workflow.set_entry_point("temp_document_processor")
    
    # Return the compiled workflow
    return workflow.compile()

# Create a function to execute the pipeline with input validation
def execute_document_query_pipeline(file_path: str, query: str) -> Dict[str, Any]:
    """
    Executes the document query pipeline with the given file path and query.
    
    Args:
        file_path: Path to the document file to process.
        query: The user's question about compliance.
        
    Returns:
        The final state after pipeline execution.
    """
    # Initialize the pipeline
    pipeline = build_document_query_pipeline()
    
    # Prepare the initial state
    initial_state = {
        "file_path": file_path,
        "query": query,
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
