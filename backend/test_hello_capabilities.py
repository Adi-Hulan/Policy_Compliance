"""
Ad-hoc test: send "hello what can you do" and verify persistence.

Run:
  cd /Users/pamigee/Desktop/Policy_Compliance/backend
  python3 test_hello_capabilities.py
"""

import os
import uuid
import time
import jwt
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from db.repositories.chat_repository import ChatRepository

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"


def generate_test_token(user_id: str, email: str = "tester@example.com") -> str:
    secret = os.getenv("SUPABASE_JWT_SECRET")
    assert secret, "SUPABASE_JWT_SECRET not configured"
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def run_test():
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
        "message": "hello what can you do",
    }

    print(f"Posting SSE to /queries/analyze/stream with session={session_id}")
    try:
        with requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120,
        ) as resp:
            if resp.status_code != 200:
                print(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
                return False
            buffer = []
            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    break
                if not line:
                    data_parts = [l[len("data:"):].lstrip() for l in buffer if l.startswith("data:")]
                    buffer = []
                    if not data_parts:
                        continue
                    try:
                        joined = "\n".join(data_parts).strip()
                        evt = json.loads(joined)
                        if isinstance(evt, dict) and evt.get("type") == "end":
                            break
                    except Exception:
                        pass
                    continue
                buffer.append(line)
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running on 5000. Start with: python3 app.py")
        return None

    # Give DB a moment to commit
    time.sleep(1.0)

    repo = ChatRepository()
    msgs = repo.get_messages(session_id)
    print(f"Found {len(msgs)} messages in DB for session {session_id}")
    if len(msgs) < 2:
        print("❌ Expected at least 2 messages (user + assistant)")
        return False
    roles = [m["role"] for m in msgs]
    if not ("user" in roles and "assistant" in roles):
        print(f"❌ Missing expected roles. Roles present: {roles}")
        return False

    # Print last two messages for sanity
    last_two = msgs[-2:]
    for i, m in enumerate(last_two, 1):
        preview = (m["content"] or "")[:120].replace("\n", " ")
        print(f"[{i}] {m['role']}: {preview}")

    print("✅ Chat completed and messages persisted")
    return True


if __name__ == "__main__":
    ok = run_test()
    if ok is True:
        print("\n🎉 Test PASSED")
    elif ok is False:
        print("\n❌ Test FAILED")
    else:
        print("\n⚠️  Test SKIPPED")


