from database import db
from datasource.model.user_entity import UserEntity
from datasource.mapper import user_mapper
from domain.model.user import User
from typing import Optional

class UserRepository:
    def __init__(self):
        pass

    def save(self, user: User) -> None:
        entity = user_mapper.to_entity(user)
        existing = db.session.get(UserEntity, entity.uuid)
        
        if existing:
            existing.login = entity.login
            existing.password = entity.password
        else:
            db.session.add(entity)
        
        db.session.commit()

    def get_by_uuid(self, uuid: str) -> Optional[User]:
        entity = db.session.get(UserEntity, uuid)
        if entity is None:
            return None
        return user_mapper.to_domain(entity)

    def get_by_login(self, login: str) -> Optional[User]:
        entity = db.session.query(UserEntity).filter_by(login=login).first()
        if entity is None:
            return None
        return user_mapper.to_domain(entity)