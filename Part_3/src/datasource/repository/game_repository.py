from database import db
from datasource.model.game_entity import GameEntity
from datasource.mapper import game_mapper
from domain.model.game import Game, GameStatus
from typing import Optional, List
from sqlalchemy import or_, and_, text

class GameRepository:
    def __init__(self, player_stats_repository=None):
        self.player_stats_repository = player_stats_repository

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
            existing.created_at = entity.created_at
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

    def get_finished_games_by_user(self, user_uuid: str) -> List[Game]:
        entities = db.session.query(GameEntity).filter(
            GameEntity.players.op('?')(user_uuid),
            or_(
                GameEntity.status == GameStatus.WIN.value,
                GameEntity.status == GameStatus.DRAW.value
            )
        ).order_by(GameEntity.created_at.desc()).all()
        
        games = [game_mapper.to_domain(entity) for entity in entities]
        print(f"Loaded {len(games)} finished games for user {user_uuid}")
        return games