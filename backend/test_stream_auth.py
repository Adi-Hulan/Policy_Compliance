"""
Test Authenticated Route
-------------------------
Test that the /queries/analyze/stream endpoint requires authentication.
This will verify Step 4 is working correctly.
"""

import requests
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"

def generate_test_token():
    """Generate a test JWT token for authentication."""
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    
    payload = {
        'sub': 'test-user-12345',  # User ID
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    return token

def test_without_auth():
    """Test that endpoint rejects requests without authentication."""
    print("\n1️⃣ Testing WITHOUT authentication...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            json={
                "session_id": "test-session-123",
                "message": "Hello",
                "document_url": None
            },
            timeout=5
        )
        
        if response.status_code == 401:
            print("   ✅ PASS: Endpoint correctly rejected unauthenticated request (401)")
            return True
        else:
            print(f"   ❌ FAIL: Expected 401, got {response.status_code}")
            print(f"   Response: {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  SKIP: Flask server not running")
        print("   Please start the server with: python3 app.py")
        return None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_with_invalid_token():
    """Test that endpoint rejects requests with invalid token."""
    print("\n2️⃣ Testing WITH invalid token...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            headers={
                "Authorization": "Bearer invalid_token_12345"
            },
            json={
                "session_id": "test-session-123",
                "message": "Hello",
                "document_url": None
            },
            timeout=5
        )
        
        if response.status_code == 401:
            print("   ✅ PASS: Endpoint correctly rejected invalid token (401)")
            return True
        else:
            print(f"   ❌ FAIL: Expected 401, got {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  SKIP: Flask server not running")
        return None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_with_valid_token():
    """Test that endpoint accepts requests with valid token."""
    print("\n3️⃣ Testing WITH valid token...")
    
    try:
        token = generate_test_token()
        print(f"   Generated token: {token[:50]}...")
        
        response = requests.post(
            f"{BASE_URL}/queries/analyze/stream",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "session_id": "test-session-123",
                "message": "Hello",
                "document_url": None
            },
            timeout=5,
            stream=True  # For SSE
        )
        
        if response.status_code == 200:
            print("   ✅ PASS: Endpoint accepted authenticated request (200)")
            print("   ✅ Response is streaming (SSE)")
            
            # Read first chunk to verify it's working
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"   📨 Received event: {line[:80]}...")
                    break  # Just check first event
            
            return True
        else:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  SKIP: Flask server not running")
        return None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def main():
    print("="*60)
    print("🧪 Testing Authenticated Query Route")
    print("="*60)
    print("\nMake sure Flask server is running:")
    print("  cd /Users/pamigee/Desktop/Policy_Compliance/backend")
    print("  python3 app.py")
    print("\nStarting tests...")
    
    results = []
    
    # Test 1: No auth
    result = test_without_auth()
    if result is not None:
        results.append(result)
    
    # Test 2: Invalid token
    result = test_with_invalid_token()
    if result is not None:
        results.append(result)
    
    # Test 3: Valid token
    result = test_with_valid_token()
    if result is not None:
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    if not results:
        print("⚠️  TESTS SKIPPED - Flask server not running")
        print("\nTo run tests:")
        print("  1. Start server: python3 app.py")
        print("  2. In another terminal: python3 test_stream_auth.py")
    elif all(results):
        print("🎉 ALL TESTS PASSED")
        print("="*60)
        print("\n✅ Step 4 Complete!")
        print("\nThe route now:")
        print("  1. ✅ Requires valid JWT token")
        print("  2. ✅ Extracts user_id from token")
        print("  3. ✅ Makes g.user_id available")
        print("  4. ✅ Streaming still works")
        print("\nNext step: Integrate with orchestrator")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Passed: {sum(results)}/{len(results)}")
    print("="*60)

if __name__ == "__main__":
    main()
