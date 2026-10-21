from functools import wraps
from flask import request, jsonify
from web.auth.jwt_provider import JwtProvider


class UserAuthenticator:
    def __init__(self, user_service, jwt_provider: JwtProvider = None):
        self.user_service = user_service
        self.jwt_provider = jwt_provider or JwtProvider()
    
    def _extract_token(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            auth_type, token = auth_header.split(' ', 1)
            if auth_type.lower() != 'bearer':
                return None
            return token
        except Exception:
            return None
    
    def authenticate(self):
        token = self._extract_token()
        
        if not token:
            raise ValueError("Missing or invalid Authorization header")
        
        if not self.jwt_provider.validate_access_token(token):
            raise ValueError("Invalid or expired token")
        
        user_uuid = self.jwt_provider.get_uuid_from_token(token)
        if not user_uuid:
            raise ValueError("Invalid token")
        
        return user_uuid
    
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


def optional_auth(user_authenticator):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_uuid = user_authenticator.authenticate()
                request.user_uuid = user_uuid
            except ValueError:
                request.user_uuid = None
            return f(*args, **kwargs)
        return decorated_function
    return decorator