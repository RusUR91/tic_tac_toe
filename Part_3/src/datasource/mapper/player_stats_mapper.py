from domain.model.player_stats import PlayerStats
from datasource.model.player_stats_entity import PlayerStatsEntity
from datetime import datetime

def to_entity(player_stats: PlayerStats) -> PlayerStatsEntity:
    return PlayerStatsEntity(
        player_stats.uuid,
        player_stats.user_uuid,
        player_stats.wins,
        player_stats.losses,
        player_stats.draws,
        player_stats.total_games,
        player_stats.win_ratio,
        player_stats.updated_at
    )

def to_domain(entity: PlayerStatsEntity) -> PlayerStats:
    return PlayerStats(
        entity.uuid,
        entity.user_uuid,
        entity.wins,
        entity.losses,
        entity.draws,
        entity.total_games,
        entity.win_ratio,
        entity.updated_at
    )