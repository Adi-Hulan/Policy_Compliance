"""
Document Retriever Node

Retrieves relevant chunks from processed document.
Specific to company policy graph.
"""

from typing import Dict, Any
from langchain_core.callbacks import BaseCallbackHandler
from agents.chunk_retriever_temp import TempRetriever
from graphs.nodes.models import DocumentRetrieverNodeInput, DocumentRetrieverNodeOutput


class DocumentRetrieverCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit retriever events for document retrieval."""

    def on_retriever_start(self, serialized, query, **kwargs):
        print("[DOCUMENT_RETRIEVER_CALLBACK] Vector search started")

    def on_retriever_end(self, documents, **kwargs):
        print("[DOCUMENT_RETRIEVER_CALLBACK] Vector search completed")


# Shared instance
_temp_retriever = TempRetriever()


def document_retriever_node(state) -> Dict[str, Any]:
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

    if not query or not tmp_file_path:
        print("[DOCUMENT_RETRIEVER_NODE] Missing query or file path, skipping")
        return {}

    print(f"[DOCUMENT_RETRIEVER_NODE] Retrieving from document for query: {query}")

    # Emit retriever start event
    callback_handler = DocumentRetrieverCallbackHandler()
    callback_handler.on_retriever_start(
        serialized={"name": "document_vector_retriever"},
        query=query
    )

    try:
        # Use document processor to retrieve relevant chunks
        safe_session_id = state.safe_session_id
        result = _temp_retriever.retrieve_chunks(query, safe_session_id)

        if result["status"] == "success":
            chunks = result["chunks"]
            print(f"[DOCUMENT_RETRIEVER_NODE] ✓ Retrieved {len(chunks)} chunks")
            # Extract content strings for output validation
            doc_context = [chunk.get("content", "") for chunk in chunks if chunk.get("content")]
        else:
            print("[DOCUMENT_RETRIEVER_NODE] ✗ Retrieval failed")
            doc_context = []

        # Emit retriever end event
        callback_handler.on_retriever_end(documents=doc_context)

        # Return validated output
        output_data = DocumentRetrieverNodeOutput(doc_context=doc_context)
        return output_data.model_dump()

    except Exception as e:
        print(f"[DOCUMENT_RETRIEVER_NODE] ✗ Retrieval failed: {e}")
        return {}