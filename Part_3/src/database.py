from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import List, Optional

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)