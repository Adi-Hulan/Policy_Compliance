#!/usr/bin/env python3
"""
Simple SSE test client for the `/queries/analyze/stream` endpoint.

Usage:
  # activate the venv first
  cd /Users/pamigee/Desktop/Policy_Compliance && . .venv/bin/activate
  cd backend
  python3 test_stream_client.py

You can pass args:
  --url   FULL_URL    (default: http://127.0.0.1:5000/queries/analyze/stream)
  --session SESSION   (default: test-session-1)
  --message MESSAGE   (default: "what is the company pto policy?")

The script sends a JSON POST and prints every SSE "data:" event it receives.
"""
import argparse
import json
import requests
import sys


def parse_sse_lines(iterable):
    """Simple SSE parser: yields event data strings for each complete event."""
    buffer_lines = []
    for raw_line in iterable:
        if raw_line is None:
            break
        # requests.iter_lines yields bytes or str depending on decode_unicode
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        # Keep the raw line for printing/debugging
        yield ("raw", line)

def run(url, session_id, message):
    headers = {"Content-Type": "application/json"}
    payload = {"session_id": session_id, "message": message}

    print(f"Posting to {url!s} with session_id={session_id!s}")

    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            print(f"Connected: status={resp.status_code}")

            event_lines = []
            # iterate over the raw lines as they arrive
            for raw_line in resp.iter_lines(decode_unicode=True):
                # print raw line immediately
                if raw_line == "":
                    # empty line indicates end of an SSE event
                    if event_lines:
                        # collect only 'data:' lines
                        data_parts = []
                        for l in event_lines:
                            if l.startswith("data:"):
                                data_parts.append(l[len("data:"):].lstrip())
                        full = "\n".join(data_parts).strip()
                        print("\n--- SSE EVENT ---")
                        print("raw event lines:")
                        for l in event_lines:
                            print(l)
                        print("parsed payload:\n", full)
                        # try to pretty print JSON payloads
                        try:
                            obj = json.loads(full)
                            print("parsed json:")
                            print(json.dumps(obj, indent=2))
                        except Exception:
                            pass
                        event_lines = []
                    continue

                # print the streaming raw fragment
                print(f"< {raw_line}")
                event_lines.append(raw_line)

            # If we exit the loop, print any leftover event_lines
            if event_lines:
                print("\n--- FINAL/LEFTOVER SSE EVENT ---")
                for l in event_lines:
                    print(l)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:5000/queries/analyze/stream")
    p.add_argument("--session", default="test-session-1")
    p.add_argument("--message", default="what is the company pto policy?")
    args = p.parse_args()
    run(args.url, args.session, args.message)


if __name__ == "__main__":
    main()
