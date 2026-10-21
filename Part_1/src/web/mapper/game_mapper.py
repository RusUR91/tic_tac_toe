from domain.model.board import Board
from domain.model.game import Game


def to_domain(request):
    board = Board(request.board)
    game = Game(request.uuid, board)
    return game

def to_response(game):
    return {
        'uuid': game.uuid,
        'board': game.board.matrix
    }