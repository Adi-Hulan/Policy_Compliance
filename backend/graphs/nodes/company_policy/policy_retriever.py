"""
Policy Retriever Node

Retrieves relevant policy chunks using RAG.
Specific to company policy graph.
"""

from typing import Dict, Any
from langchain_core.callbacks import BaseCallbackHandler
from agents.chunk_retriever_v2 import RetrieverV2
from graphs.nodes.models import PolicyRetrieverNodeInput, PolicyRetrieverNodeOutput


class PolicyRetrieverCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for policy retrieval."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[POLICY_RETRIEVER_CALLBACK] Vector search started")

    def on_retriever_end(self, documents, **kwargs):
        print("[POLICY_RETRIEVER_CALLBACK] Vector search completed")


# Shared instance
_policy_retriever = RetrieverV2()


def policy_retriever_node(state) -> Dict[str, Any]:
    """
    Retrieve relevant policy chunks from vector store.

    Args:
        state: Current graph state

    Returns:
        Dict with retrieved_chunks (list of relevant chunks)

    Streams:
        - on_retriever_start: Vector search started
        - on_retriever_end: Vector search completed
        - stage: Policy retrieval progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = PolicyRetrieverNodeInput(
            message=state.message
        )
    except Exception as e:
        raise ValueError(f"Policy retriever input validation failed: {e}")

    query = input_data.message
    session_id = state.session_id

    if not query:
        print("[POLICY_RETRIEVER_NODE] No query, skipping")
        return {}

    print(f"[POLICY_RETRIEVER_NODE] Retrieving for query: {query}")

    # Emit retriever start event
    callback_handler = PolicyRetrieverCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "policy_vector_retriever"},
        query=query
    )

    try:
        # Use retriever to get chunks with citations
        result = _policy_retriever.retrieve_chunks_with_citations(query, top_k=5)

        if result["status"] == "success":
            chunks = result["chunks"]
            print(f"[POLICY_RETRIEVER_NODE] ✓ Retrieved {len(chunks)} chunks with citations")
            # Extract content strings for output validation
            policy_context = [chunk.get("content", "") for chunk in chunks if chunk.get("content")]
            # Store full chunk data including citations for context combination
            policy_chunks_with_metadata = chunks
        else:
            print("[POLICY_RETRIEVER_NODE] ✗ Retrieval failed")
            policy_context = []
            policy_chunks_with_metadata = []

        # Emit retriever end event
        callback_handler.on_retriever_end(documents=policy_context)

        # Return validated output with citation metadata
        output_data = PolicyRetrieverNodeOutput(
            policy_context=policy_context,
            policy_chunks_with_metadata=policy_chunks_with_metadata
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[POLICY_RETRIEVER_NODE] ✗ Retrieval failed: {e}")
        return {}