"""
Test Chat Persistence
---------------------
Verify that sending a message through the streaming route persists both the
user and assistant messages to the database.

Run:
  cd /Users/pamigee/Desktop/Policy_Compliance/backend
  python3 test_chat_persistence.py
"""

import os
import time
import uuid
import jwt
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import repository to verify DB state
from db.repositories.chat_repository import ChatRepository

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"


def generate_test_token(user_id: str, email: str = "test@example.com") -> str:
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    assert jwt_secret, "SUPABASE_JWT_SECRET not configured"
    payload = {
        'sub': user_id,
        'email': email,
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


def test_persist_messages():
    print("\n=== Test: Persist Messages ===")
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    token = generate_test_token(user_id)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "session_id": session_id,
        "message": "What is our vacation policy?",
    }

    print(f"Posting streaming request with session_id={session_id}")
    try:
        # Open SSE stream and read until we receive the end signal
        with requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120,
        ) as resp:
            if resp.status_code != 200:
                print(f"❌ Unexpected status: {resp.status_code} - {resp.text[:200]}")
                return False
            buffer = []
            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    break
                if not line:
                    # end of event; parse accumulated data lines
                    data_parts = [l[len("data:"):].lstrip() for l in buffer if l.startswith("data:")]
                    if data_parts:
                        try:
                            payload_obj = None
                            # join lines (server sends one JSON per event)
                            joined = "\n".join(data_parts).strip()
                            payload_obj = __import__('json').loads(joined)
                            if isinstance(payload_obj, dict) and payload_obj.get("type") == "end":
                                break
                        except Exception:
                            pass
                    buffer = []
                    continue
                buffer.append(line)
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask server not running; start with: python3 app.py")
        return None

    # Small wait to ensure DB writes are committed
    time.sleep(1.0)

    # Verify messages in DB
    repo = ChatRepository()
    msgs = repo.get_messages(session_id)
    if len(msgs) < 2:
        print(f"❌ Expected at least 2 messages, found {len(msgs)}")
        return False

    roles = [m['role'] for m in msgs]
    if 'user' not in roles or 'assistant' not in roles:
        print(f"❌ Expected roles to include both 'user' and 'assistant', got {roles}")
        return False

    print("✅ Messages persisted: both user and assistant present")
    return True


if __name__ == "__main__":
    result = test_persist_messages()
    if result is True:
        print("\n🎉 Chat persistence test PASSED")
    elif result is False:
        print("\n❌ Chat persistence test FAILED")
    else:
        print("\n⚠️  Chat persistence test SKIPPED")


