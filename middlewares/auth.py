from functools import wraps
from flask import request, jsonify
from database import Database

db = Database()

def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No authorization token provided'}), 401
            
            token = auth_header.split(' ')[1]
            user = db.verify_session(token)
            
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            if roles and user['role'] not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 