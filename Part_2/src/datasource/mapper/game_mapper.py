from domain.model.game import Game, GameStatus, GameMode
from domain.model.board import Board
from datasource.model.game_entity import GameEntity


def to_entity(game):
    game_entity = GameEntity(
        game.uuid, 
        game.board.matrix,
        game.mode.value, 
        game.status.value,  
        game.players,
        game.current_turn,
        game.winner,
        game.move_history
    )
    return game_entity

def to_domain(entity):
    game_board = Board(entity.matrix)
    game = Game(entity.uuid, game_board, GameMode(entity.mode))
    game.status = GameStatus(entity.status)
    game.players = entity.players or {}
    game.current_turn = entity.current_turn
    game.winner = entity.winner
    game.move_history = entity.move_history or []
    return game