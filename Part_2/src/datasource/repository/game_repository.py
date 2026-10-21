from database import db
from datasource.model.game_entity import GameEntity
from datasource.mapper import game_mapper
from domain.model.game import Game
from typing import Optional, List

class GameRepository:
    def __init__(self):
        pass

    def save(self, game: Game) -> None:
        entity = game_mapper.to_entity(game)
        existing = db.session.get(GameEntity, entity.uuid)
        
        if existing:
            existing.matrix = entity.matrix
            existing.mode = entity.mode
            existing.status = entity.status
            existing.players = entity.players
            existing.current_turn = entity.current_turn
            existing.winner = entity.winner
            existing.move_history = entity.move_history
        else:
            db.session.add(entity)
        
        db.session.commit()
        print(f"Game {game.uuid} saved. Players: {game.players}")

    def get(self, uuid: str) -> Optional[Game]:
        entity = db.session.get(GameEntity, uuid)
        if entity is None:
            return None
        game = game_mapper.to_domain(entity)
        print(f"Game {uuid} loaded. Players: {game.players}")
        return game

    def get_all(self) -> List[Game]:
        entities = db.session.query(GameEntity).all()
        games = [game_mapper.to_domain(entity) for entity in entities]
        print(f"Loaded {len(games)} games from database")
        return games