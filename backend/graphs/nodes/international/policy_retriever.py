"""
International Policy Retriever Node

Retrieves relevant international policy chunks using RAG.
Specific to international policy graph.
"""

from typing import Dict, Any
from langchain_core.callbacks import BaseCallbackHandler
from agents.international_policy_retriever import InternationalPolicyRetriever
from graphs.nodes.models import PolicyRetrieverNodeInput, PolicyRetrieverNodeOutput


class InternationalPolicyRetrieverCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for international policy retrieval."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[INTERNATIONAL_POLICY_RETRIEVER_CALLBACK] Vector search started")

    def on_retriever_end(self, documents, **kwargs):
        print("[INTERNATIONAL_POLICY_RETRIEVER_CALLBACK] Vector search completed")


# Shared instance
_international_policy_retriever = InternationalPolicyRetriever()


def international_policy_retriever_node(state) -> Dict[str, Any]:
    """
    Retrieve relevant international policy chunks from vector store.

    Args:
        state: Current graph state

    Returns:
        Dict with retrieved_chunks (list of relevant chunks)

    Streams:
        - on_retriever_start: Vector search started
        - on_retriever_end: Vector search completed
        - stage: International policy retrieval progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = PolicyRetrieverNodeInput(
            message=state.message
        )
    except Exception as e:
        raise ValueError(f"International policy retriever input validation failed: {e}")

    query = input_data.message
    session_id = state.session_id

    if not query:
        print("[INTERNATIONAL_POLICY_RETRIEVER_NODE] No query, skipping")
        return {}

    print(f"[INTERNATIONAL_POLICY_RETRIEVER_NODE] Retrieving for query: {query}")

    # Emit retriever start event
    callback_handler = InternationalPolicyRetrieverCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "international_policy_vector_retriever"},
        query=query
    )

    try:
        # For now, we'll need to implement a method similar to retrieve_chunks_with_citations
        # Since the InternationalPolicyRetriever doesn't have this method yet, we'll create a basic implementation
        # This will need to be enhanced to match the company policy retriever functionality

        # Generate embedding for the query
        result = _international_policy_retriever.client.models.embed_content(
            model=_international_policy_retriever.model,
            contents=[query]
        )
        query_embedding = result.embeddings[0].values
        query_embedding = [float(x) for x in query_embedding]

        # For international policies, we need to determine which policy to search
        # For now, let's assume we search across all policies or need policy specification
        # This is a simplified version - in practice, we'd need to determine the relevant policy

        # Get all available policies from the database (this is a placeholder)
        # In a real implementation, we'd have a method to get available policies
        policies = ["GDPR", "HIPAA", "SOX"]  # Placeholder

        all_chunks = []
        for policy in policies:
            policy_results = _international_policy_retriever.retrieve_for_embeddings(
                [query_embedding], session_id, policy, top_k=3
            )

            if policy_results["status"] == "success":
                for embedding_results in policy_results["results"].values():
                    for chunk_data in embedding_results:
                        chunk_data["policy_type"] = f"international_policy_{policy}"
                        all_chunks.append(chunk_data)

        print(f"[INTERNATIONAL_POLICY_RETRIEVER_NODE] ✓ Retrieved {len(all_chunks)} chunks")

        # Extract content strings for output validation
        policy_context = [chunk.get("content", "") for chunk in all_chunks if chunk.get("content")]
        # Store full chunk data including metadata
        policy_chunks_with_metadata = all_chunks

        # Emit retriever end event
        callback_handler.on_retriever_end(documents=policy_context)

        # Return validated output with metadata
        output_data = PolicyRetrieverNodeOutput(
            policy_context=policy_context,
            policy_chunks_with_metadata=policy_chunks_with_metadata
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[INTERNATIONAL_POLICY_RETRIEVER_NODE] ✗ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return {}