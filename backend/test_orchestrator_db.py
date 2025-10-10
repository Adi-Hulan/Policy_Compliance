"""
Test Orchestrator Database Integration
--------------------------------------
Test that the Orchestrator loads and saves history from the database.
"""
import uuid
from orchestrator.orchestrator import Orchestrator


def test_orchestrator_db():
    print("\n🧪 Testing Orchestrator Database Integration\n")
    orchestrator = Orchestrator()
    test_user_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    print(f"Test User ID: {test_user_id}")
    print(f"Test Session ID: {test_session_id}\n")

    # 1️⃣ Test: New session should return only system message
    print("1️⃣ Testing new session loads only system message...")
    history = orchestrator.get_session_history(test_session_id, test_user_id)
    if len(history) == 1 and history[0].type == 'system':
        print("   ✅ PASS: New session returns system message only")
    else:
        print("   ❌ FAIL: Unexpected history for new session")
        return

    # 2️⃣ Test: Save a user and assistant message
    print("\n2️⃣ Testing saving messages to database...")
    user_msg = "Hello, this is a test from orchestrator!"
    ai_msg = "Hi! This is the assistant's reply."
    orchestrator.update_session_history(test_session_id, test_user_id, user_msg, ai_msg)
    print("   ✅ Messages saved.")

    # 3️⃣ Test: Load history for existing session
    print("\n3️⃣ Testing loading history for existing session...")
    history = orchestrator.get_session_history(test_session_id, test_user_id)
    if len(history) == 2:
        print(f"   ✅ PASS: Loaded {len(history)} messages (user + assistant)")
        print("   Messages:")
        for msg in history:
            print(f"      - {msg.type}: {msg.content[:40]}")
    else:
        print(f"   ❌ FAIL: Expected 2 messages, got {len(history)}")
        return

    # 4️⃣ Test: New session for same user is independent
    print("\n4️⃣ Testing new session for same user is independent...")
    new_session_id = str(uuid.uuid4())
    history2 = orchestrator.get_session_history(new_session_id, test_user_id)
    if len(history2) == 1 and history2[0].type == 'system':
        print("   ✅ PASS: New session is independent and returns system message only")
    else:
        print("   ❌ FAIL: New session is not independent")
        return

    print("\n" + "="*60)
    print("🎉 Orchestrator DB Integration: ALL TESTS PASSED")
    print("="*60)

if __name__ == "__main__":
    test_orchestrator_db()
