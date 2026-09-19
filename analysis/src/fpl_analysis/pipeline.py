"""Orchestrates one end-to-end analysis run for a manager.

Fetches from the FPL API exactly once per endpoint, threading the parsed
data through the rest of the analysis modules. Building fine-grained
per-gameweek metrics (Trend/Consistency/DEFCON) requires one element-summary
call per player -- fetching that for the *entire* player pool (600+
players) on every run would be slow and impolite to an unofficial API, so
buy candidates are first cheaply shortlisted using bootstrap-static's own
season-aggregate `form` figure, and only the shortlist gets the fine-grained
treatment.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from fpl_analysis.consistency import compute_consistency
from fpl_analysis.defcon import defcon_hit_rate
from fpl_analysis.fixtures import DEFAULT_HORIZON, next_n_fixtures
from fpl_analysis.fpl_client import FplClient
from fpl_analysis.free_transfers import derive_ft_bank
from fpl_analysis.models import (
    PlayerAnalysis,
    SquadPlayer,
    TransferSuggestion,
    build_squad,
    gw_stats_from_element_summary,
    transfer_activity_from_history,
    transfer_records_from_transfers,
)
from fpl_analysis.sell_price import derive_bought_price
from fpl_analysis.suggestions import score_pool, suggest_transfers
from fpl_analysis.trend import compute_trend

SHORTLIST_SIZE_PER_POSITION = 15
TREND_WINDOW = 8
_POSITION_BY_TYPE_ID = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
_AVAILABLE_STATUSES = {"a", "d"}  # exclude injured/suspended/unavailable from buy candidates


@dataclass(frozen=True)
class AnalysisResult:
    entry_id: int
    manager_name: str
    team_name: str
    overall_rank: int
    total_points: int
    gameweek: int
    next_deadline: str | None
    is_current_gw_finished: bool
    bank: int  # tenths of £m
    team_value: int  # tenths of £m
    free_transfers: int
    teams: dict[int, str]  # club_id -> club name
    squad: list[SquadPlayer]
    squad_analysis: list[PlayerAnalysis]
    squad_quality_scores: dict[int, float]  # player_id -> quality_score
    bought_prices: dict[int, int]  # player_id -> tenths of £m
    points_trend: list[dict]  # [{event, points, overall_rank}, ...]
    suggestions: list[TransferSuggestion]


RECENT_POINTS_COUNT = 5


def _current_event(bootstrap_static: dict) -> dict:
    for event in bootstrap_static["events"]:
        if event["is_current"]:
            return event
    return bootstrap_static["events"][0]


def _next_deadline(bootstrap_static: dict, current_gw: int) -> str | None:
    for event in bootstrap_static["events"]:
        if event["id"] == current_gw + 1:
            return event["deadline_time"]
    return None


def _minutes_reliability(gw_stats, window: int = TREND_WINDOW) -> float | None:
    """Fraction of the last `window` gameweeks with a starter-length appearance.

    Unlike Trend/Consistency, this deliberately does NOT filter out unplayed
    gameweeks -- being benched or injured *is* the rotation-risk signal this
    metric exists to capture.
    """
    recent = gw_stats[-window:]
    if not recent:
        return None
    return sum(1 for g in recent if g.minutes >= 60) / len(recent)


def _analyze_player(
    element: dict, client: FplClient, fixtures: list[dict], from_event: int
) -> PlayerAnalysis:
    gw_stats = gw_stats_from_element_summary(client.get_element_summary(element["id"]))
    position = _POSITION_BY_TYPE_ID[element["element_type"]]
    fixture_difficulty_next = next_n_fixtures(
        fixtures, club_id=element["team"], from_event=from_event, horizon=DEFAULT_HORIZON
    )
    return PlayerAnalysis(
        player_id=element["id"],
        web_name=element["web_name"],
        position=position,
        club_id=element["team"],
        now_cost=element["now_cost"],
        status=element["status"],
        chance_of_playing_next_round=element["chance_of_playing_next_round"],
        total_points_season=element["total_points"],
        recent_points=[g.points for g in gw_stats[-RECENT_POINTS_COUNT:]],
        trend=compute_trend(gw_stats, window=TREND_WINDOW),
        consistency=compute_consistency(gw_stats, window=TREND_WINDOW),
        defcon_hit_rate=defcon_hit_rate(gw_stats, position),
        minutes_reliability=_minutes_reliability(gw_stats),
        fixture_difficulty_next=fixture_difficulty_next,
    )


def _shortlist_candidate_ids(
    bootstrap_static: dict, owned_ids: set[int], shortlist_size: int = SHORTLIST_SIZE_PER_POSITION
) -> list[int]:
    """Cheaply rank non-owned players by FPL's own `form` figure, per position,
    to bound how many element-summary calls the fine-grained analysis needs.
    """
    by_position: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    for element in bootstrap_static["elements"]:
        if element["id"] in owned_ids or element["status"] not in _AVAILABLE_STATUSES:
            continue
        by_position[element["element_type"]].append(element)

    shortlisted: list[int] = []
    for elements in by_position.values():
        elements.sort(key=lambda e: float(e["form"]), reverse=True)
        shortlisted.extend(e["id"] for e in elements[:shortlist_size])
    return shortlisted


def run(entry_id: int, client: FplClient | None = None) -> AnalysisResult:
    client = client or FplClient()

    bootstrap_static = client.get_bootstrap_static()
    fixtures = client.get_fixtures()
    entry = client.get_entry(entry_id)
    entry_history = client.get_entry_history(entry_id)
    entry_transfers = client.get_entry_transfers(entry_id)

    current_gw = _current_event(bootstrap_static)["id"]
    try:
        picks = client.get_entry_picks(entry_id, current_gw)
    except requests.HTTPError:  # current GW picks 404 until its deadline passes
        picks = client.get_entry_picks(entry_id, current_gw - 1)
        current_gw -= 1

    squad = build_squad(bootstrap_static, picks)
    elements_by_id = {e["id"]: e for e in bootstrap_static["elements"]}

    squad_analysis = [
        _analyze_player(elements_by_id[p.player_id], client, fixtures, current_gw + 1)
        for p in squad
    ]

    owned_ids = {p.player_id for p in squad}
    candidate_ids = _shortlist_candidate_ids(bootstrap_static, owned_ids)
    candidate_analysis = [
        _analyze_player(elements_by_id[cid], client, fixtures, current_gw + 1)
        for cid in candidate_ids
    ]

    transfer_records = transfer_records_from_transfers(entry_transfers)
    bought_prices = {
        p.player_id: derive_bought_price(
            transfer_records,
            p.player_id,
            gw1_price=elements_by_id[p.player_id]["now_cost"],
        )
        for p in squad
    }

    club_counts: dict[int, int] = {}
    for p in squad:
        club_counts[p.club_id] = club_counts.get(p.club_id, 0) + 1

    latest_gw_state = entry_history["current"][-1]
    free_transfers = derive_ft_bank(transfer_activity_from_history(entry_history))

    suggestions = suggest_transfers(
        squad=squad_analysis,
        candidate_pool=candidate_analysis,
        free_transfers=free_transfers,
        bank=latest_gw_state["bank"],
        bought_prices=bought_prices,
        club_counts=club_counts,
    )

    quality_scores = score_pool(squad_analysis + candidate_analysis)
    current_event = next(e for e in bootstrap_static["events"] if e["id"] == current_gw)
    teams = {t["id"]: t["name"] for t in bootstrap_static["teams"]}
    points_trend = [
        {"event": gw["event"], "points": gw["points"], "overall_rank": gw["overall_rank"]}
        for gw in entry_history["current"]
    ]

    return AnalysisResult(
        entry_id=entry_id,
        manager_name=f"{entry['player_first_name']} {entry['player_last_name']}",
        team_name=entry["name"],
        overall_rank=entry["summary_overall_rank"],
        total_points=entry["summary_overall_points"],
        gameweek=current_gw,
        next_deadline=_next_deadline(bootstrap_static, current_gw),
        is_current_gw_finished=current_event["finished"],
        bank=latest_gw_state["bank"],
        team_value=latest_gw_state["value"],
        free_transfers=free_transfers,
        teams=teams,
        squad=squad,
        squad_analysis=squad_analysis,
        squad_quality_scores={pid: quality_scores[pid] for pid in owned_ids},
        bought_prices=bought_prices,
        points_trend=points_trend,
        suggestions=suggestions,
    )
