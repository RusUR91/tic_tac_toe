from datasource.mapper import game_mapper


class GameRepository:
    def __init__(self, storage):
        self.storage = storage

    def save(self, game):
        entity = game_mapper.to_entity(game)
        self.storage.save(entity)

    def get(self, uuid):
        entity = self.storage.get(uuid)
        if entity is None:
            return None
        return game_mapper.to_domain(entity)