from domain.service.game_service import GameServiceInterface
from domain.model.board import Board
from domain.model.game import Game
from math import inf

import uuid

class GameServiceImpl(GameServiceInterface):
    def __init__(self, game_repository):
        self.game_repository = game_repository

    def _validate_move(self, old_cell, new_cell):
        if old_cell != 0:
            raise ValueError("Cell is already occupied")
        
        if new_cell != 1:
            raise ValueError("Invalid player move")

    def _check_winner(self, board):
        main_diag = []
        side_diag = []
        for row in range(len(board)):
            if len(set(board[row])) == 1 and board[row][0] != 0:
                return board[row][0]
            if board[0][row] == board[1][row] == board[2][row] and board[0][row] != 0:
                return board[0][row]
            main_diag.append(board[row][row])
            side_diag.append(board[row][len(board[row]) - 1 - row])
        if len(set(main_diag)) == 1 and main_diag[0] != 0:
            return main_diag[0]
        elif len(set(side_diag)) == 1 and side_diag[0] != 0:
            return side_diag[0]
        return 0

    def _get_available_moves(self, board):
        moves = []
        for row in range(len(board)):
            for cell in range(len(board[row])):
                if board[row][cell] == 0:
                    moves.append((row, cell))
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
            best_score = (-1 * inf)

            for row, cell in self._get_available_moves(board):
                board[row][cell] = 2
                score = self._minimax(board, False)
                board[row][cell] = 0
                best_score = max(best_score, score)

        else:
            best_score = inf

            for row, cell in self._get_available_moves(board):
                board[row][cell] = 1
                score = self._minimax(board, True)
                board[row][cell] = 0
                best_score = min(best_score, score)

        return best_score


    def create_game(self):
        game_uuid = str(uuid.uuid4())
        board = Board([[0, 0, 0], 
                        [0, 0, 0],
                        [0, 0, 0]])
        game = Game(game_uuid, board)
        self.game_repository.save(game)
        return game

    def get_game(self, uuid):
        game = self.game_repository.get(uuid)
        if game is None:
            raise ValueError('Game with the given UUID does not exist')
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

    
    def is_game_over(self, game):
        winner = self._check_winner(game.board.matrix)
        if winner != 0:
            return True
        for row in game.board.matrix:
            if 0 in row:
                return False
        return True

    
    def get_next_move(self, game):

        if self.is_game_over(game):
            return game

        best_score = -inf
        best_move = None

        for row, cell in self._get_available_moves(game.board.matrix):
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

        self.game_repository.save(game)

        return game