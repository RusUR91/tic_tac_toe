from abc import ABC, abstractmethod


class GameServiceInterface(ABC):


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
    def create_game(self):
        pass

    @abstractmethod
    def get_game(self, uuid):
        pass