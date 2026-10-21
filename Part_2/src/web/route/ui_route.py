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
        .cell:disabled { opacity: 0.6; cursor: not-allowed; }
        .cell:not(:disabled):hover { background-color: #e0e0e0; }
        .info { margin: 20px; }
        button { margin-top: 10px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
        .auth-container { margin: 20px auto; max-width: 300px; }
        .auth-container input { display: block; margin: 10px auto; padding: 8px; width: 200px; }
        .error { color: red; }
        .success { color: green; }
        .game-list { margin: 20px auto; max-width: 500px; }
        .game-item { border: 1px solid #ccc; padding: 10px; margin: 10px; }
        .game-item button { margin-top: 10px; }
        .your-turn { color: #4CAF50; font-weight: bold; }
        .opponent-turn { color: #FF9800; }
        .waiting { color: #2196F3; }
        .game-over { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Крестики-нолики</h1>
    
    <div id="authSection">
        <div class="auth-container">
            <h3>Регистрация</h3>
            <input type="text" id="regLogin" placeholder="Логин (мин. 3 символа)">
            <input type="password" id="regPassword" placeholder="Пароль (мин. 6 символов)">
            <button onclick="register()">Зарегистрироваться</button>
        </div>
        <div class="auth-container">
            <h3>Вход</h3>
            <input type="text" id="loginInput" placeholder="Логин">
            <input type="password" id="passwordInput" placeholder="Пароль">
            <button onclick="login()">Войти</button>
        </div>
        <div id="authMessage"></div>
    </div>

    <div id="gameSection" style="display: none;">
        <div class="info">
            <p>Пользователь: <span id="userInfo">-</span></p>
            <p>Режим игры: <span id="gameMode">-</span></p>
            <p>UUID игры: <span id="gameUuid">-</span></p>
            <p>Статус: <span id="status">Загрузка...</span></p>
            <p>Ваш символ: <span id="yourSymbol">-</span></p>
            <p>Ваш ход: <span id="yourTurn">-</span></p>
            <p>Игроки: <span id="playersList">-</span></p>
        </div>
        <div class="board" id="board"></div>
        <br>
        <button onclick="newGame('with_computer')">Новая игра с компьютером</button>
        <button onclick="newGame('with_player')">Новая игра с игроком</button>
        <button onclick="showAvailableGames()">Доступные игры</button>
        <button onclick="logout()">Выйти</button>
        <div id="gameList" class="game-list"></div>
    </div>

    <script>
        let currentUuid = null;
        let authToken = null;
        let currentUser = null;
        let currentSymbol = null;
        let gameMode = null;
        let updateInterval = null;
        let isGameActive = false;
        
        function setAuthHeader() {
            return authToken ? { 'Authorization': 'Basic ' + authToken } : {};
        }
        
        async function register() {
            const login = document.getElementById('regLogin').value;
            const password = document.getElementById('regPassword').value;
            const messageDiv = document.getElementById('authMessage');
            
            try {
                const response = await fetch('/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ login, password })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    messageDiv.innerHTML = '<span class="success">Регистрация успешна! Теперь войдите.</span>';
                } else {
                    messageDiv.innerHTML = '<span class="error">' + result.error + '</span>';
                }
            } catch(e) {
                messageDiv.innerHTML = '<span class="error">Ошибка сервера</span>';
            }
        }
        
        async function login() {
            const login = document.getElementById('loginInput').value;
            const password = document.getElementById('passwordInput').value;
            const messageDiv = document.getElementById('authMessage');
            
            try {
                authToken = btoa(login + ':' + password);
                
                const userResponse = await fetch('/user/me', {
                    headers: setAuthHeader()
                });
                
                if (!userResponse.ok) {
                    throw new Error('Failed to get user info');
                }
                
                const userData = await userResponse.json();
                currentUser = userData;
                
                document.getElementById('userInfo').textContent = userData.login;
                document.getElementById('authSection').style.display = 'none';
                document.getElementById('gameSection').style.display = 'block';
                await showAvailableGames();
            } catch(e) {
                messageDiv.innerHTML = '<span class="error">' + e.message + '</span>';
                authToken = null;
            }
        }
        
        function logout() {
            authToken = null;
            currentUser = null;
            currentUuid = null;
            isGameActive = false;
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
            document.getElementById('authSection').style.display = 'block';
            document.getElementById('gameSection').style.display = 'none';
            document.getElementById('authMessage').innerHTML = '';
        }
        
        async function newGame(mode) {
            try {
                const response = await fetch('/game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...setAuthHeader()
                    },
                    body: JSON.stringify({ mode: mode })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    if (response.status === 401) {
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    throw new Error(error.error || 'Ошибка создания игры');
                }
                
                const game = await response.json();
                currentUuid = game.uuid;
                gameMode = game.mode;
                currentSymbol = game.your_symbol;
                isGameActive = game.status === 'in_progress';
                
                updateGameUI(game);
                
                if (updateInterval) {
                    clearInterval(updateInterval);
                }
                updateInterval = setInterval(() => refreshGameStatus(), 1500);
                
                document.getElementById('gameList').innerHTML = '';
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('status').textContent = 'Ошибка: ' + e.message;
            }
        }
        
        async function refreshGameStatus() {
            if (!currentUuid || !authToken) return;
            
            try {
                const response = await fetch(`/game/${currentUuid}`, {
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    return;
                }
                
                const game = await response.json();
                const oldStatus = document.getElementById('status').textContent;
                const oldTurn = document.getElementById('yourTurn').textContent;
                
                updateGameUI(game);
                
                // Если статус изменился с WAITING на IN_PROGRESS - игра началась!
                if (oldStatus.includes('Ожидание второго игрока') && game.status === 'in_progress') {
                    document.getElementById('status').textContent = '🎮 Игра началась!';
                    if (game.current_turn === currentUser.uuid) {
                        document.getElementById('status').textContent = '🎯 Ваш ход!';
                    }
                    isGameActive = true;
                    drawBoard(game.board);
                }
                
                if (game.status === 'win' || game.status === 'draw') {
                    if (updateInterval) {
                        clearInterval(updateInterval);
                        updateInterval = null;
                    }
                    isGameActive = false;
                }
            } catch(e) {
                console.error('Ошибка обновления:', e);
            }
        }
        
        async function showAvailableGames() {
            try {
                const response = await fetch('/game/available', {
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    throw new Error('Ошибка получения игр');
                }
                
                const games = await response.json();
                const gameListDiv = document.getElementById('gameList');
                
                if (games.length === 0) {
                    gameListDiv.innerHTML = '<p>Нет доступных игр</p>';
                    return;
                }
                
                gameListDiv.innerHTML = '<h3>Доступные игры:</h3>';
                for (const game of games) {
                    const gameItem = document.createElement('div');
                    gameItem.className = 'game-item';
                    gameItem.innerHTML = `
                        <p>UUID: ${game.uuid}</p>
                        <p>Статус: ${game.status}</p>
                        <p>Игроков: ${game.players_count}</p>
                        <button onclick="joinGame('${game.uuid}')">Присоединиться</button>
                    `;
                    gameListDiv.appendChild(gameItem);
                }
            } catch(e) {
                console.error('Ошибка:', e);
            }
        }
        
        async function joinGame(uuid) {
            try {
                const response = await fetch(`/game/${uuid}/join`, {
                    method: 'POST',
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Ошибка присоединения');
                }
                
                const game = await response.json();
                currentUuid = game.uuid;
                currentSymbol = game.your_symbol;
                isGameActive = game.status === 'in_progress';
                
                updateGameUI(game);
                
                if (updateInterval) {
                    clearInterval(updateInterval);
                }
                updateInterval = setInterval(() => refreshGameStatus(), 1500);
                
                document.getElementById('gameList').innerHTML = '';
                
                // Принудительно обновляем статус через 1 секунду
                setTimeout(() => refreshGameStatus(), 1000);
                
                // Если игра уже началась, показываем уведомление
                if (game.status === 'in_progress') {
                    document.getElementById('status').textContent = '🎮 Игра началась!';
                }
            } catch(e) {
                alert('Ошибка: ' + e.message);
            }
        }
        
        function updateGameUI(game) {
            document.getElementById('gameUuid').textContent = game.uuid;
            document.getElementById('gameMode').textContent = game.mode === 'with_player' ? 'С игроком' : 'С компьютером';
            document.getElementById('yourSymbol').textContent = game.your_symbol === 1 ? 'X' : 'O';
            document.getElementById('playersList').textContent = game.players.join(', ');
            
            // Обновляем список игроков с отметкой кто ходит
            let playersText = '';
            for (const player of game.players) {
                const isCurrent = player === game.current_turn;
                const isYou = player === currentUser.uuid;
                const symbol = game.your_symbol === 1 ? 'X' : 'O';
                playersText += `${player}${isYou ? ' (Вы)' : ''}${isCurrent ? ' 🎯' : ''}, `;
            }
            document.getElementById('playersList').textContent = playersText.slice(0, -2);
            
            drawBoard(game.board);
            updateStatus(game);
        }
        
        function drawBoard(board) {
            const boardDiv = document.getElementById('board');
            boardDiv.innerHTML = '';
            
            const statusText = document.getElementById('status').textContent;
            const isGameActive = !statusText.includes('Ожидание') && 
                               !statusText.includes('Игра завершена') &&
                               !statusText.includes('Победили') &&
                               !statusText.includes('Ничья');
            
            const isYourTurn = document.getElementById('yourTurn').textContent.includes('Да');
            const isWaiting = statusText.includes('Ожидание второго игрока');
            
            for(let i = 0; i < 3; i++) {
                for(let j = 0; j < 3; j++) {
                    const cell = document.createElement('button');
                    cell.className = 'cell';
                    const val = board[i][j];
                    cell.textContent = val === 1 ? 'X' : (val === 2 ? 'O' : '');
                    
                    // Разрешаем ход только если:
                    // 1. Клетка пустая
                    // 2. Игра активна
                    // 3. Не ожидание второго игрока
                    // 4. Это ваш ход
                    const canMove = val === 0 && isGameActive && !isWaiting && isYourTurn;
                    cell.disabled = !canMove;
                    
                    if (canMove) {
                        cell.style.cursor = 'pointer';
                        cell.style.backgroundColor = '#e8f5e9';
                    } else if (val === 0) {
                        cell.style.backgroundColor = '#f5f5f5';
                    }
                    
                    cell.onclick = () => {
                        if (!cell.disabled) {
                            makeMove(i, j);
                        }
                    };
                    boardDiv.appendChild(cell);
                }
            }
        }
        
        async function makeMove(row, col) {
            try {
                const response = await fetch(`/game/${currentUuid}/move`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...setAuthHeader()
                    },
                    body: JSON.stringify({ row: row, col: col })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    if (response.status === 401) {
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    document.getElementById('status').textContent = 'Ошибка: ' + error.error;
                    return;
                }
                
                const result = await response.json();
                updateGameUI(result);
                
                // Если игра с компьютером и игра продолжается, делаем ход компьютера
                if (result.mode === 'with_computer' && 
                    result.status === 'in_progress' && 
                    result.current_turn === 'computer') {
                    document.getElementById('status').textContent = '🤖 Ход компьютера...';
                    setTimeout(() => refreshGameStatus(), 500);
                }
                
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('status').textContent = 'Ошибка! Смотри консоль (F12)';
            }
        }
        
        function updateStatus(game) {
            const statusDiv = document.getElementById('status');
            const yourTurnDiv = document.getElementById('yourTurn');
            
            if (game.status === 'waiting') {
                statusDiv.innerHTML = '⏳ <span class="waiting">Ожидание второго игрока...</span>';
                yourTurnDiv.textContent = 'Ожидание';
                yourTurnDiv.className = 'waiting';
            } else if (game.status === 'in_progress') {
                if (game.current_turn === currentUser.uuid) {
                    statusDiv.innerHTML = '🎯 <span class="your-turn">Ваш ход!</span>';
                    yourTurnDiv.textContent = 'Да';
                    yourTurnDiv.className = 'your-turn';
                } else if (game.current_turn === 'computer') {
                    statusDiv.innerHTML = '🤖 <span class="opponent-turn">Ход компьютера...</span>';
                    yourTurnDiv.textContent = 'Нет';
                    yourTurnDiv.className = 'opponent-turn';
                } else {
                    statusDiv.innerHTML = '⏳ <span class="opponent-turn">Ход противника...</span>';
                    yourTurnDiv.textContent = 'Нет';
                    yourTurnDiv.className = 'opponent-turn';
                }
            } else if (game.status === 'win') {
                if (game.winner === currentUser.uuid) {
                    statusDiv.innerHTML = '🎉 <span class="your-turn">Вы победили!</span>';
                } else {
                    statusDiv.innerHTML = '😢 <span class="game-over">Вы проиграли!</span>';
                }
                yourTurnDiv.textContent = 'Игра завершена';
                yourTurnDiv.className = 'game-over';
            } else if (game.status === 'draw') {
                statusDiv.innerHTML = '🤝 <span class="waiting">Ничья!</span>';
                yourTurnDiv.textContent = 'Игра завершена';
                yourTurnDiv.className = 'game-over';
            }
        }
    </script>
</body>
</html>"""