"""
International Policy Document Download Node

Downloads document from provided URL.
Specific to international policy graph.
"""

from typing import Dict, Any
import tempfile
import requests
from langchain_core.callbacks import BaseCallbackHandler
from graphs.nodes.models import DocumentDownloadNodeInput, DocumentDownloadNodeOutput


class InternationalDocumentDownloadCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit tool events for document download."""

    def on_tool_start(self, serialized, input_str, **kwargs):
        print("[INTERNATIONAL_DOCUMENT_DOWNLOAD_CALLBACK] HTTP request started")

    def on_tool_end(self, output, **kwargs):
        print("[INTERNATIONAL_DOCUMENT_DOWNLOAD_CALLBACK] HTTP request completed")


def international_document_download_node(state) -> Dict[str, Any]:
    """
    Download document from provided URL.

    Args:
        state: Current graph state

    Returns:
        Dict with tmp_file_path (path to downloaded file)

    Streams:
        - on_tool_start: HTTP request started
        - on_tool_end: HTTP request completed
        - stage: Download progress
    """
    # Validate inputs using Pydantic model
    try:
        input_data = DocumentDownloadNodeInput(
            document_url=state.document_url
        )
    except Exception as e:
        raise ValueError(f"Document download input validation failed: {e}")

    url = input_data.document_url
    if not url:
        print("[INTERNATIONAL_DOCUMENT_DOWNLOAD_NODE] No document URL, skipping")
        return {}

    print(f"[INTERNATIONAL_DOCUMENT_DOWNLOAD_NODE] Downloading from: {url}")

    # Emit tool start event
    callback_handler = InternationalDocumentDownloadCallbackHandler()
    callback_handler.on_tool_start(
        serialized={"name": "http_request"},
        input_str=f"GET {url}"
    )

    try:
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name

        print(f"[INTERNATIONAL_DOCUMENT_DOWNLOAD_NODE] ✓ Downloaded to: {tmp_file_path}")

        # Emit tool end event
        callback_handler.on_tool_end(output=f"Downloaded {len(response.content)} bytes")

        # Return validated output
        output_data = DocumentDownloadNodeOutput(
            tmp_file_path=tmp_file_path
        )
        return output_data.model_dump()

    except Exception as e:
        print(f"[INTERNATIONAL_DOCUMENT_DOWNLOAD_NODE] ✗ Download failed: {e}")
        return {}