"""Assembles and serializes the Snapshot -- the JSON contract between this
Python analysis job and the Next.js frontend (see docs/adr/0001 and
CONTEXT.md's "Snapshot" definition). Money is converted from FPL's native
tenths-of-£m integers to decimal £m only here, at the boundary -- nothing
upstream of this module deals in decimal money.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fpl_analysis.fixtures import DEFAULT_HORIZON
from fpl_analysis.pipeline import TREND_WINDOW, AnalysisResult
from fpl_analysis.sell_price import compute_sell_price
from fpl_analysis.suggestions import WEIGHTS

SCHEMA_VERSION = 1


def _pounds(tenths: int) -> float:
    return round(tenths / 10, 1)


def _rounded(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def _fixture_dicts(result: AnalysisResult, fixtures) -> list[dict]:
    return [
        {
            "event": f.event,
            "opponent": result.teams.get(f.opponent_club_id, "Unknown"),
            "is_home": f.is_home,
            "difficulty": f.difficulty,
        }
        for f in fixtures
    ]


def _squad_player_dict(result: AnalysisResult, squad_player, analysis) -> dict:
    bought_price = result.bought_prices[squad_player.player_id]
    sell_price = compute_sell_price(bought_price, analysis.now_cost)
    return {
        "player_id": squad_player.player_id,
        "web_name": squad_player.web_name,
        "club": squad_player.club,
        "club_id": squad_player.club_id,
        "position": squad_player.position,
        "squad_role": "starting" if squad_player.squad_slot <= 11 else "bench",
        "is_captain": squad_player.is_captain,
        "is_vice_captain": squad_player.is_vice_captain,
        "now_cost": _pounds(analysis.now_cost),
        "bought_price": _pounds(bought_price),
        "sell_price": _pounds(sell_price),
        "status": squad_player.status,
        "news": squad_player.news,
        "chance_of_playing_next_round": analysis.chance_of_playing_next_round,
        "total_points_season": analysis.total_points_season,
        "recent_gw_points": analysis.recent_points,
        "trend": _rounded(analysis.trend),
        "consistency": _rounded(analysis.consistency),
        "defcon_hit_rate": _rounded(analysis.defcon_hit_rate),
        "fixture_difficulty_next_3": _fixture_dicts(result, analysis.fixture_difficulty_next),
        "quality_score": round(result.squad_quality_scores[squad_player.player_id], 1),
    }


def _suggestion_dict(result: AnalysisResult, suggestion, suggestion_id: str) -> dict:
    def _player_ref(p) -> dict:
        return {"player_id": p.player_id, "web_name": p.web_name, "position": p.position}

    return {
        "id": suggestion_id,
        "player_out": _player_ref(suggestion.player_out),
        "player_in": _player_ref(suggestion.player_in),
        "cost_delta": round(suggestion.cost_delta, 1),
        "projected_point_gain": suggestion.projected_point_gain,
        "hit_cost": suggestion.hit_cost,
        "net_projected_gain": suggestion.net_projected_gain,
        "free_transfers_available_at_suggestion": suggestion.free_transfers_available,
        "rationale": suggestion.rationale,
    }


def _chip_advice_dict(advice) -> dict:
    return {
        "chip": advice.chip,
        "is_available": advice.is_available,
        "recommended": advice.recommended,
        "target_gameweek": advice.target_gameweek,
        "reasoning": advice.reasoning,
    }


def build_snapshot(result: AnalysisResult) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gameweek": {
            "current": result.gameweek,
            "next_deadline": result.next_deadline,
            "is_current_gw_finished": result.is_current_gw_finished,
        },
        "manager": {
            "entry_id": result.entry_id,
            "team_name": result.team_name,
            "manager_name": result.manager_name,
            "overall_rank": result.overall_rank,
            "total_points": result.total_points,
            "bank": _pounds(result.bank),
            "team_value": _pounds(result.team_value),
            "free_transfers_available": result.free_transfers,
        },
        "squad": [
            _squad_player_dict(result, sp, pa)
            for sp, pa in zip(result.squad, result.squad_analysis, strict=True)
        ],
        "points_trend": {"by_gameweek": result.points_trend},
        "suggestions": [
            _suggestion_dict(result, s, f"gw{result.gameweek}-{i + 1:03d}")
            for i, s in enumerate(result.suggestions)
        ],
        "chip_advice": [_chip_advice_dict(a) for a in result.chip_advice],
        "meta": {
            "analysis_horizon_gws": DEFAULT_HORIZON,
            "trend_window_gws": TREND_WINDOW,
            "scoring_weights": WEIGHTS,
            "source_data_as_of_event": result.gameweek,
        },
    }
