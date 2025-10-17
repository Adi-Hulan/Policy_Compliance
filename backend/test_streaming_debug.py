#!/usr/bin/env python3
"""
Test streaming endpoint with debug prints
"""
import requests
import json
import time
import threading
import subprocess
import sys
import os

def start_server():
    """Start the FastAPI server in a separate process"""
    os.chdir('/Users/pamigee/Desktop/Policy_Compliance/backend')
    cmd = ['python3', 'app_fastapi.py']
    return subprocess.Popen(cmd)  # Don't capture output, let it print to console

def test_streaming():
    """Test the streaming endpoint"""
    time.sleep(3)  # Wait for server to start

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzNDUiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJpYXQiOjE3NjAyOTg3OTcsImV4cCI6MTc2MDMwMjM5N30.7X8igYKEP9TyhlXtQv9pO9WV_s5xuzW5xVpHK-sYt1Y"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",  # Valid UUID
        "message": "What is the company PTO policy?"
    }

    try:
        print("Making request to streaming endpoint...")
        response = requests.post(
            "http://localhost:8000/queries/analyze/stream",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )

        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            print("Reading SSE stream...")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Received: {line}")
                    if "end" in line or "error" in line:
                        break
        else:
            print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting server...")
    server_process = start_server()

    try:
        test_streaming()
    finally:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()