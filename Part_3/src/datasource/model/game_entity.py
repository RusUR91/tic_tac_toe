from typing import List, Dict, Optional
from database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, DateTime
from datetime import datetime

class GameEntity(db.Model):
    __tablename__ = 'games'
    
    uuid: Mapped[str] = mapped_column(primary_key=True)
    matrix: Mapped[List[List[int]]] = mapped_column(JSON, nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    players: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    current_turn: Mapped[Optional[str]] = mapped_column(nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(nullable=True)
    move_history: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, uuid: str, matrix: List[List[int]], mode: str, status: str, 
                 players: Dict[str, int] = None, current_turn: str = None, 
                 winner: str = None, move_history: List[Dict] = None,
                 created_at: datetime = None):
        self.uuid = uuid
        self.matrix = matrix
        self.mode = mode
        self.status = status
        self.players = players or {}
        self.current_turn = current_turn
        self.winner = winner
        self.move_history = move_history or []
        self.created_at = created_at or datetime.utcnow()