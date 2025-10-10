"""
Tests for Chat History Endpoints
--------------------------------
Exercises:
- GET /chat/sessions
- GET /chat/sessions/<id>/messages
- DELETE /chat/sessions/<id>

Note: Requires Flask server running locally.
"""

import os
import jwt
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db.repositories.chat_repository import ChatRepository

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"


def generate_token(user_id: str, email: str = "test@example.com") -> str:
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def setup_sample_data(user_id: str) -> str:
    repo = ChatRepository()
    session_id = "11111111-1111-1111-1111-111111111111"
    # Ensure session exists and belongs to user
    repo.get_or_create_session(session_id, user_id, title="History Test Chat")
    # Seed a couple messages
    repo.save_message(session_id, "user", "Hello")
    repo.save_message(session_id, "assistant", "Hi there")
    return session_id


def test_get_sessions(token: str):
    res = requests.get(
        f"{BASE_URL}/chat/sessions", headers={"Authorization": f"Bearer {token}"}, timeout=10
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "sessions" in data
    print(f"Sessions count: {len(data['sessions'])}")


def test_get_messages(token: str, session_id: str):
    res = requests.get(
        f"{BASE_URL}/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("session", {}).get("id") == session_id
    assert isinstance(data.get("messages"), list)
    print(f"Messages count: {len(data['messages'])}")


def test_delete_session(token: str, session_id: str):
    res = requests.delete(
        f"{BASE_URL}/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("status") == "deleted"
    print("Session deleted")


def main():
    print("=" * 60)
    print("🧪 Testing Chat History Endpoints")
    print("=" * 60)
    print("Make sure Flask server is running: python3 app.py")
    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    token = generate_token(user_id)
    session_id = setup_sample_data(user_id)

    test_get_sessions(token)
    test_get_messages(token, session_id)
    test_delete_session(token, session_id)
    print("✅ All chat history endpoint tests completed")


if __name__ == "__main__":
    main()





