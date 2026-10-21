from domain.service.user_service import UserServiceInterface
from domain.model.user import User
from web.model.signup_request import SignUpRequest
import uuid
import hashlib

class UserServiceImpl(UserServiceInterface):
    def __init__(self, user_repository):
        self.user_repository = user_repository

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

    def authenticate(self, login: str, password: str) -> str:
        user = self.user_repository.get_by_login(login)
        
        if not user:
            raise ValueError("Invalid login or password")
        
        hashed_password = self._hash_password(password)
        if user.password != hashed_password:
            raise ValueError("Invalid login or password")
        
        return user.uuid

    def get_user_by_uuid(self, uuid: str) -> User:
        user = self.user_repository.get_by_uuid(uuid)
        if not user:
            raise ValueError("User not found")
        return user