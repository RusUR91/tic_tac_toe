from enum import Enum
from typing import Optional

class GameStatus(Enum):
    WAITING = "waiting"  
    IN_PROGRESS = "in_progress" 
    DRAW = "draw" 
    WIN = "win"  

class GameMode(Enum):
    WITH_COMPUTER = "with_computer"
    WITH_PLAYER = "with_player"

class Game:
    def __init__(self, uuid, board, mode: GameMode = GameMode.WITH_COMPUTER):
        self.uuid = uuid
        self.board = board
        self.mode = mode
        self.status = GameStatus.WAITING
        self.players = {}  
        self.current_turn = None  
        self.winner = None  
        self.move_history = []  

    def add_player(self, user_uuid: str) -> int:
        if len(self.players) >= 2:
            raise ValueError("Game is full")
        
        if user_uuid in self.players:
            raise ValueError("Player already in game")
        
        symbol = 1 if len(self.players) == 0 else 2
        self.players[user_uuid] = symbol
        
        if len(self.players) == 2:
            self.status = GameStatus.IN_PROGRESS
            self.current_turn = next(iter(self.players.keys())) 
        
        return symbol

    def make_move(self, user_uuid: str, row: int, col: int):
    
        if self.status == GameStatus.WAITING:
            raise ValueError("Game is waiting for another player")
        
        if self.status == GameStatus.DRAW or self.status == GameStatus.WIN:
            raise ValueError("Game is already finished")
        
        if user_uuid not in self.players:
            raise ValueError("Player is not in this game")
        
        if self.current_turn != user_uuid:
            raise ValueError("It's not your turn")
        
        if self.board.matrix[row][col] != 0:
            raise ValueError("Cell is already occupied")
        
        symbol = self.players[user_uuid]
        self.board.matrix[row][col] = symbol
        self.move_history.append({
            'player': user_uuid,
            'row': row,
            'col': col,
            'symbol': symbol
        })
        
        print(f"Player {user_uuid} moved to ({row}, {col}) with symbol {symbol}")
        
        self._update_game_status()
        
        if self.status == GameStatus.IN_PROGRESS:
            players_list = list(self.players.keys())
            current_index = players_list.index(user_uuid)
            next_index = (current_index + 1) % len(players_list)
            self.current_turn = players_list[next_index]
            print(f"Next turn: {self.current_turn}")

    def _update_game_status(self):
        winner = self._check_winner()
        
        if winner:
            self.status = GameStatus.WIN
            for uuid, symbol in self.players.items():
                if symbol == winner:
                    self.winner = uuid
                    break
        elif self._is_board_full():
            self.status = GameStatus.DRAW
        else:
            self.status = GameStatus.IN_PROGRESS

    def _check_winner(self):
        board = self.board.matrix
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

    def _is_board_full(self):
        for row in self.board.matrix:
            for cell in row:
                if cell == 0:
                    return False
        return True

    def get_player_symbol(self, user_uuid: str) -> Optional[int]:
        return self.players.get(user_uuid)

    def get_opponent(self, user_uuid: str) -> Optional[str]:
        for uuid in self.players:
            if uuid != user_uuid:
                return uuid
        return None