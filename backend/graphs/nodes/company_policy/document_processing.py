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
        # Extract text from PDF
        text_content = extract_text_from_pdf(tmp_file_path)

        print(f"[DOCUMENT_PROCESSING_NODE] ✓ Extracted {len(text_content)} characters")

        # Clean up temp file
        try:
            os.unlink(tmp_file_path)
            print(f"[DOCUMENT_PROCESSING_NODE] ✓ Cleaned up temp file")
        except Exception as e:
            print(f"[DOCUMENT_PROCESSING_NODE] Warning: Could not clean up temp file: {e}")

        # Return validated output
        output_data = DocumentProcessingNodeOutput(processed_content=text_content)
        return output_data.model_dump()

    except Exception as e:
        print(f"[DOCUMENT_PROCESSING_NODE] ✗ Processing failed: {e}")
        return {}