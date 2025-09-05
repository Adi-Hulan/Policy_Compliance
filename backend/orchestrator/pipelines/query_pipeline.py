from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph
from typing import Dict, Any, TypedDict

from orchestrator.nodes.retriever_node import retriever_node
from orchestrator.nodes.query_analyzer_node import query_analyzer_node
from orchestrator.nodes.message_sender_node import message_sender_node

class QueryState(TypedDict):
    query: str
    status: str
    chunks: list
    result: str
    source_chunks: list
    message_status: str
    message_id: str
    message_created_at: str
    message_error: str

def build_query_pipeline() -> StateGraph:
    """
    Builds a LangGraph pipeline for processing policy queries.
    
    The pipeline:
    1. Takes a user query
    2. Retrieves relevant policy chunks
    3. Analyzes the query against the retrieved chunks
    4. Sends the result back to the messages table as an agent response
    
    Returns:
        A LangGraph StateGraph that can be executed with a query.
    """
    # Define the workflow graph
    workflow = StateGraph(QueryState)
    
    # Add nodes to the graph
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("analyzer", query_analyzer_node)
    workflow.add_node("message_sender", message_sender_node)
    
    # Add edges
    workflow.add_edge("retriever", "analyzer")
    workflow.add_edge("analyzer", "message_sender")
    
    # Set the entry point
    workflow.set_entry_point("retriever")
    
    # Define conditional edges - if retriever fails, stop the process
    workflow.add_conditional_edges(
        "retriever",
        lambda state: "analyzer" if state["status"] == "success" else None
    )
    
    # Return the compiled workflow
    return workflow.compile()

# Create a function to execute the pipeline with input validation
def execute_query_pipeline(query: str) -> Dict[str, Any]:
    """
    Executes the query pipeline with the given query.
    
    Args:
        query: The user's question about policies.
        
    Returns:
        The final state after pipeline execution.
    """
    # Initialize the pipeline
    pipeline = build_query_pipeline()
    
    # Prepare the initial state
    initial_state = {
        "query": query,
        "status": "pending"
    }
    
    # Execute the pipeline
    try:
        result = pipeline.invoke(initial_state)
        
        # Include message information in the response
        if result.get("message_status") == "success":
            result["agent_message_sent"] = True
            result["agent_message_id"] = result.get("message_id")
        else:
            result["agent_message_sent"] = False
            result["agent_message_error"] = result.get("message_error")
            
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Pipeline execution failed: {str(e)}"
        }
