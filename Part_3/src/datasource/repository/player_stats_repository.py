from database import db
from datasource.model.player_stats_entity import PlayerStatsEntity
from datasource.model.user_entity import UserEntity
from datasource.mapper import player_stats_mapper
from domain.model.player_stats import PlayerStats
from typing import Optional, List
from sqlalchemy import desc

class PlayerStatsRepository:
    def __init__(self):
        pass

    def save(self, player_stats: PlayerStats) -> None:
        entity = player_stats_mapper.to_entity(player_stats)
        existing = db.session.get(PlayerStatsEntity, entity.uuid)
        
        if existing:
            existing.wins = entity.wins
            existing.losses = entity.losses
            existing.draws = entity.draws
            existing.total_games = entity.total_games
            existing.win_ratio = entity.win_ratio
            existing.updated_at = entity.updated_at
        else:
            db.session.add(entity)
        
        db.session.commit()

    def get_by_user_uuid(self, user_uuid: str) -> Optional[PlayerStats]:
        entity = db.session.query(PlayerStatsEntity).filter_by(user_uuid=user_uuid).first()
        if entity is None:
            return None
        return player_stats_mapper.to_domain(entity)

    def get_top_players_with_stats(self, limit: int) -> List[dict]:
        result = db.session.query(
            PlayerStatsEntity.user_uuid,
            PlayerStatsEntity.wins,
            PlayerStatsEntity.losses,
            PlayerStatsEntity.draws,
            PlayerStatsEntity.total_games,
            PlayerStatsEntity.win_ratio,
            UserEntity.login
        ).join(
            UserEntity,
            PlayerStatsEntity.user_uuid == UserEntity.uuid
        ).filter(
            PlayerStatsEntity.total_games > 0
        ).order_by(
            desc(PlayerStatsEntity.win_ratio)
        ).limit(limit).all()
        
        return [
            {
                'user_uuid': row.user_uuid,
                'login': row.login,
                'wins': row.wins,
                'losses': row.losses,
                'draws': row.draws,
                'total_games': row.total_games,
                'win_ratio': round(row.win_ratio, 3)
            }
            for row in result
        ]