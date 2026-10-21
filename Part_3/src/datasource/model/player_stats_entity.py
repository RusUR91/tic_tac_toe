from database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Float, Integer
from datetime import datetime

class PlayerStatsEntity(db.Model):
    __tablename__ = 'player_stats'
    
    uuid: Mapped[str] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(nullable=False, unique=True)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, uuid: str, user_uuid: str, wins: int = 0, losses: int = 0, 
                 draws: int = 0, total_games: int = 0, win_ratio: float = 0.0,
                 updated_at: datetime = None):
        self.uuid = uuid
        self.user_uuid = user_uuid
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.total_games = total_games
        self.win_ratio = win_ratio
        self.updated_at = updated_at or datetime.utcnow()
    
    def update_stats(self, wins: int = 0, losses: int = 0, draws: int = 0):
        self.wins += wins
        self.losses += losses
        self.draws += draws
        self.total_games = self.wins + self.losses + self.draws
        if self.total_games > 0:
            self.win_ratio = self.wins / self.total_games
        else:
            self.win_ratio = 0.0
        self.updated_at = datetime.utcnow()