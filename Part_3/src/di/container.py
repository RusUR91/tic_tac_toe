import os
from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager
from web.route.game_router import register_routes
from web.route.ui_route import create_ui_blueprint
from web.route.auth_router import register_auth_routes
from web.route.user_router import register_user_routes
from web.auth.user_authenticator import UserAuthenticator
from web.auth.jwt_provider import JwtProvider
from database import db

load_dotenv()


class Container:
    
    def __init__(self):
        self._repository = None
        self._service = None
        self._app = None
        self._user_repository = None
        self._user_service = None
        self._user_authenticator = None
        self._jwt_provider = None
        self._player_stats_repository = None
    
    @property
    def player_stats_repository(self):
        if self._player_stats_repository is None:
            from datasource.repository.player_stats_repository import PlayerStatsRepository
            self._player_stats_repository = PlayerStatsRepository()
        return self._player_stats_repository
    
    @property
    def repository(self):
        if self._repository is None:
            from datasource.repository.game_repository import GameRepository
            self._repository = GameRepository(self.player_stats_repository)
        return self._repository
    
    @property
    def service(self):
        if self._service is None:
            from domain.service.game_service_impl import GameServiceImpl
            self._service = GameServiceImpl(self.repository, self.player_stats_repository)
        return self._service
    
    @property
    def user_repository(self):
        if self._user_repository is None:
            from datasource.repository.user_repository import UserRepository
            self._user_repository = UserRepository()
        return self._user_repository
    
    @property
    def jwt_provider(self):
        if self._jwt_provider is None:
            self._jwt_provider = JwtProvider()
        return self._jwt_provider
    
    @property
    def user_service(self):
        if self._user_service is None:
            from domain.service.user_service_impl import UserServiceImpl
            self._user_service = UserServiceImpl(self.user_repository, self.jwt_provider)
        return self._user_service
    
    @property
    def user_authenticator(self):
        if self._user_authenticator is None:
            self._user_authenticator = UserAuthenticator(self.user_service, self.jwt_provider)
        return self._user_authenticator
    
    @property
    def app(self):
        if self._app is None:
            self._app = Flask('tic-tac-toe')
            
            database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/tic_tac_toe')
            self._app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            self._app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            self._app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here-change-in-production')
            self._app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900))
            self._app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))
            
            jwt = JWTManager(self._app)
            
            db.init_app(self._app)
            
            with self._app.app_context():
                db.create_all()
            
            register_routes(self._app, self.service, self.user_authenticator)
            register_auth_routes(self._app, self.user_service, self.user_authenticator)
            register_user_routes(self._app, self.user_service, self.user_authenticator)
            self._app.register_blueprint(create_ui_blueprint())
            
        return self._app


container = Container()