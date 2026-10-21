from database import db
from sqlalchemy.orm import Mapped, mapped_column

class UserEntity(db.Model):
    __tablename__ = 'users'
    
    uuid: Mapped[str] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    
    def __init__(self, uuid: str, login: str, password: str):
        self.uuid = uuid
        self.login = login
        self.password = password