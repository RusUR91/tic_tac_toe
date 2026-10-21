from domain.service.game_service import GameServiceInterface
from domain.model.board import Board
from domain.model.game import Game, GameStatus, GameMode
from domain.model.player_stats import PlayerStats
from datasource.repository.player_stats_repository import PlayerStatsRepository
from math import inf
import uuid
from typing import List, Optional
from datetime import datetime

class GameServiceImpl(GameServiceInterface):
    def __init__(self, game_repository, player_stats_repository: PlayerStatsRepository = None):
        self.game_repository = game_repository
        self.player_stats_repository = player_stats_repository or PlayerStatsRepository()

    def create_game(self, mode: GameMode = GameMode.WITH_COMPUTER) -> Game:
        game_uuid = str(uuid.uuid4())
        board = Board([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        game = Game(game_uuid, board, mode, datetime.utcnow())
        print(f"Created game: {game_uuid} with mode: {mode}")
        print(f"Initial players: {game.players}")
        
        self.game_repository.save(game)
        
        saved_game = self.game_repository.get(game_uuid)
        if saved_game:
            print(f"Game saved successfully. Players in saved game: {saved_game.players}")
        else:
            print(f"WARNING: Game {game_uuid} was not saved properly!")
        
        return game

    def join_game(self, game_uuid: str, user_uuid: str) -> Game:
        
        game = self.game_repository.get(game_uuid)
        if game is None:
            raise ValueError('Game with the given UUID does not exist')
        
        if game.status != GameStatus.WAITING:
            raise ValueError('Game is already in progress or finished')
        
        if len(game.players) >= 2:
            raise ValueError('Game is full')
        
        game.add_player(user_uuid)
        print(f"User {user_uuid} joined game {game_uuid}")
        print(f"Players after join: {game.players}")
        
        if len(game.players) == 2:
            game.status = GameStatus.IN_PROGRESS
            for uuid, symbol in game.players.items():
                if symbol == 1:
                    game.current_turn = uuid
                    break
            print(f"Game {game_uuid} started! First turn: {game.current_turn}")
        
        self.game_repository.save(game)
        return game

    def get_available_games(self) -> List[Game]:
        all_games = self.game_repository.get_all()
        return [game for game in all_games if game.status == GameStatus.WAITING and len(game.players) < 2]

    def get_game(self, uuid: str) -> Optional[Game]:
        game = self.game_repository.get(uuid)
        if game is None:
            raise ValueError('Game with the given UUID does not exist')
        print(f"Retrieved game {uuid}: mode={game.mode}, status={game.status}, players={game.players}")
        return game

    def validate_game(self, game):
        if not game:
            raise ValueError("Game is required")
        
        if not game.uuid:
            raise ValueError("UUID is required")
        
        if len(game.board.matrix) != 3:
            raise ValueError("Game board must have 3 rows")

        for row in game.board.matrix:
            if len(row) != 3:
                raise ValueError("Game board must have 3 columns")

        if not (old_game := self.game_repository.get(game.uuid)):
            raise ValueError("Game with the given UUID does not exist")

        if old_game.status not in [GameStatus.IN_PROGRESS, GameStatus.WAITING]:
            raise ValueError("Game is already finished")

        for row in game.board.matrix:
            for cell in row:
                if cell not in [0, 1, 2]:
                    raise ValueError("Game board cells must be either 0, 1, or 2")

        move_count = 0
        for row in range(len(game.board.matrix)):
            for cell in range(len(game.board.matrix[row])):
                old_cell = old_game.board.matrix[row][cell]
                new_cell = game.board.matrix[row][cell]

                if old_cell != new_cell:
                    self._validate_move(old_cell, new_cell)
                    move_count += 1
        
        if move_count != 1:
            raise ValueError("Only one move is allowed per turn")

    def _validate_move(self, old_cell, new_cell):
        if old_cell != 0:
            raise ValueError("Cell is already occupied")
        
        if new_cell not in [1, 2]:
            raise ValueError("Invalid player move")

    def get_next_move(self, game):
        if game.mode != GameMode.WITH_COMPUTER:
            raise ValueError("This game is not with computer")
        
        if self.is_game_over(game):
            return game

        if not hasattr(game, 'board') or not hasattr(game.board, 'matrix'):
            raise ValueError("Invalid game object passed to get_next_move")

        print(f"Computing next move for game {game.uuid}")
        
        best_score = -inf
        best_move = None

        available_moves = self._get_available_moves(game.board.matrix)
        
        if not available_moves:
            return game

        for row, cell in available_moves:
            game.board.matrix[row][cell] = 2
            score = self._minimax(game.board.matrix, False)
            game.board.matrix[row][cell] = 0

            if score > best_score:
                best_score = score
                best_move = (row, cell)

        if best_move is None:
            return game

        best_row, best_cell = best_move
        game.board.matrix[best_row][best_cell] = 2

        game.move_history.append({
            'player': 'computer',
            'row': best_row,
            'col': best_cell,
            'symbol': 2
        })
        
        game._update_game_status()
        
        if game.status == GameStatus.IN_PROGRESS:
            for uuid in game.players:
                if uuid != 'computer':
                    game.current_turn = uuid
                    break
        
        print(f"Computer moved to ({best_row}, {best_cell})")
        
        if game.status in [GameStatus.WIN, GameStatus.DRAW]:
            self._update_player_stats(game)
        
        self.game_repository.save(game)
        return game

    def is_game_over(self, game):
        if not game or not hasattr(game, 'status'):
            return True
        return game.status in [GameStatus.DRAW, GameStatus.WIN]

    def _check_winner(self, board):
        for row in range(3):
            if board[row][0] == board[row][1] == board[row][2] != 0:
                return board[row][0]
        
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != 0:
                return board[0][col]
        
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        
        return 0

    def _get_available_moves(self, board):
        moves = []
        for row in range(3):
            for col in range(3):
                if board[row][col] == 0:
                    moves.append((row, col))
        return moves

    def _minimax(self, board, is_maximizing):
        winner = self._check_winner(board)
        
        if winner == 1:
            return -1
        elif winner == 2:
            return 1
        elif not self._get_available_moves(board):
            return 0
        
        if is_maximizing:
            best_score = -inf
            for row, cell in self._get_available_moves(board):
                board[row][cell] = 2
                score = self._minimax(board, False)
                board[row][cell] = 0
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = inf
            for row, cell in self._get_available_moves(board):
                board[row][cell] = 1
                score = self._minimax(board, True)
                board[row][cell] = 0
                best_score = min(best_score, score)
            return best_score

    def get_finished_games_by_user(self, user_uuid: str) -> List[Game]:
        return self.game_repository.get_finished_games_by_user(user_uuid)

    def _update_player_stats(self, game: Game):

        if game.status not in [GameStatus.WIN, GameStatus.DRAW]:
            return
        
        for user_uuid, symbol in game.players.items():
            if user_uuid == 'computer':
                continue
            
            if game.status == GameStatus.WIN:
                if game.winner == user_uuid:
                    result = 'win'
                else:
                    result = 'lose'
            else:  # DRAW
                result = 'draw'
            
            player_stats = self.player_stats_repository.get_by_user_uuid(user_uuid)
            
            if player_stats is None:
                player_stats = PlayerStats(
                    uuid=str(uuid.uuid4()),
                    user_uuid=user_uuid,
                    wins=0,
                    losses=0,
                    draws=0,
                    total_games=0,
                    win_ratio=0.0
                )
            
            player_stats.update_stats(result)
            self.player_stats_repository.save(player_stats)
            
            print(f"Updated stats for user {user_uuid}: {result}, wins={player_stats.wins}")

    def get_top_players(self, limit: int = 10) -> List[dict]:
        
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if limit > 100:
            limit = 100
        
        return self.player_stats_repository.get_top_players_with_stats(limit)