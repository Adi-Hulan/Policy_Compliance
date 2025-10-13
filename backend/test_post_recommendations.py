"""
Simple script to POST an analyzer output JSON into the recommendations endpoint.
Usage:
  # from backend/ folder
  python test_post_recommendations.py analyzer_output.json

If no file is provided the script will exit with usage instructions.

The script expects the analyzer output JSON to contain at least:
{
  "violations": [...],
  "paired_contexts": [...],
  "session_id": "optional-session-id"
}

This will verify the server uses incoming `paired_contexts` rather than fetching fallback contexts.
"""
import sys
import json
import requests

API = "http://127.0.0.1:5000/recommendations/generate"


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_post_recommendations.py <analyzer_output.json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Ensure Content-Type header
    headers = {"Content-Type": "application/json"}

    print(f"Posting {path} to {API} ...")
    r = requests.post(API, json=payload, headers=headers)

    print(f"Status: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


if __name__ == "__main__":
    main()
