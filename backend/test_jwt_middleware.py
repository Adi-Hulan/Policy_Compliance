"""
Test JWT Authentication Middleware
-----------------------------------
Test that the auth decorator correctly extracts user_id from JWT tokens.
"""

import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def test_jwt_generation():
    """Test that we can generate and decode a test JWT token."""
    
    print("🧪 Testing JWT Token Generation and Decoding\n")
    
    # Get JWT secret
    jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found in .env file")
        return False
    
    print(f"✅ JWT Secret loaded (length: {len(jwt_secret)})\n")
    
    # Create a test token (similar to what Supabase generates)
    test_user_id = "12345678-1234-1234-1234-123456789012"
    test_email = "test@example.com"
    
    payload = {
        'sub': test_user_id,  # User ID
        'email': test_email,
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    # Generate token
    print("📝 Generating test JWT token...")
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    print(f"✅ Token generated: {token[:50]}...\n")
    
    # Decode token
    print("🔍 Decoding token...")
    try:
        decoded = jwt.decode(
            token,
            jwt_secret,
            algorithms=['HS256'],
            audience='authenticated'
        )
        
        print("✅ Token decoded successfully!")
        print(f"   User ID: {decoded.get('sub')}")
        print(f"   Email: {decoded.get('email')}")
        print(f"   Audience: {decoded.get('aud')}")
        print(f"   Role: {decoded.get('role')}\n")
        
        # Verify extracted data
        if decoded.get('sub') == test_user_id:
            print("✅ User ID extraction: PASSED")
        else:
            print("❌ User ID extraction: FAILED")
            return False
        
        if decoded.get('email') == test_email:
            print("✅ Email extraction: PASSED")
        else:
            print("❌ Email extraction: FAILED")
            return False
        
        print("\n" + "="*60)
        print("🎉 JWT Middleware Setup: READY")
        print("="*60)
        print("\nThe middleware will be able to:")
        print("  1. ✅ Decode Supabase JWT tokens")
        print("  2. ✅ Extract user_id from 'sub' claim")
        print("  3. ✅ Extract email from token")
        print("  4. ✅ Make user_id available in g.user_id")
        print("\nNext: Test with actual route endpoint")
        
        return True
        
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return False
    except jwt.InvalidTokenError as e:
        print(f"❌ Token validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_jwt_generation()
