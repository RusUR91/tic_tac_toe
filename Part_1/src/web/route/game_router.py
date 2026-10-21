from flask import request
from web.model.game_request import GameRequest
from web.mapper import game_mapper


def register_routes(app, game_service):

    @app.post('/game/<uuid>')
    def update_game(uuid):
        game = GameRequest(uuid, request.json['board'])
        domain_game = game_mapper.to_domain(game)

        try:
            game_service.validate_game(domain_game)
            next_move = game_service.get_next_move(domain_game)
            return game_mapper.to_response(next_move)
        except ValueError as error:
            return {'error': str(error)}, 400

    @app.post('/game')
    def new_game():
        new_game = game_service.create_game()
        return game_mapper.to_response(new_game), 201

    @app.get('/game/<uuid>')
    def get_game(uuid):
        game = game_service.get_game(uuid)
        return game_mapper.to_response(game), 201
