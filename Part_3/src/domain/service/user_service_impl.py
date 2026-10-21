from domain.service.user_service import UserServiceInterface
from domain.model.user import User
from web.model.signup_request import SignUpRequest
from web.model.jwt_request import JwtRequest
from web.model.jwt_response import JwtResponse
from web.model.refresh_jwt_request import RefreshJwtRequest
from web.auth.jwt_provider import JwtProvider
import uuid
import hashlib


class UserServiceImpl(UserServiceInterface):
    def __init__(self, user_repository, jwt_provider: JwtProvider = None):
        self.user_repository = user_repository
        self.jwt_provider = jwt_provider or JwtProvider()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _validate_login(self, login: str) -> bool:
        return login and len(login) >= 3

    def _validate_password(self, password: str) -> bool:
        return password and len(password) >= 6

    def register(self, signup_request: SignUpRequest) -> bool:
        if not self._validate_login(signup_request.login):
            raise ValueError("Login must be at least 3 characters long")
        
        if not self._validate_password(signup_request.password):
            raise ValueError("Password must be at least 6 characters long")
        
        existing_user = self.user_repository.get_by_login(signup_request.login)
        if existing_user:
            raise ValueError("User with this login already exists")
        
        user_uuid = str(uuid.uuid4())
        hashed_password = self._hash_password(signup_request.password)
        user = User(user_uuid, signup_request.login, hashed_password)
        
        self.user_repository.save(user)
        return True

    def authenticate(self, jwt_request: JwtRequest) -> JwtResponse:
        user = self.user_repository.get_by_login(jwt_request.login)
        
        if not user:
            raise ValueError("Invalid login or password")
        
        hashed_password = self._hash_password(jwt_request.password)
        if user.password != hashed_password:
            raise ValueError("Invalid login or password")
        
        access_token, refresh_token = self.jwt_provider.generate_tokens(user)
        
        return JwtResponse('Bearer', access_token, refresh_token)

    def refresh_access_token(self, refresh_token: str) -> JwtResponse:
        if not self.jwt_provider.validate_refresh_token(refresh_token):
            raise ValueError("Invalid refresh token")
        
        user_uuid = self.jwt_provider.get_uuid_from_token(refresh_token)
        if not user_uuid:
            raise ValueError("Invalid refresh token")
        
        user = self.get_user_by_uuid(user_uuid)
        
        access_token = self.jwt_provider.generate_access_token(user)
        refresh_token_new = self.jwt_provider.generate_refresh_token(user)
        
        return JwtResponse('Bearer', access_token, refresh_token_new)

    def refresh_tokens(self, refresh_token: str) -> JwtResponse:
        if not self.jwt_provider.validate_refresh_token(refresh_token):
            raise ValueError("Invalid refresh token")
        
        user_uuid = self.jwt_provider.get_uuid_from_token(refresh_token)
        if not user_uuid:
            raise ValueError("Invalid refresh token")
        
        user = self.get_user_by_uuid(user_uuid)
        
        access_token, refresh_token_new = self.jwt_provider.generate_tokens(user)
        
        return JwtResponse('Bearer', access_token, refresh_token_new)

    def get_user_by_uuid(self, uuid: str) -> User:
        user = self.user_repository.get_by_uuid(uuid)
        if not user:
            raise ValueError("User not found")
        return user

    def get_user_by_login(self, login: str) -> User:
        user = self.user_repository.get_by_login(login)
        if not user:
            raise ValueError("User not found")
        return user