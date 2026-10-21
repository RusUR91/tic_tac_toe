from functools import wraps
from flask import request, jsonify
import base64

class UserAuthenticator:
    def __init__(self, user_service):
        self.user_service = user_service
    
    def _extract_auth_header(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None, None
        
        try:
            auth_type, auth_token = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return None, None
            
            decoded = base64.b64decode(auth_token).decode('utf-8')
            login, password = decoded.split(':', 1)
            return login, password
        except Exception:
            return None, None
    
    def authenticate(self):
        login, password = self._extract_auth_header()
        
        if not login or not password:
            raise ValueError("Invalid authorization header")
        
        try:
            user_uuid = self.user_service.authenticate(login, password)
            return user_uuid
        except ValueError as e:
            raise ValueError(str(e))
    
    def get_authenticated_user(self):
        user_uuid = self.authenticate()
        return self.user_service.get_user_by_uuid(user_uuid)

def require_auth(user_authenticator):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_uuid = user_authenticator.authenticate()
                request.user_uuid = user_uuid
                return f(*args, **kwargs)
            except ValueError as e:
                return jsonify({'error': str(e)}), 401
        return decorated_function
    return decorator

def public_endpoint(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function