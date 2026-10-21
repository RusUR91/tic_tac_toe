from domain.model.game import Game
from domain.model.board import Board
from datasource.model.game_entity import GameEntity


def to_entity(game):
    game_entity = GameEntity(game.uuid, game.board.matrix)
    return game_entity

def to_domain(entity):
    game_board = Board(entity.matrix)
    game = Game(entity.uuid, game_board)
    return game