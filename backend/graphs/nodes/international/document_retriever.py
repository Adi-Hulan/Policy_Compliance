"""
International Policy Document Retriever Node

Retrieves relevant chunks from processed document.
Specific to international policy graph.
"""

from typing import Dict, Any
from langchain_core.callbacks import BaseCallbackHandler
from agents.chunk_retriever_temp import TempRetriever
from graphs.nodes.models import DocumentRetrieverNodeInput, DocumentRetrieverNodeOutput


class InternationalDocumentRetrieverCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for document retrieval."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[INTERNATIONAL_DOCUMENT_RETRIEVER_CALLBACK] Vector search started")

    def on_retriever_end(self, documents, **kwargs):
        print("[INTERNATIONAL_DOCUMENT_RETRIEVER_CALLBACK] Vector search completed")


# Shared instance
_temp_retriever = TempRetriever()


def international_document_retriever_node(state) -> Dict[str, Any]:
    """
    Retrieve relevant chunks from processed document.

    Args:
        state: Current graph state

    Returns:
        Dict with retrieved_chunks (list of relevant chunks)

    Streams:
        - on_retriever_start: Vector search started
        - on_retriever_end: Vector search completed
        - stage: Document retrieval progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = DocumentRetrieverNodeInput(
            message=state.message,
            tmp_file_path=state.tmp_file_path
        )
    except Exception as e:
        raise ValueError(f"Document retriever input validation failed: {e}")

    query = input_data.message
    tmp_file_path = input_data.tmp_file_path

    if not query:
        print("[INTERNATIONAL_DOCUMENT_RETRIEVER_NODE] No query, skipping")
        return {}

    print(f"[INTERNATIONAL_DOCUMENT_RETRIEVER_NODE] Retrieving for query: {query}")

    # Emit retriever start event
    callback_handler = InternationalDocumentRetrieverCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "temp_document_retriever"},
        query=query
    )

    try:
        # Use retriever to get chunks (temp tables don't have citation metadata)
        result = _temp_retriever.retrieve_chunks(query, state.safe_session_id, top_k=5)

        if result["status"] == "success":
            chunks = result["chunks"]
            print(f"[INTERNATIONAL_DOCUMENT_RETRIEVER_NODE] ✓ Retrieved {len(chunks)} chunks")

            # For temp documents, we don't have citation metadata
            # Add empty citation objects to maintain compatibility
            for chunk in chunks:
                if 'citation' not in chunk:
                    chunk['citation'] = None

            # Extract content strings for output validation
            doc_context = [chunk.get("content", "") for chunk in chunks if chunk.get("content")]
            # Store full chunk data including metadata for context combination
            doc_chunks_with_metadata = chunks
        else:
            print(f"[INTERNATIONAL_DOCUMENT_RETRIEVER_NODE] ✗ Retrieval failed: {result.get('message', 'Unknown error')}")
            doc_context = []
            doc_chunks_with_metadata = []

        # Emit retriever end event
        callback_handler.on_retriever_end(documents=doc_context)

        # Return validated output with citation metadata
        output_data = DocumentRetrieverNodeOutput(
            doc_context=doc_context,
            doc_chunks_with_metadata=doc_chunks_with_metadata
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[INTERNATIONAL_DOCUMENT_RETRIEVER_NODE] ✗ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return {}