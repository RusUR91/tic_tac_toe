from abc import ABC, abstractmethod
from domain.model.user import User
from web.model.signup_request import SignUpRequest
from web.model.jwt_request import JwtRequest
from web.model.jwt_response import JwtResponse

class UserServiceInterface(ABC):
    @abstractmethod
    def register(self, signup_request: SignUpRequest) -> bool:
        pass

    @abstractmethod
    def authenticate(self, jwt_request: JwtRequest) -> JwtResponse:
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> JwtResponse:
        pass
    
    @abstractmethod
    def refresh_tokens(self, refresh_token: str) -> JwtResponse:
        pass
    
    @abstractmethod
    def get_user_by_uuid(self, uuid: str) -> User:
        pass
    
    @abstractmethod
    def get_user_by_login(self, login: str) -> User:
        pass