from domain.model.board import Board
from domain.model.game import Game, GameStatus, GameMode

def to_domain(request):
    board = Board(request.board)
    game = Game(request.uuid, board)
    return game

def to_response(game, user_uuid=None):
    response = {
        'uuid': game.uuid,
        'board': game.board.matrix,
        'status': game.status.value,
        'mode': game.mode.value,
        'players': list(game.players.keys()),
        'current_turn': game.current_turn,
        'is_full': len(game.players) >= 2,
        'move_history': game.move_history,
        'created_at': game.created_at.isoformat() if game.created_at else None
    }
    
    if game.status == GameStatus.WIN:
        response['winner'] = game.winner
    
    if user_uuid:
        response['your_symbol'] = game.get_player_symbol(user_uuid)
        response['your_turn'] = game.current_turn == user_uuid
    
    return response

def to_game_list_response(games, user_uuid=None):
    result = []
    for game in games:
        game_data = {
            'uuid': game.uuid,
            'status': game.status.value,
            'mode': game.mode.value,
            'players_count': len(game.players),
            'is_full': len(game.players) >= 2,
            'created_at': game.created_at.isoformat() if game.created_at else None
        }
        if user_uuid:
            game_data['is_player'] = user_uuid in game.players
        result.append(game_data)
    return result

def to_game_history_response(game, user_uuid=None):
    response = {
        'uuid': game.uuid,
        'status': game.status.value,
        'mode': game.mode.value,
        'players': list(game.players.keys()),
        'winner': game.winner,
        'move_history': game.move_history,
        'created_at': game.created_at.isoformat() if game.created_at else None,
        'board': game.board.matrix
    }
    
    if user_uuid:
        response['your_symbol'] = game.get_player_symbol(user_uuid)
        if game.status == GameStatus.WIN:
            if game.winner == user_uuid:
                response['result'] = 'win'
            else:
                response['result'] = 'lose'
        elif game.status == GameStatus.DRAW:
            response['result'] = 'draw'
    
    return response

def to_game_history_list_response(games, user_uuid=None):
    result = []
    for game in games:
        game_data = to_game_history_response(game, user_uuid)
        result.append(game_data)
    return result