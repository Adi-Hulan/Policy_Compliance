"""
Document Download Node

Downloads document from provided URL.
Specific to company policy graph.
"""

from typing import Dict, Any
import tempfile
import requests
from langchain_core.callbacks import BaseCallbackHandler
from graphs.nodes.models import DocumentDownloadNodeInput, DocumentDownloadNodeOutput


class DocumentDownloadCallbackHandler(BaseCallbackHandler):
    """Callback handler to emit tool events for document download."""

    def on_tool_start(self, serialized, input_str, **kwargs):
        print("[DOCUMENT_DOWNLOAD_CALLBACK] HTTP request started")

    def on_tool_end(self, output, **kwargs):
        print("[DOCUMENT_DOWNLOAD_CALLBACK] HTTP request completed")


def document_download_node(state) -> Dict[str, Any]:
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
        print("[DOCUMENT_DOWNLOAD_NODE] No document URL, skipping")
        return {}

    print(f"[DOCUMENT_DOWNLOAD_NODE] Downloading from: {url}")

    # Emit tool start event
    callback_handler = DocumentDownloadCallbackHandler()
    callback_handler.on_tool_start(
        serialized={"name": "http_downloader"},
        input_str=url
    )

    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        content = res.content

        print(f"[DOCUMENT_DOWNLOAD_NODE] Downloaded {len(content)} bytes")

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()

        print(f"[DOCUMENT_DOWNLOAD_NODE] ✓ Saved to: {tmp.name}")

        # Emit tool end event
        callback_handler.on_tool_end(output=f"Downloaded {len(content)} bytes to {tmp.name}")

        # Return validated output
        output_data = DocumentDownloadNodeOutput(tmp_file_path=tmp.name)
        return output_data.model_dump()

    except Exception as e:
        print(f"[DOCUMENT_DOWNLOAD_NODE] ✗ Download failed: {e}")
        return {}