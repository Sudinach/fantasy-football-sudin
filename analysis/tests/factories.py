"""Small synthetic-data builders shared across analysis-module tests."""

from fpl_analysis.models import (
    FixtureDifficulty,
    GwStatLine,
    GwTransferActivity,
    PlayerAnalysis,
    SquadPlayer,
)


def gw(event: int, points: int, minutes: int = 90, cbi: int = 0, tackles: int = 0, recoveries: int = 0) -> GwStatLine:
    return GwStatLine(
        event=event,
        points=points,
        minutes=minutes,
        clearances_blocks_interceptions=cbi,
        tackles=tackles,
        recoveries=recoveries,
    )


def activity(event: int, transfers_made: int = 0, chip_played: str | None = None) -> GwTransferActivity:
    return GwTransferActivity(event=event, transfers_made=transfers_made, chip_played=chip_played)


def fixture_difficulty(event: int = 1, opponent: int = 999, is_home: bool = True, difficulty: int = 3) -> FixtureDifficulty:
    return FixtureDifficulty(event=event, opponent_club_id=opponent, is_home=is_home, difficulty=difficulty)


def player(
    player_id: int,
    web_name: str = "Player",
    position: str = "MID",
    club_id: int = 1,
    now_cost: int = 50,
    status: str = "available",
    chance_of_playing_next_round: int | None = 100,
    total_points_season: int = 0,
    recent_points: list[int] | None = None,
    trend: float | None = 5.0,
    consistency: float | None = 0.5,
    defcon_hit_rate: float | None = 0.0,
    minutes_reliability: float | None = 1.0,
    fixture_difficulty_next: list[FixtureDifficulty] | None = None,
) -> PlayerAnalysis:
    return PlayerAnalysis(
        player_id=player_id,
        web_name=web_name,
        position=position,
        club_id=club_id,
        now_cost=now_cost,
        status=status,
        chance_of_playing_next_round=chance_of_playing_next_round,
        total_points_season=total_points_season,
        recent_points=recent_points if recent_points is not None else [],
        trend=trend,
        consistency=consistency,
        defcon_hit_rate=defcon_hit_rate,
        minutes_reliability=minutes_reliability,
        fixture_difficulty_next=fixture_difficulty_next or [fixture_difficulty()],
    )


def squad_player(
    player_id: int,
    web_name: str = "Player",
    club: str = "Some FC",
    club_id: int = 1,
    position: str = "MID",
    squad_slot: int = 1,
    is_captain: bool = False,
    is_vice_captain: bool = False,
    now_cost: float = 5.0,
    status: str = "available",
    news: str = "",
) -> SquadPlayer:
    return SquadPlayer(
        player_id=player_id,
        web_name=web_name,
        club=club,
        club_id=club_id,
        position=position,
        squad_slot=squad_slot,
        is_captain=is_captain,
        is_vice_captain=is_vice_captain,
        now_cost=now_cost,
        status=status,
        news=news,
    )
