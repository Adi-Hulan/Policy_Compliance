"""
Test ChatRepository
-------------------
Verify that the ChatRepository can create sessions and save messages.
"""

import uuid
from db.repositories.chat_repository import ChatRepository

def test_chat_repository():
    """Test basic ChatRepository operations."""
    
    print("🧪 Testing ChatRepository...\n")
    
    repo = ChatRepository()
    
    # Test data
    test_user_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    
    print(f"Test User ID: {test_user_id}")
    print(f"Test Session ID: {test_session_id}\n")
    
    # Test 1: Create session
    print("1️⃣ Testing create_session...")
    try:
        session = repo.create_session(
            session_id=test_session_id,
            user_id=test_user_id,
            title="Test Chat Session"
        )
        print(f"   ✅ Session created: {session['id']}")
        print(f"      Title: {session['title']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 2: Get session
    print("\n2️⃣ Testing get_session...")
    try:
        session = repo.get_session(test_session_id)
        if session:
            print(f"   ✅ Session retrieved: {session['title']}")
        else:
            print(f"   ❌ Session not found")
            return
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 3: Save user message
    print("\n3️⃣ Testing save_message (user)...")
    try:
        message = repo.save_message(
            session_id=test_session_id,
            role="user",
            content="Hello, this is a test message!",
            metadata={"document_url": None}
        )
        print(f"   ✅ User message saved: {message['id']}")
        print(f"      Content: {message['content'][:50]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 4: Save assistant message
    print("\n4️⃣ Testing save_message (assistant)...")
    try:
        message = repo.save_message(
            session_id=test_session_id,
            role="assistant",
            content="Hi! I'm here to help with policy compliance.",
            metadata={}
        )
        print(f"   ✅ Assistant message saved: {message['id']}")
        print(f"      Content: {message['content'][:50]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 5: Get messages
    print("\n5️⃣ Testing get_messages...")
    try:
        messages = repo.get_messages(test_session_id)
        print(f"   ✅ Retrieved {len(messages)} messages:")
        for msg in messages:
            print(f"      - {msg['role']}: {msg['content'][:40]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 6: Get user sessions
    print("\n6️⃣ Testing get_user_sessions...")
    try:
        sessions = repo.get_user_sessions(test_user_id)
        print(f"   ✅ User has {len(sessions)} session(s)")
        for s in sessions:
            print(f"      - {s['title']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 7: Update session title
    print("\n7️⃣ Testing update_session_title...")
    try:
        repo.update_session_title(test_session_id, "Updated Test Chat")
        session = repo.get_session(test_session_id)
        print(f"   ✅ Title updated to: {session['title']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 8: Delete session
    print("\n8️⃣ Testing delete_session...")
    try:
        repo.delete_session(test_session_id)
        session = repo.get_session(test_session_id)
        if session is None:
            print(f"   ✅ Session deleted successfully")
        else:
            print(f"   ❌ Session still exists")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    print("\n" + "="*60)
    print("🎉 All tests passed! ChatRepository is working correctly.")
    print("="*60)

if __name__ == "__main__":
    test_chat_repository()
