from flask import request, jsonify
from web.model.game_request import GameRequest
from web.mapper import game_mapper
from web.auth.user_authenticator import require_auth
from domain.model.game import GameMode, GameStatus

def register_routes(app, game_service, user_authenticator):

    @app.post('/game')
    @require_auth(user_authenticator)
    def new_game():
        try:
            user_uuid = request.user_uuid
            data = request.get_json() or {}
            mode_str = data.get('mode', 'with_computer')
            
            print(f"Creating game for user: {user_uuid}, mode: {mode_str}")
            
            if mode_str == 'with_player':
                mode = GameMode.WITH_PLAYER
            else:
                mode = GameMode.WITH_COMPUTER
            
            game = game_service.create_game(mode)
            
            symbol = game.add_player(user_uuid)
            print(f"Added player {user_uuid} with symbol {symbol}")
            
            if mode == GameMode.WITH_COMPUTER:
                game.add_player('computer')
                game.status = GameStatus.IN_PROGRESS
                game.current_turn = user_uuid
                print(f"Added computer, current turn: {game.current_turn}")
            else:
                pass
            
            game_service.game_repository.save(game)
            
            print(f"Game saved. Players: {game.players}, Status: {game.status}, Current turn: {game.current_turn}")
            
            return jsonify(game_mapper.to_response(game, user_uuid)), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error creating game: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.post('/game/<uuid>/join')
    @require_auth(user_authenticator)
    def join_game(uuid):
        try:
            user_uuid = request.user_uuid
            game = game_service.join_game(uuid, user_uuid)
            
            if len(game.players) == 2 and game.status == GameStatus.WAITING:
                game.status = GameStatus.IN_PROGRESS

                for uuid, symbol in game.players.items():
                    if symbol == 1:
                        game.current_turn = uuid
                        break
                print(f"Game {uuid} started! First turn: {game.current_turn}")
                game_service.game_repository.save(game)
            
            print(f"User {user_uuid} joined game {uuid}. Players: {game.players}, Status: {game.status}, Current turn: {game.current_turn}")
            return jsonify(game_mapper.to_response(game, user_uuid)), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error joining game: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.get('/game/available')
    @require_auth(user_authenticator)
    def get_available_games():
        try:
            user_uuid = request.user_uuid
            games = game_service.get_available_games()
            return jsonify(game_mapper.to_game_list_response(games, user_uuid)), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.post('/game/<uuid>/move')
    @require_auth(user_authenticator)
    def make_move(uuid):
        try:
            user_uuid = request.user_uuid
            data = request.get_json()
            
            if not data or 'row' not in data or 'col' not in data:
                return jsonify({'error': 'Row and col are required'}), 400
            
            row = data.get('row')
            col = data.get('col')
            
            print(f"Move request: user={user_uuid}, game={uuid}, row={row}, col={col}")
            
            game = game_service.get_game(uuid)
            
            if not game:
                return jsonify({'error': 'Game not found'}), 404
            
            print(f"Game state: players={game.players}, status={game.status}, current_turn={game.current_turn}")
            
            if user_uuid not in game.players:
                print(f"User {user_uuid} not in players: {game.players}")
                return jsonify({'error': 'You are not in this game'}), 403
            
            if game.status == GameStatus.WAITING:
                return jsonify({'error': 'Game is waiting for another player'}), 400
            
            if game.status in [GameStatus.DRAW, GameStatus.WIN]:
                return jsonify({'error': 'Game is already finished'}), 400
            
            if game.current_turn != user_uuid:
                return jsonify({'error': f'It is not your turn. Current turn: {game.current_turn}'}), 400
            
            if game.board.matrix[row][col] != 0:
                return jsonify({'error': 'Cell is already occupied'}), 400
            
            if game.mode == GameMode.WITH_COMPUTER:
                try:
                    game.board.matrix[row][col] = 1
                    game.move_history.append({
                        'player': user_uuid,
                        'row': row,
                        'col': col,
                        'symbol': 1
                    })
                    
                    game._update_game_status()
                    
                    if game.status in [GameStatus.WIN, GameStatus.DRAW]:
                        game_service._update_player_stats(game)
                        game_service.game_repository.save(game)
                        print(f"Game finished: {game.status}")
                        return jsonify(game_mapper.to_response(game, user_uuid)), 200
                    
                    game.current_turn = 'computer'
                    game_service.game_repository.save(game)
                    game = game_service.get_next_move(game)
                    
                    print(f"After computer move: status={game.status}, current_turn={game.current_turn}")
                    
                    return jsonify(game_mapper.to_response(game, user_uuid)), 200
                    
                except ValueError as error:
                    return jsonify({'error': str(error)}), 400
            else:
                try:
                    game.make_move(user_uuid, row, col)
                    
                    if game.status in [GameStatus.WIN, GameStatus.DRAW]:
                        game_service._update_player_stats(game)
                    
                    game_service.game_repository.save(game)
                    return jsonify(game_mapper.to_response(game, user_uuid)), 200
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error in make_move: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.get('/game/<uuid>')
    @require_auth(user_authenticator)
    def get_game(uuid):
        try:
            user_uuid = request.user_uuid
            game = game_service.get_game(uuid)
            return jsonify(game_mapper.to_response(game, user_uuid)), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.get('/game/history')
    @require_auth(user_authenticator)
    def get_game_history():
        try:
            user_uuid = request.user_uuid
            games = game_service.get_finished_games_by_user(user_uuid)
            
            response = game_mapper.to_game_history_list_response(games, user_uuid)
            
            return jsonify({
                'total': len(response),
                'games': response
            }), 200
        except Exception as e:
            print(f"Error getting game history: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.get('/game/leaderboard')
    @require_auth(user_authenticator)
    def get_leaderboard():
        try:
            limit = request.args.get('limit', 10, type=int)
            
            if limit <= 0:
                return jsonify({'error': 'Limit must be positive'}), 400
            if limit > 100:
                limit = 100
            
            top_players = game_service.get_top_players(limit)
            
            return jsonify({
                'total': len(top_players),
                'players': top_players
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500