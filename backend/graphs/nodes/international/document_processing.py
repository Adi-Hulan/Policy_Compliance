"""
International Policy Document Processing Node

Processes downloaded document and stores in temporary collection.
Specific to international policy graph.
"""

from typing import Dict, Any
import os
from agents.attached_document_processor import DocumentProcessorTemp
from utils.pdf_parser import extract_text_from_pdf
from graphs.nodes.models import DocumentProcessingNodeInput, DocumentProcessingNodeOutput

# Shared instance
_doc_processor = DocumentProcessorTemp()


def international_document_processing_node(state) -> Dict[str, Any]:
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
        print("[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] No file path, skipping")
        return {}

    print(f"[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] Processing file: {tmp_file_path}")

    try:
        # Extract text from PDF
        text = extract_text_from_pdf(tmp_file_path)
        if not text.strip():
            print("[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] ✗ No text extracted from PDF")
            return {}

        print(f"[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] ✓ Extracted {len(text)} characters")

        # Process document into chunks and store in temp table
        result = _doc_processor.process_document(
            file_path=tmp_file_path,
            session_id=state.session_id
        )

        if result["status"] == "success":
            print(f"[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] ✓ Document processed into temp table")
        else:
            print(f"[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] ✗ Document processing failed: {result.get('result', 'Unknown error')}")
            return {}

        # Return validated output
        output_data = DocumentProcessingNodeOutput(
            processed_content=text
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[INTERNATIONAL_DOCUMENT_PROCESSING_NODE] ✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return {}