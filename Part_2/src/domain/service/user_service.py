from abc import ABC, abstractmethod
from domain.model.user import User
from web.model.signup_request import SignUpRequest

class UserServiceInterface(ABC):
    @abstractmethod
    def register(self, signup_request: SignUpRequest) -> bool:
        pass

    @abstractmethod
    def authenticate(self, login: str, password: str) -> str:
        pass
    
    @abstractmethod
    def get_user_by_uuid(self, uuid: str) -> User:
        pass