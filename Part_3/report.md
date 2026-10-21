# Отчет по разработке игры "Крестики-нолики"

## Задание 1.JWT-авторизация
### Цель задания
Заменить basic-авторизацию на JWT-авторизацию с поддержкой access и refresh токенов.

1.1 Создание моделей для работы с JWT

*JwtRequest - модель запроса аутентификации*

### web/model/jwt_request.py
```
class JwtRequest:
    """Модель запроса для аутентификации пользователя"""
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
```        
Пример использования:

### Создание запроса из данных формы
```
data = request.get_json()
jwt_request = JwtRequest(
    login=data.get('login'),
    password=data.get('password')
)
```
*JwtResponse - модель ответа с токенами*

### web/model/jwt_response.py
```
class JwtResponse:
    """Модель ответа с JWT токенами"""
    def __init__(self, token_type: str, access_token: str, refresh_token: str):
        self.token_type = token_type
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def to_dict(self):
        """Преобразование в словарь для JSON ответа"""
        return {
            'token_type': self.token_type,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }
```

Пример ответа:
```
json
{
    "token_type": "Bearer",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

*RefreshJwtRequest - модель запроса обновления токена*

### web/model/refresh_jwt_request.py
```
class RefreshJwtRequest:
    """Модель запроса для обновления токена"""
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
```

1.2 Реализация JwtProvider

### web/auth/jwt_provider.py
```
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from datetime import timedelta
import os

class JwtProvider:
    """Провайдер для работы с JWT токенами"""
    
    def __init__(self):
        # Настройка времени жизни токенов
        self.access_token_expires = timedelta(
            minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15))
        )
        self.refresh_token_expires = timedelta(
            days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 7))
        )
    
    def generate_access_token(self, user: User) -> str:
        """Генерация access токена"""
        return create_access_token(
            identity=user.uuid,  # Сохраняем UUID пользователя
            expires_delta=self.access_token_expires
        )
    
    def generate_refresh_token(self, user: User) -> str:
        """Генерация refresh токена"""
        return create_refresh_token(
            identity=user.uuid,
            expires_delta=self.refresh_token_expires
        )
    
    def generate_tokens(self, user: User) -> tuple:
        """Генерация обоих токенов"""
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)
        return access_token, refresh_token
    
    def validate_access_token(self, token: str) -> bool:
        """Валидация access токена"""
        try:
            decode_token(token, allow_expired=False)
            return True
        except (InvalidTokenError, JWTExtendedException):
            return False
    
    def validate_refresh_token(self, token: str) -> bool:
        """Валидация refresh токена"""
        try:
            decode_token(token, allow_expired=False)
            return True
        except (InvalidTokenError, JWTExtendedException):
            return False
    
    def get_uuid_from_token(self, token: str) -> Optional[str]:
        """Получение UUID из токена"""
        try:
            decoded = decode_token(token, allow_expired=False)
            return decoded.get('sub')
        except (InvalidTokenError, JWTExtendedException):
            return None
```

1.3 Обновление сервиса пользователей

### domain/service/user_service_impl.py
```
class UserServiceImpl(UserServiceInterface):
    """Реализация сервиса пользователей с JWT поддержкой"""
    
    def __init__(self, user_repository, jwt_provider: JwtProvider = None):
        self.user_repository = user_repository
        self.jwt_provider = jwt_provider or JwtProvider()
    
    def authenticate(self, jwt_request: JwtRequest) -> JwtResponse:
        """
        Аутентификация пользователя
        
        Args:
            jwt_request: Запрос с логином и паролем
        
        Returns:
            JwtResponse: Ответ с токенами
        
        Raises:
            ValueError: При неверных учетных данных
        """
        # Поиск пользователя по логину
        user = self.user_repository.get_by_login(jwt_request.login)
        
        if not user:
            raise ValueError("Invalid login or password")
        
        # Проверка пароля
        hashed_password = self._hash_password(jwt_request.password)
        if user.password != hashed_password:
            raise ValueError("Invalid login or password")
        
        # Генерация токенов
        access_token, refresh_token = self.jwt_provider.generate_tokens(user)
        
        return JwtResponse('Bearer', access_token, refresh_token)
    
    def refresh_tokens(self, refresh_token: str) -> JwtResponse:
        """
        Обновление обоих токенов
        
        Args:
            refresh_token: Текущий refresh токен
        
        Returns:
            JwtResponse: Новые токены
        """
        # Валидация refresh токена
        if not self.jwt_provider.validate_refresh_token(refresh_token):
            raise ValueError("Invalid refresh token")
        
        # Получение UUID пользователя из токена
        user_uuid = self.jwt_provider.get_uuid_from_token(refresh_token)
        if not user_uuid:
            raise ValueError("Invalid refresh token")
        
        # Получение пользователя
        user = self.get_user_by_uuid(user_uuid)
        
        # Генерация новых токенов
        access_token, refresh_token_new = self.jwt_provider.generate_tokens(user)
        
        return JwtResponse('Bearer', access_token, refresh_token_new)
```        
1.4 Реализация аутентификатора

### web/auth/user_authenticator.py
```
from functools import wraps
from flask import request, jsonify

class UserAuthenticator:
    """Класс для аутентификации пользователей через JWT"""
    
    def __init__(self, user_service, jwt_provider: JwtProvider = None):
        self.user_service = user_service
        self.jwt_provider = jwt_provider or JwtProvider()
    
    def _extract_token(self):
        """Извлечение токена из заголовка Authorization"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            # Парсинг "Bearer {token}"
            auth_type, token = auth_header.split(' ', 1)
            if auth_type.lower() != 'bearer':
                return None
            return token
        except Exception:
            return None
    
    def authenticate(self):
        """
        Аутентификация по токену
        
        Returns:
            str: UUID пользователя
        
        Raises:
            ValueError: При невалидном токене
        """
        token = self._extract_token()
        
        if not token:
            raise ValueError("Missing or invalid Authorization header")
        
        if not self.jwt_provider.validate_access_token(token):
            raise ValueError("Invalid or expired token")
        
        user_uuid = self.jwt_provider.get_uuid_from_token(token)
        if not user_uuid:
            raise ValueError("Invalid token")
        
        return user_uuid
    
    def get_authenticated_user(self):
        """Получение аутентифицированного пользователя"""
        user_uuid = self.authenticate()
        return self.user_service.get_user_by_uuid(user_uuid)


def require_auth(user_authenticator):
    """
    Декоратор для защиты endpoint'ов
    
    Использование:
        @app.get('/protected')
        @require_auth(user_authenticator)
        def protected_endpoint():
            user_uuid = request.user_uuid
            return jsonify({'message': 'Access granted'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_uuid = user_authenticator.authenticate()
                request.user_uuid = user_uuid
                return f(*args, **kwargs)
            except ValueError as e:
                return jsonify({'error': str(e)}), 401
        return decorated_function
    return decorator
```    
1.5 Обновление контроллера авторизации

### web/route/auth_router.py
```
def register_auth_routes(app, user_service, user_authenticator):
    
    @app.post('/auth/login')
    def login():
        """Endpoint для входа в систему"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            login = data.get('login')
            password = data.get('password')
            
            if not login or not password:
                return jsonify({'error': 'Login and password are required'}), 400
            
            # Создание запроса и аутентификация
            jwt_request = JwtRequest(login, password)
            jwt_response = user_service.authenticate(jwt_request)
            
            return jsonify(jwt_response.to_dict()), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.post('/auth/refresh')
    def refresh_tokens():
        """Endpoint для обновления токенов"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return jsonify({'error': 'Refresh token is required'}), 400
            
            jwt_response = user_service.refresh_tokens(refresh_token)
            
            return jsonify(jwt_response.to_dict()), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.get('/auth/me')
    @require_auth(user_authenticator)
    def get_current_user():
        """Получение информации о текущем пользователе"""
        try:
            user = user_authenticator.get_authenticated_user()
            return jsonify({
                'uuid': user.uuid,
                'login': user.login
            }), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
```

1.6 Использование в защищенных endpoint'ах

### web/route/game_router.py
```
@require_auth(user_authenticator)
def new_game():
    """Создание новой игры (только для авторизованных)"""
    user_uuid = request.user_uuid  # UUID доступен в request
    # ... создание игры
```

Примеры запросов и ответов
1. Вход в систему

Запрос:
```
http
POST /auth/login
Content-Type: application/json

{
    "login": "alex",
    "password": "password123"
}
```
Ответ (200 OK):
```
json
{
    "token_type": "Bearer",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ"
}
```
2. Запрос истории игр

Запрос:
```
http
GET /game/history
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Ответ (200 OK):
```
json
{
    "total": 5,
    "games": [...]
}
```

## Задание 2. История игр
### Цель задания

Добавить возможность просмотра истории завершенных игр пользователя.

2.1 Добавление даты создания в модель Game

### domain/model/game.py
```
from datetime import datetime

class Game:
    def __init__(self, uuid, board, mode: GameMode = GameMode.WITH_COMPUTER, 
                 created_at: datetime = None):
        self.uuid = uuid
        self.board = board
        self.mode = mode
        self.status = GameStatus.WAITING
        self.players = {}
        self.current_turn = None
        self.winner = None
        self.move_history = []
        self.created_at = created_at or datetime.utcnow()  # Добавлено поле
```

2.2 Обновление SQLAlchemy модели

### datasource/model/game_entity.py
```
from sqlalchemy import DateTime
from datetime import datetime

class GameEntity(db.Model):
    __tablename__ = 'games'
    
    uuid: Mapped[str] = mapped_column(primary_key=True)
    matrix: Mapped[List[List[int]]] = mapped_column(JSON, nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    players: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    current_turn: Mapped[Optional[str]] = mapped_column(nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(nullable=True)
    move_history: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, 
                                                  default=datetime.utcnow)  # Добавлено
```

2.3 Реализация репозитория

### datasource/repository/game_repository.py
```
from sqlalchemy import or_, and_, text

class GameRepository:
    def get_finished_games_by_user(self, user_uuid: str) -> List[Game]:
        """
        Получение всех завершенных игр пользователя
        
        Args:
            user_uuid: UUID пользователя
        
        Returns:
            List[Game]: Список завершенных игр
        """
        # JSON оператор '?' проверяет наличие ключа в JSON объекте
        entities = db.session.query(GameEntity).filter(
            GameEntity.players.op('?')(user_uuid),  # Пользователь есть в игре
            or_(
                GameEntity.status == GameStatus.WIN.value,
                GameEntity.status == GameStatus.DRAW.value
            )
        ).order_by(GameEntity.created_at.desc()).all()  # Сортировка по дате
        
        games = [game_mapper.to_domain(entity) for entity in entities]
        print(f"Loaded {len(games)} finished games for user {user_uuid}")
        return games
```

2.4 Добавление метода в сервис

### domain/service/game_service_impl.py
```
class GameServiceImpl(GameServiceInterface):
    def get_finished_games_by_user(self, user_uuid: str) -> List[Game]:
        """
        Получение всех завершенных игр пользователя
        
        Args:
            user_uuid: UUID пользователя
        
        Returns:
            List[Game]: Список завершенных игр
        """
        return self.game_repository.get_finished_games_by_user(user_uuid)
```

2.5 Создание маппера для истории

### web/mapper/game_mapper.py
```
def to_game_history_response(game, user_uuid=None):
    """
    Преобразование игры в формат истории
    
    Args:
        game: Объект Game
        user_uuid: UUID пользователя для определения результата
    
    Returns:
        dict: Данные игры для истории
    """
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
    
    # Определение результата для пользователя
    if user_uuid and game.status == GameStatus.WIN:
        if game.winner == user_uuid:
            response['result'] = 'win'
        else:
            response['result'] = 'lose'
    elif user_uuid and game.status == GameStatus.DRAW:
        response['result'] = 'draw'
    
    return response

def to_game_history_list_response(games, user_uuid=None):
    """Преобразование списка игр в формат истории"""
    return [to_game_history_response(game, user_uuid) for game in games]
```

2.6 Создание endpoint для истории игр

### web/route/game_router.py
```
@app.get('/game/history')
@require_auth(user_authenticator)
def get_game_history():
    """
    Получение истории игр пользователя
    
    Returns:
        JSON: Список завершенных игр с деталями
    """
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
```

Пример ответа истории игр
```
json
{
    "total": 3,
    "games": [
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "status": "win",
            "mode": "with_computer",
            "players": ["user-uuid-1", "computer"],
            "winner": "user-uuid-1",
            "result": "win",
            "created_at": "2026-06-25T15:30:00",
            "board": [
                [1, 2, 0],
                [0, 1, 2],
                [0, 0, 1]
            ],
            "move_history": [
                {"player": "user-uuid-1", "row": 0, "col": 0, "symbol": 1},
                {"player": "computer", "row": 0, "col": 1, "symbol": 2},
                {"player": "user-uuid-1", "row": 1, "col": 1, "symbol": 1}
            ]
        },
        {
            "uuid": "223e4567-e89b-12d3-a456-426614174001",
            "status": "draw",
            "mode": "with_player",
            "players": ["user-uuid-1", "user-uuid-2"],
            "winner": null,
            "result": "draw",
            "created_at": "2026-06-24T14:20:00",
            "board": [
                [1, 2, 1],
                [1, 2, 2],
                [2, 1, 1]
            ],
            "move_history": [...]
        }
    ]
}
```
## Задание 3.Таблица лидеров

### Цель задания

Создать систему статистики игроков и таблицу лидеров на основе соотношения побед.

3.1 Создание модели PlayerStats

### domain/model/player_stats.py
```
from datetime import datetime

class PlayerStats:
    """Модель статистики игрока"""
    
    def __init__(self, uuid: str, user_uuid: str, wins: int = 0, losses: int = 0,
                 draws: int = 0, total_games: int = 0, win_ratio: float = 0.0,
                 updated_at: datetime = None):
        self.uuid = uuid
        self.user_uuid = user_uuid
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.total_games = total_games
        self.win_ratio = win_ratio
        self.updated_at = updated_at or datetime.utcnow()
    
    def update_stats(self, result: str):
        """
        Обновление статистики после игры
        
        Args:
            result: 'win', 'lose' или 'draw'
        """
        if result == 'win':
            self.wins += 1
        elif result == 'lose':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
        
        # Пересчет общего количества игр
        self.total_games = self.wins + self.losses + self.draws
        
        # Пересчет соотношения побед
        if self.total_games > 0:
            self.win_ratio = self.wins / self.total_games
        else:
            self.win_ratio = 0.0
        
        self.updated_at = datetime.utcnow()
```

3.2 Создание SQLAlchemy модели

### datasource/model/player_stats_entity.py
```
from database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Float, Integer
from datetime import datetime

class PlayerStatsEntity(db.Model):
    __tablename__ = 'player_stats'
    
    uuid: Mapped[str] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(nullable=False, unique=True)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, 
                                                  default=datetime.utcnow)
    
    def update_stats(self, wins: int = 0, losses: int = 0, draws: int = 0):
        """Обновление статистики в БД"""
        self.wins += wins
        self.losses += losses
        self.draws += draws
        self.total_games = self.wins + self.losses + self.draws
        if self.total_games > 0:
            self.win_ratio = self.wins / self.total_games
        else:
            self.win_ratio = 0.0
        self.updated_at = datetime.utcnow()
```

3.3 Реализация репозитория

### datasource/repository/player_stats_repository.py
```
from sqlalchemy import desc

class PlayerStatsRepository:
    def get_top_players_with_stats(self, limit: int) -> List[dict]:
        """
        Получение топ-N игроков по соотношению побед
        
        Args:
            limit: Количество игроков для возврата
        
        Returns:
            List[dict]: Список игроков с их статистикой
        """
        result = db.session.query(
            PlayerStatsEntity.user_uuid,
            PlayerStatsEntity.wins,
            PlayerStatsEntity.losses,
            PlayerStatsEntity.draws,
            PlayerStatsEntity.total_games,
            PlayerStatsEntity.win_ratio,
            UserEntity.login  # Добавляем логин из таблицы users
        ).join(
            UserEntity,
            PlayerStatsEntity.user_uuid == UserEntity.uuid
        ).filter(
            PlayerStatsEntity.total_games > 0  # Только игравшие игроки
        ).order_by(
            desc(PlayerStatsEntity.win_ratio)  # Сортировка по убыванию win_ratio
        ).limit(limit).all()
        
        return [
            {
                'user_uuid': row.user_uuid,
                'login': row.login,
                'wins': row.wins,
                'losses': row.losses,
                'draws': row.draws,
                'total_games': row.total_games,
                'win_ratio': round(row.win_ratio, 3)  # Округление до 3 знаков
            }
            for row in result
        ]
```

3.4 Обновление статистики после игры

### domain/service/game_service_impl.py
```
class GameServiceImpl(GameServiceInterface):
    
    def _update_player_stats(self, game: Game):
        """
        Обновление статистики игроков после завершения игры
        
        Args:
            game: Завершенная игра
        """
        if game.status not in [GameStatus.WIN, GameStatus.DRAW]:
            return
        
        for user_uuid, symbol in game.players.items():
            # Пропускаем компьютер
            if user_uuid == 'computer':
                continue
            
            # Определение результата для игрока
            if game.status == GameStatus.WIN:
                if game.winner == user_uuid:
                    result = 'win'
                else:
                    result = 'lose'
            else:  # DRAW
                result = 'draw'
            
            # Получение или создание статистики
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
            
            # Обновление статистики
            player_stats.update_stats(result)
            self.player_stats_repository.save(player_stats)
            
            print(f"Updated stats for user {user_uuid}: {result}, "
                  f"wins={player_stats.wins}, win_ratio={player_stats.win_ratio:.3f}")
```

3.5 Добавление метода в сервис

### domain/service/game_service_impl.py
```
class GameServiceImpl(GameServiceInterface):
    
    def get_top_players(self, limit: int = 10) -> List[dict]:
        """
        Получение топ-N игроков
        
        Args:
            limit: Количество игроков (от 1 до 100)
        
        Returns:
            List[dict]: Список игроков с их статистикой
        
        Raises:
            ValueError: При некорректном limit
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if limit > 100:
            limit = 100  # Ограничение максимального значения
        
        return self.player_stats_repository.get_top_players_with_stats(limit)
```

3.6 Создание endpoint для таблицы лидеров

### web/route/game_router.py
```
@app.get('/game/leaderboard')
@require_auth(user_authenticator)
def get_leaderboard():
    """
    Получение таблицы лидеров
    
    Query Parameters:
        limit: Количество игроков (по умолчанию 10)
    
    Returns:
        JSON: Список лучших игроков с их статистикой
    """
    try:
        # Получение параметра limit из запроса
        limit = request.args.get('limit', 10, type=int)
        
        # Валидация
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
```

Пример ответа таблицы лидеров
```
json
{
    "total": 5,
    "players": [
        {
            "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "login": "alex",
            "wins": 25,
            "losses": 3,
            "draws": 2,
            "total_games": 30,
            "win_ratio": 0.833
        },
        {
            "user_uuid": "223e4567-e89b-12d3-a456-426614174001",
            "login": "maria",
            "wins": 18,
            "losses": 5,
            "draws": 3,
            "total_games": 26,
            "win_ratio": 0.692
        },
        {
            "user_uuid": "323e4567-e89b-12d3-a456-426614174002",
            "login": "john",
            "wins": 12,
            "losses": 8,
            "draws": 4,
            "total_games": 24,
            "win_ratio": 0.500
        }
    ]
}
```