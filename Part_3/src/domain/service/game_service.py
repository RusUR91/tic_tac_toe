from abc import ABC, abstractmethod
from typing import List, Optional
from domain.model.game import Game, GameMode

class GameServiceInterface(ABC):
    @abstractmethod
    def create_game(self, mode: GameMode = GameMode.WITH_COMPUTER) -> Game:
        pass

    @abstractmethod
    def join_game(self, game_uuid: str, user_uuid: str) -> Game:
        pass

    @abstractmethod
    def get_available_games(self) -> List[Game]:
        pass

    @abstractmethod
    def get_game(self, uuid: str) -> Optional[Game]:
        pass

    @abstractmethod
    def validate_game(self, game):
        pass

    @abstractmethod
    def get_next_move(self, game):
        pass

    @abstractmethod
    def is_game_over(self, game):
        pass

    @abstractmethod
    def get_finished_games_by_user(self, user_uuid: str) -> List[Game]:
        pass

    @abstractmethod
    def get_top_players(self, limit: int = 10) -> List[dict]:
        pass