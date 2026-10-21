class Container:
    
    def __init__(self):
        self._storage = None
        self._repository = None
        self._service = None
        self._app = None
    
    @property
    def storage(self):
        if self._storage is None:
            from datasource.repository.game_storage import GameStorage
            self._storage = GameStorage()
        return self._storage
    
    @property
    def repository(self):
        if self._repository is None:
            from datasource.repository.game_repository import GameRepository
            self._repository = GameRepository(self.storage)
        return self._repository
    
    @property
    def service(self):
        if self._service is None:
            from domain.service.game_service_impl import GameServiceImpl
            self._service = GameServiceImpl(self.repository)
        return self._service
    
    @property
    def app(self):
        if self._app is None:
            from flask import Flask
            from web.route.game_router import register_routes
            from web.route.ui_route import create_ui_blueprint
            
            self._app = Flask('tic-tac-toe')
            register_routes(self._app, self.service)
            self._app.register_blueprint(create_ui_blueprint())
        return self._app

container = Container()