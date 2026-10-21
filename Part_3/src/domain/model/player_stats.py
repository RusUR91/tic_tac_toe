from datetime import datetime

class PlayerStats:
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
    
    def update_stats(self, result: str):
        if result == 'win':
            self.wins += 1
        elif result == 'lose':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
        
        self.total_games = self.wins + self.losses + self.draws
        if self.total_games > 0:
            self.win_ratio = self.wins / self.total_games
        else:
            self.win_ratio = 0.0
        self.updated_at = datetime.utcnow()