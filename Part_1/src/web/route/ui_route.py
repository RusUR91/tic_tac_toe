from flask import Blueprint, render_template_string


def create_ui_blueprint():
    ui_blueprint = Blueprint("ui", __name__)

    @ui_blueprint.get("/")
    def index():
        return render_template_string(HTML_PAGE)

    return ui_blueprint

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Крестики-нолики</title>
    <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; }
        .board { display: inline-grid; grid-template-columns: repeat(3, 100px); gap: 5px; }
        .cell { width: 100px; height: 100px; font-size: 40px; cursor: pointer; }
        .info { margin: 20px; }
        button { margin-top: 20px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Крестики-нолики</h1>
    <div class="info">
        <p>UUID игры: <span id="gameUuid">-</span></p>
        <p>Статус: <span id="status">Загрузка...</span></p>
    </div>
    <div class="board" id="board"></div>
    <br>
    <button onclick="newGame()">Новая игра</button>
    <!-- <pre id="debug">Ожидание...</pre> -->

    <script>
        let currentUuid = null;
        
        async function newGame() {
            try {
                const response = await fetch('/game', { method: 'POST' });
                const game = await response.json();
                
                currentUuid = game.uuid;
                document.getElementById('gameUuid').textContent = currentUuid;
                drawBoard(game.board);
                document.getElementById('status').textContent = 'Твой ход (X)';
            } catch(e) {
                console.error('Ошибка:', e);  // Ошибка будет только в консоли браузера
            }
        }
        
        function drawBoard(board) {
            const boardDiv = document.getElementById('board');
            boardDiv.innerHTML = '';
            
            for(let i = 0; i < 3; i++) {
                for(let j = 0; j < 3; j++) {
                    const cell = document.createElement('button');
                    cell.className = 'cell';
                    const val = board[i][j];
                    cell.textContent = val === 1 ? 'X' : (val === 2 ? 'O' : '');
                    cell.disabled = val !== 0;
                    cell.onclick = () => makeMove(i, j, board);
                    boardDiv.appendChild(cell);
                }
            }
        }
        
        async function makeMove(row, col, currentBoard) {
            const newBoard = JSON.parse(JSON.stringify(currentBoard));
            newBoard[row][col] = 1;
            
            document.getElementById('status').textContent = 'Ход отправлен...';
            
            try {
                const response = await fetch(`/game/${currentUuid}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uuid: currentUuid, board: newBoard })
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    document.getElementById('status').textContent = 'Ошибка: ' + result.error;
                    return;
                }
                
                drawBoard(result.board);
                
                const winner = checkWinner(result.board);
                if(winner === 1) document.getElementById('status').textContent = 'Ты выиграл!';
                else if(winner === 2) document.getElementById('status').textContent = 'Компьютер выиграл';
                else if(isDraw(result.board)) document.getElementById('status').textContent = 'Ничья!';
                else document.getElementById('status').textContent = 'Твой ход (X)';
                
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('status').textContent = 'Ошибка! Смотри консоль (F12)';
            }
        }
        
        function checkWinner(board) {
            const lines = [
                [[0,0],[0,1],[0,2]], [[1,0],[1,1],[1,2]], [[2,0],[2,1],[2,2]],
                [[0,0],[1,0],[2,0]], [[0,1],[1,1],[2,1]], [[0,2],[1,2],[2,2]],
                [[0,0],[1,1],[2,2]], [[0,2],[1,1],[2,0]]
            ];
            
            for(const line of lines) {
                const a = board[line[0][0]][line[0][1]];
                const b = board[line[1][0]][line[1][1]];
                const c = board[line[2][0]][line[2][1]];
                if(a !== 0 && a === b && b === c) return a;
            }
            return null;
        }
        
        function isDraw(board) {
            return checkWinner(board) === null && board.flat().every(cell => cell !== 0);
        }
        
        newGame();
    </script>
</body>
</html>
"""    