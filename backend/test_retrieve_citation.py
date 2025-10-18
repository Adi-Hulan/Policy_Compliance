import pytest
from fastapi.testclient import TestClient
from app_fastapi import app

# Suppress AsyncClient shutdown errors by monkey-patching __del__
try:
    from google.genai.client import AsyncClient
    AsyncClient.__del__ = lambda self: None
except ImportError:
    pass

client = TestClient(app)

def test_retrieve_citation():
    # Mock data for testing
    mock_file_path = "/Users/pamigee/Desktop/Policy_Compliance/backend/uploads/Employee-Handbook.pdf"
    mock_content = "This is a test document. It contains multiple sentences for testing."

    # Create a temporary mock file
    with open(mock_file_path, "w", encoding="utf-8") as mock_file:
        mock_file.write(mock_content)

    # Define test parameters
    char_start = 10
    char_end = 34

    # Expected citation text
    expected_citation = mock_content[char_start:char_end]

    print("--- Test Retrieve Citation ---")
    print(f"Mock file path: {mock_file_path}")
    print(f"Mock content: {mock_content}")
    print(f"Character range: {char_start} to {char_end}")
    print(f"Expected citation: {expected_citation}")

    print("--- Sending Request ---")
    print(f"GET /retrieve-citation?file_path={mock_file_path}&char_start={char_start}&char_end={char_end}")

    # Make a GET request to the endpoint
    response = client.get(
        f"/retrieve-citation?file_path={mock_file_path}&char_start={char_start}&char_end={char_end}"
    )

    print("--- Response ---")
    print(f"Status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")

    # Validate the response
    assert response.status_code == 200
    assert response.json() == {"citation_text": expected_citation}

    # Clean up the mock file
    import os
    os.remove(mock_file_path)