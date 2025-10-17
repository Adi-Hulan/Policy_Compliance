# middleware/auth.py (your existing file - UPDATED)
from functools import wraps
from flask import request, jsonify, g
from .shared_auth import verify_jwt_token  # Import shared function

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'No authorization header',
                'message': 'Authorization header is required'
            }), 401
        
        try:
            # Extract token from "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid authorization header', 
                    'message': 'Format must be: Bearer <token>'
                }), 401
            
            token = parts[1]
            
            # Use shared auth function instead of duplicate logic
            user_data = verify_jwt_token(token)
            
            # Set in Flask g object (same as before)
            g.user_id = user_data['user_id']
            g.user_email = user_data['user_email'] 
            g.user_role = user_data['user_role']
            
            return f(*args, **kwargs)
            
        except ValueError as e:  # Now catching ValueError from shared function
            return jsonify({
                'error': 'Authentication failed',
                'message': str(e)
            }), 401
        except Exception as e:
            print(f"[AUTH ERROR] {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to authenticate request'
            }), 401
    
    return decorated_function


def require_role(required_role):
    """
    Decorator that checks if user has required role.
    Must be used AFTER @require_auth decorator.
    
    Role hierarchy: user < analyst < admin
    
    Usage:
        @app.route('/admin-only')
        @require_auth
        @require_role('admin')
        def admin_route():
            return jsonify({'message': 'Admin access granted'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = getattr(g, 'user_role', 'user')
            
            # Define role hierarchy
            role_hierarchy = {
                'user': 0,
                'analyst': 1,
                'admin': 2
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'This action requires {required_role} role or higher',
                    'your_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def get_current_user_id():
    """
    Helper function to get current user ID from Flask g object.
    Returns None if not authenticated.
    """
    return getattr(g, 'user_id', None)


def get_current_user_email():
    """
    Helper function to get current user email from Flask g object.
    Returns None if not authenticated.
    """
    return getattr(g, 'user_email', None)


def get_current_user_role():
    """
    Helper function to get current user role from Flask g object.
    Returns 'user' as default if not authenticated.
    """
    return getattr(g, 'user_role', 'user')
