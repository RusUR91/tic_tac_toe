from flask_jwt_extended import create_access_token, create_refresh_token, decode_token, get_jwt_identity
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import InvalidTokenError
from typing import Optional
from domain.model.user import User
import os
from datetime import timedelta
from flask import current_app


class JwtProvider:
    def __init__(self):
        self.access_token_expires = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15)))
        self.refresh_token_expires = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 7)))
    
    def generate_access_token(self, user: User) -> str:
        return create_access_token(
            identity=user.uuid,
            expires_delta=self.access_token_expires
        )
    
    def generate_refresh_token(self, user: User) -> str:
        return create_refresh_token(
            identity=user.uuid,
            expires_delta=self.refresh_token_expires
        )
    
    def generate_tokens(self, user: User) -> tuple:
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)
        return access_token, refresh_token
    
    def validate_access_token(self, token: str) -> bool:
        try:
            decode_token(token, allow_expired=False)
            return True
        except (InvalidTokenError, JWTExtendedException):
            return False
    
    def validate_refresh_token(self, token: str) -> bool:
        try:
            decode_token(token, allow_expired=False)
            return True
        except (InvalidTokenError, JWTExtendedException):
            return False
    
    def get_uuid_from_token(self, token: str) -> Optional[str]:
        try:
            decoded = decode_token(token, allow_expired=False)
            return decoded.get('sub')
        except (InvalidTokenError, JWTExtendedException):
            return None
    
    def get_uuid_from_access_token(self) -> Optional[str]:
        try:
            return get_jwt_identity()
        except Exception:
            return None