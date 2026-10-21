from multiprocessing import Lock


class GameStorage:
    def __init__(self):
        self.games = {}
        self.lock = Lock()

    def save(self, game):
        with self.lock:
            self.games[game.uuid] = game
    
    def get(self, uuid):
        with self.lock:
            return self.games.get(uuid)