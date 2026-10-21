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
        .history-container { margin: 20px auto; max-width: 800px; }
        .history-item { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; background: #f9f9f9; }
        .history-item .result-win { color: #4CAF50; font-weight: bold; font-size: 1.2em; }
        .history-item .result-lose { color: #f44336; font-weight: bold; font-size: 1.2em; }
        .history-item .result-draw { color: #FF9800; font-weight: bold; font-size: 1.2em; }
        .history-item .date { color: #666; font-size: 0.9em; margin: 5px 0; }
        .history-board { display: inline-grid; grid-template-columns: repeat(3, 40px); gap: 2px; margin: 10px 0; }
        .history-cell { width: 40px; height: 40px; font-size: 20px; text-align: center; line-height: 40px; border: 1px solid #ccc; background: #fff; }
        .nav-buttons { margin: 20px 0; }
        .nav-buttons button { margin: 0 10px; }
        /* Стили для таблицы лидеров */
        .leaderboard-table { margin: 0 auto; border-collapse: collapse; width: 80%; }
        .leaderboard-table th { padding: 12px; border: 1px solid #ddd; background: #4CAF50; color: white; }
        .leaderboard-table td { padding: 10px; border: 1px solid #ddd; text-align: center; }
        .leaderboard-table tr:nth-child(even) { background: #f9f9f9; }
        .leaderboard-table tr.current-user { background: #e3f2fd; }
        .medal { font-size: 1.2em; }
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
        <div class="nav-buttons">
            <button onclick="showMainGame()">🎮 Игра</button>
            <button onclick="showHistory()">📜 История игр</button>
            <button onclick="showLeaderboard()">🏆 Таблица лидеров</button>
            <button onclick="logout()">🚪 Выйти</button>
        </div>
        
        <div id="mainGameView">
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
            <div id="gameList" class="game-list"></div>
        </div>
        
        <div id="historyView" style="display: none;">
            <h2>📜 История игр</h2>
            <div id="historyContainer" class="history-container">
                <p>Загрузка истории...</p>
            </div>
            <button onclick="showMainGame()">← Назад к игре</button>
        </div>
        
        <div id="leaderboardView" style="display: none;">
            <h2>🏆 Таблица лидеров</h2>
            <div id="leaderboardContainer">
                <p>Загрузка...</p>
            </div>
            <button onclick="showMainGame()">← Назад к игре</button>
        </div>
    </div>

    <script>
        let currentUuid = null;
        let accessToken = null;
        let refreshToken = null;
        let currentUser = null;
        let currentSymbol = null;
        let gameMode = null;
        let updateInterval = null;
        let isGameActive = false;
        let showingHistory = false;
        
        function setAuthHeader() {
            return accessToken ? { 'Authorization': 'Bearer ' + accessToken } : {};
        }
        
        function showMainGame() {
            showingHistory = false;
            document.getElementById('mainGameView').style.display = 'block';
            document.getElementById('historyView').style.display = 'none';
            document.getElementById('leaderboardView').style.display = 'none';
            if (currentUuid) {
                refreshGameStatus();
            }
        }
        
        async function showHistory() {
            showingHistory = true;
            document.getElementById('mainGameView').style.display = 'none';
            document.getElementById('historyView').style.display = 'block';
            document.getElementById('leaderboardView').style.display = 'none';
            
            try {
                const response = await fetch('/game/history', {
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        if (await refreshAccessToken()) {
                            return showHistory();
                        }
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    throw new Error('Ошибка получения истории');
                }
                
                const data = await response.json();
                const container = document.getElementById('historyContainer');
                
                if (data.total === 0) {
                    container.innerHTML = '<p>У вас пока нет завершенных игр.</p>';
                    return;
                }
                
                container.innerHTML = `<p>Всего игр: ${data.total}</p>`;
                
                for (const game of data.games) {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    let resultText = '';
                    let resultClass = '';
                    if (game.result === 'win') {
                        resultText = '🏆 Победа!';
                        resultClass = 'result-win';
                    } else if (game.result === 'lose') {
                        resultText = '😢 Поражение';
                        resultClass = 'result-lose';
                    } else if (game.result === 'draw') {
                        resultText = '🤝 Ничья';
                        resultClass = 'result-draw';
                    }
                    
                    const date = new Date(game.created_at);
                    const dateStr = date.toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
                    });
                    
                    item.innerHTML = `
                        <div class="${resultClass}">${resultText}</div>
                        <div class="date">📅 ${dateStr}</div>
                        <div>Режим: ${game.mode === 'with_player' ? 'С игроком' : 'С компьютером'}</div>
                        <div>Игроки: ${game.players.join(', ')}</div>
                        <div>Статус: ${game.status}</div>
                        <div>Ваш символ: ${game.your_symbol === 1 ? 'X' : 'O'}</div>
                        <div>Доска:</div>
                        <div class="history-board">
                            ${game.board.map(row => 
                                row.map(cell => 
                                    `<div class="history-cell">${cell === 1 ? 'X' : (cell === 2 ? 'O' : '')}</div>`
                                ).join('')
                            ).join('')}
                        </div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">UUID: ${game.uuid}</div>
                    `;
                    container.appendChild(item);
                }
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('historyContainer').innerHTML = '<p>Ошибка загрузки истории</p>';
            }
        }
        
        async function showLeaderboard() {
            showingHistory = false;
            document.getElementById('mainGameView').style.display = 'none';
            document.getElementById('historyView').style.display = 'none';
            document.getElementById('leaderboardView').style.display = 'block';
            
            await loadLeaderboard();
        }
        
        async function loadLeaderboard(limit = 10) {
            try {
                const response = await fetch(`/game/leaderboard?limit=${limit}`, {
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        if (await refreshAccessToken()) {
                            return loadLeaderboard(limit);
                        }
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    throw new Error('Ошибка получения таблицы лидеров');
                }
                
                const data = await response.json();
                const container = document.getElementById('leaderboardContainer');
                
                if (data.total === 0) {
                    container.innerHTML = '<p>Пока нет игроков в таблице лидеров.</p>';
                    return;
                }
                
                let html = `
                    <div style="margin: 20px 0;">
                        <label>Количество игроков: 
                            <select onchange="loadLeaderboard(this.value)">
                                <option value="5">5</option>
                                <option value="10" selected>10</option>
                                <option value="25">25</option>
                                <option value="50">50</option>
                            </select>
                        </label>
                    </div>
                    <table class="leaderboard-table">
                        <thead>
                            <tr>
                                <th>Место</th>
                                <th>Игрок</th>
                                <th>Победы</th>
                                <th>Поражения</th>
                                <th>Ничьи</th>
                                <th>Всего игр</th>
                                <th>Соотношение побед</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.players.forEach((player, index) => {
                    const isCurrentUser = player.user_uuid === currentUser?.uuid;
                    const medal = index === 0 ? '🥇' : (index === 1 ? '🥈' : (index === 2 ? '🥉' : `#${index + 1}`));
                    const winRatio = (player.win_ratio * 100).toFixed(1) + '%';
                    
                    html += `
                        <tr class="${isCurrentUser ? 'current-user' : ''}">
                            <td class="medal">${medal}</td>
                            <td>${isCurrentUser ? '⭐ ' : ''}${player.login}</td>
                            <td style="color: #4CAF50;">${player.wins}</td>
                            <td style="color: #f44336;">${player.losses}</td>
                            <td style="color: #FF9800;">${player.draws}</td>
                            <td>${player.total_games}</td>
                            <td><strong>${winRatio}</strong></td>
                        </tr>
                    `;
                });
                
                html += `
                        </tbody>
                    </table>
                `;
                
                container.innerHTML = html;
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('leaderboardContainer').innerHTML = '<p>Ошибка загрузки таблицы лидеров</p>';
            }
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
                    messageDiv.innerHTML = '<span class="error">' + (result.error || 'Ошибка регистрации') + '</span>';
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
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ login, password })
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Ошибка входа');
                }
                
                accessToken = result.access_token;
                refreshToken = result.refresh_token;
                
                const userResponse = await fetch('/auth/me', {
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
                
                startTokenRefresh();
            } catch(e) {
                messageDiv.innerHTML = '<span class="error">' + e.message + '</span>';
                accessToken = null;
                refreshToken = null;
            }
        }
        
        function startTokenRefresh() {
            setInterval(async () => {
                try {
                    await refreshAccessToken();
                } catch(e) {
                    console.error('Token refresh failed:', e);
                }
            }, 10 * 60 * 1000);
        }
        
        async function refreshAccessToken() {
            try {
                const response = await fetch('/auth/refresh', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to refresh token');
                }
                
                const result = await response.json();
                accessToken = result.access_token;
                return true;
            } catch(e) {
                console.error('Token refresh failed:', e);
                logout();
                return false;
            }
        }
        
        function logout() {
            accessToken = null;
            refreshToken = null;
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
            document.getElementById('gameList').innerHTML = '';
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
                        if (await refreshAccessToken()) {
                            return newGame(mode);
                        }
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
            if (!currentUuid || !accessToken) return;
            
            try {
                const response = await fetch(`/game/${currentUuid}`, {
                    headers: setAuthHeader()
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        if (await refreshAccessToken()) {
                            return refreshGameStatus();
                        }
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    return;
                }
                
                const game = await response.json();
                const oldStatus = document.getElementById('status').textContent;
                
                updateGameUI(game);
                
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
                        if (await refreshAccessToken()) {
                            return showAvailableGames();
                        }
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
                document.getElementById('gameList').innerHTML = '<p>Ошибка загрузки игр</p>';
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
                    if (response.status === 401) {
                        if (await refreshAccessToken()) {
                            return joinGame(uuid);
                        }
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
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
                
                setTimeout(() => refreshGameStatus(), 1000);
                
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
            
            let playersText = '';
            for (const player of game.players) {
                const isCurrent = player === game.current_turn;
                const isYou = player === currentUser?.uuid;
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
                        if (await refreshAccessToken()) {
                            return makeMove(row, col);
                        }
                        alert('Сессия истекла. Войдите заново.');
                        logout();
                        return;
                    }
                    document.getElementById('status').textContent = 'Ошибка: ' + (error.error || 'Неизвестная ошибка');
                    return;
                }
                
                const result = await response.json();
                updateGameUI(result);
                
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
                if (game.current_turn === currentUser?.uuid) {
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
                if (game.winner === currentUser?.uuid) {
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
</html>
"""