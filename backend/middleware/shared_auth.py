# shared_auth.py
import jwt
import os
from typing import Dict, Optional

def verify_jwt_token(token: str) -> Dict:
    """
    Shared JWT verification used by both Flask and FastAPI
    Returns user data dict if valid, raises ValueError if invalid
    """
    if not token:
        raise ValueError("No token provided")
    
    try:
        # Your existing JWT logic - copied from Flask decorator
        decoded = jwt.decode(
            token,
            os.getenv('SUPABASE_JWT_SECRET'),
            algorithms=['HS256'],
            audience='authenticated'
        )
        
        # Extract user information (same as your Flask logic)
        user_id = decoded.get('sub')  # Subject = User ID
        user_email = decoded.get('email')
        
        # Get role from user_metadata or app_metadata
        user_metadata = decoded.get('user_metadata', {})
        app_metadata = decoded.get('app_metadata', {})
        user_role = user_metadata.get('role') or app_metadata.get('role') or 'user'
        
        print(f"[SHARED_AUTH] User authenticated: {user_id} ({user_email}) - Role: {user_role}")
        
        return {
            'user_id': user_id,
            'user_email': user_email,
            'user_role': user_role
        }
        
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"[SHARED_AUTH ERROR] {str(e)}")
        raise ValueError("Authentication failed")