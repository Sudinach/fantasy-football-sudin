"""Narrow, hand-picked types built from the raw FPL API dicts.

We deliberately don't validate the full API payload shape (it's undocumented
and evolves season-to-season) -- these dataclasses only carry the fields the
analysis code actually needs, built by small adapter functions below.
"""

from __future__ import annotations

from dataclasses import dataclass

_POSITION_BY_TYPE_ID = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

_STATUS_LABELS = {
    "a": "available",
    "d": "doubtful",
    "i": "injured",
    "s": "suspended",
    "u": "unavailable",
    "n": "not available",
}


@dataclass(frozen=True)
class SquadPlayer:
    player_id: int
    web_name: str
    club: str
    club_id: int
    position: str
    squad_slot: int  # 1-11 starting, 12-15 bench, per the picks endpoint's `position` field
    is_captain: bool
    is_vice_captain: bool
    now_cost: float  # decimal £m
    status: str
    news: str


def build_squad(bootstrap_static: dict, picks: dict) -> list[SquadPlayer]:
    """Combine bootstrap-static (player/team reference data) with one gameweek's
    picks (a manager's actual squad) into a list of SquadPlayer.
    """
    elements_by_id = {element["id"]: element for element in bootstrap_static["elements"]}
    teams_by_id = {team["id"]: team["name"] for team in bootstrap_static["teams"]}

    squad = []
    for pick in picks["picks"]:
        element = elements_by_id[pick["element"]]
        squad.append(
            SquadPlayer(
                player_id=element["id"],
                web_name=element["web_name"],
                club=teams_by_id[element["team"]],
                club_id=element["team"],
                position=_POSITION_BY_TYPE_ID[element["element_type"]],
                squad_slot=pick["position"],
                is_captain=pick["is_captain"],
                is_vice_captain=pick["is_vice_captain"],
                now_cost=element["now_cost"] / 10,
                status=_STATUS_LABELS.get(element["status"], element["status"]),
                news=element["news"],
            )
        )
    return sorted(squad, key=lambda p: p.squad_slot)


@dataclass(frozen=True)
class GwStatLine:
    """One player's stat line for one gameweek, from element-summary's `history`."""

    event: int
    points: int
    minutes: int
    clearances_blocks_interceptions: int
    tackles: int
    recoveries: int


def gw_stats_from_element_summary(element_summary: dict) -> list[GwStatLine]:
    return [
        GwStatLine(
            event=entry["round"],
            points=entry["total_points"],
            minutes=entry["minutes"],
            clearances_blocks_interceptions=entry["clearances_blocks_interceptions"],
            tackles=entry["tackles"],
            recoveries=entry["recoveries"],
        )
        for entry in element_summary["history"]
    ]


@dataclass(frozen=True)
class GwTransferActivity:
    """One gameweek's transfer activity for a manager, from entry/history."""

    event: int
    transfers_made: int
    chip_played: str | None  # "wildcard" | "freehit" | "bboost" | "3xc" | None


def transfer_activity_from_history(entry_history: dict) -> list[GwTransferActivity]:
    chip_by_event = {chip["event"]: chip["name"] for chip in entry_history["chips"]}
    return [
        GwTransferActivity(
            event=gw["event"],
            transfers_made=gw["event_transfers"],
            chip_played=chip_by_event.get(gw["event"]),
        )
        for gw in entry_history["current"]
    ]


@dataclass(frozen=True)
class TransferRecord:
    """One transfer a manager made, from entry/transfers."""

    event: int
    element_in: int
    element_in_cost: int  # tenths of £m, FPL's native unit
    element_out: int
    element_out_cost: int


def transfer_records_from_transfers(transfers: list[dict]) -> list[TransferRecord]:
    return [
        TransferRecord(
            event=t["event"],
            element_in=t["element_in"],
            element_in_cost=t["element_in_cost"],
            element_out=t["element_out"],
            element_out_cost=t["element_out_cost"],
        )
        for t in transfers
    ]


@dataclass(frozen=True)
class FixtureDifficulty:
    event: int
    opponent_club_id: int
    is_home: bool
    difficulty: int  # FPL's 1 (easiest) - 5 (hardest) rating


@dataclass(frozen=True)
class PlayerAnalysis:
    """A player's computed analysis signals, ready for scoring in suggestions.py."""

    player_id: int
    web_name: str
    position: str
    club_id: int
    now_cost: int  # tenths of £m
    status: str
    chance_of_playing_next_round: int | None
    total_points_season: int
    recent_points: list[int]  # last few gameweeks' raw points, zeros included
    trend: float | None
    consistency: float | None
    defcon_hit_rate: float | None
    minutes_reliability: float | None
    fixture_difficulty_next: list[FixtureDifficulty]


@dataclass(frozen=True)
class TransferSuggestion:
    player_out: PlayerAnalysis
    player_in: PlayerAnalysis
    cost_delta: float  # decimal £m, positive means spending more
    projected_point_gain: float
    hit_cost: int
    net_projected_gain: float
    free_transfers_available: int
    rationale: list[str]


@dataclass(frozen=True)
class ChipWindow:
    """One playable instance of a transfer-affecting Chip, from bootstrap-static's `chips`."""

    name: str  # "wildcard" | "freehit"
    window_number: int  # 1 (first half of the season) or 2 (second half)
    start_event: int
    stop_event: int


@dataclass(frozen=True)
class ChipStatus:
    """A ChipWindow cross-referenced with one manager's play history."""

    name: str
    window_number: int
    start_event: int
    stop_event: int
    played_event: int | None
    is_available: bool  # not yet played, and the current gameweek falls within the window


@dataclass(frozen=True)
class ChipAdvice:
    chip: str  # "wildcard" | "freehit"
    is_available: bool
    recommended: bool
    target_gameweek: int | None  # the gameweek the advice applies to, when recommended
    reasoning: list[str]
