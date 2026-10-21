from domain.model.user import User
from datasource.model.user_entity import UserEntity

def to_entity(user: User) -> UserEntity:
    return UserEntity(user.uuid, user.login, user.password)

def to_domain(entity: UserEntity) -> User:
    return User(entity.uuid, entity.login, entity.password)