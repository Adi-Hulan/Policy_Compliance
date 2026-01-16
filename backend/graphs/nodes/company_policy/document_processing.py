"""
Document Processing Node

Processes downloaded document and stores in temporary collection.
Specific to company policy graph.
"""

from typing import Dict, Any
import os
from agents.attached_document_processor import DocumentProcessorTemp
from utils.pdf_parser import extract_text_from_pdf
from graphs.nodes.models import DocumentProcessingNodeInput, DocumentProcessingNodeOutput

# Shared instance
_doc_processor = DocumentProcessorTemp()


def document_processing_node(state) -> Dict[str, Any]:
    """
    Process uploaded document and extract text content.

    Args:
        state: Current graph state

    Returns:
        Dict with processed_content (extracted text)

    Streams:
        - document_processing_start: Processing initiated
        - document_processing_progress: Processing progress updates
        - document_processing_complete: Processing finished
    """
    # Validate inputs using Pydantic model
    try:
        input_data = DocumentProcessingNodeInput(
            tmp_file_path=state.tmp_file_path
        )
    except Exception as e:
        raise ValueError(f"Document processing input validation failed: {e}")

    tmp_file_path = input_data.tmp_file_path

    if not tmp_file_path:
        print("[DOCUMENT_PROCESSING_NODE] No file path, skipping")
        return {}

    print(f"[DOCUMENT_PROCESSING_NODE] Processing file: {tmp_file_path}")

    try:
        # Use the shared DocumentProcessorTemp to process and persist the document into
        # the temporary DB table (temp_documents_{safe_session_id}). This ensures
        # subsequent retriever nodes can query the temp table for chunks.
        safe_session_id = getattr(state, 'safe_session_id', None)
        if not safe_session_id:
            print("[DOCUMENT_PROCESSING_NODE] ✗ Missing safe_session_id, cannot insert into temp collection")
            return {}

        result = _doc_processor.process(tmp_file_path, safe_session_id)

        if result.get("status") == "success":
            # The processor inserts chunks into the temp table; use its message as processed_content
            processed_content = result.get("result", "Document processed successfully")
            print(f"[DOCUMENT_PROCESSING_NODE] ✓ Document processed into temp table: {result.get('collection_name')}")
        else:
            processed_content = result.get("result", "Document processing failed")
            print(f"[DOCUMENT_PROCESSING_NODE] ✗ Document processing reported error: {processed_content}")

        # Clean up temp file (processor already read it)
        try:
            os.unlink(tmp_file_path)
            print(f"[DOCUMENT_PROCESSING_NODE] ✓ Cleaned up temp file")
        except Exception as e:
            print(f"[DOCUMENT_PROCESSING_NODE] Warning: Could not clean up temp file: {e}")

        # Return validated output
        output_data = DocumentProcessingNodeOutput(processed_content=processed_content)
        return output_data.model_dump()

    except Exception as e:
        print(f"[DOCUMENT_PROCESSING_NODE] ✗ Processing failed: {e}")
        return {}