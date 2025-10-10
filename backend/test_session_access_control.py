"""
Test Session Access Control
---------------------------
Verify that a user cannot access another user's session id via the streaming route.

Run:
  cd /Users/pamigee/Desktop/Policy_Compliance/backend
  python3 test_session_access_control.py
"""

import os
import uuid
import jwt
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

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


def test_cross_user_forbidden():
    print("\n=== Test: Cross-user Access Forbidden (403) ===")
    # Create a session for user A
    session_id = str(uuid.uuid4())
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())

    repo = ChatRepository()
    repo.get_or_create_session(session_id=session_id, user_id=user_a, title="Access Control Test")

    # Attempt to use user B's token with user A's session
    token_b = generate_test_token(user_b)
    headers = {
        "Authorization": f"Bearer {token_b}",
        "Content-Type": "application/json",
    }
    payload = {
        "session_id": session_id,
        "message": "Hello",
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            headers=headers,
            json=payload,
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask server not running; start with: python3 app.py")
        return None

    if resp.status_code == 403:
        print("✅ Received 403 Forbidden for cross-user session access")
        return True
    else:
        print(f"❌ Expected 403, got {resp.status_code}. Body: {resp.text[:200]}")
        return False


if __name__ == "__main__":
    result = test_cross_user_forbidden()
    if result is True:
        print("\n🎉 Session access control test PASSED")
    elif result is False:
        print("\n❌ Session access control test FAILED")
    else:
        print("\n⚠️  Session access control test SKIPPED")


