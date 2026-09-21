"""Advisory-only recommendations on whether to play Wildcard or Free Hit.

Like suggestions.py, this module never talks to the API or executes anything
(see docs/adr/0002) -- it just scores already-fetched data. Chip Advice is a
coarser signal than a Transfer Suggestion: it doesn't propose a new squad,
just whether *now* looks like a good moment to burn the chip.
"""

from __future__ import annotations

from fpl_analysis.models import ChipAdvice, ChipStatus, PlayerAnalysis

WEAK_LINK_SCORE_GAP = 15.0
WEAK_LINK_COUNT_THRESHOLD = 3
HIT_COST_PER_TRANSFER = 4

BLANK_GW_SQUAD_THRESHOLD = 3
FREE_HIT_SCAN_HORIZON = 8


def _unavailable_reason(status: ChipStatus) -> str:
    if status.played_event is not None:
        return f"Already played this window, in GW{status.played_event}."
    return f"Opens in GW{status.start_event}."


def wildcard_advice(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    scores: dict[int, float],
    free_transfers: int,
    status: ChipStatus,
) -> ChipAdvice:
    """Recommends Wildcard when several squad players are well behind the best
    available replacement in their position -- fixing them one at a time would
    cost more Hits than the manager's Free Transfers cover.
    """
    if not status.is_available:
        return ChipAdvice("wildcard", False, False, None, [_unavailable_reason(status)])

    best_score_by_position: dict[str, float] = {}
    for candidate in candidate_pool:
        best_score_by_position[candidate.position] = max(
            best_score_by_position.get(candidate.position, 0.0), scores.get(candidate.player_id, 0.0)
        )

    weak_links = [
        p
        for p in squad
        if best_score_by_position.get(p.position, 0.0) - scores.get(p.player_id, 0.0) >= WEAK_LINK_SCORE_GAP
    ]

    if len(weak_links) < WEAK_LINK_COUNT_THRESHOLD:
        return ChipAdvice(
            "wildcard",
            True,
            False,
            None,
            [f"Only {len(weak_links)} squad player(s) are clearly outclassed -- not enough to justify a rebuild."],
        )

    hits_avoided = max(0, len(weak_links) - free_transfers) * HIT_COST_PER_TRANSFER
    names = ", ".join(p.web_name for p in weak_links)
    reasoning = [f"{len(weak_links)} squad players trail the best available replacement in their position: {names}."]
    if hits_avoided:
        reasoning.append(
            f"Fixing them via normal transfers would cost {hits_avoided} points in Hits with "
            f"{free_transfers} free transfer(s) banked; Wildcard fixes them all for free."
        )
    else:
        reasoning.append(
            "Your free transfers cover them without a Hit, but Wildcard lets you fix them all "
            "at once and re-optimise the rest of the squad in the same move."
        )
    return ChipAdvice("wildcard", True, True, None, reasoning)


def _blank_gw_counts(
    squad_club_ids: list[int], fixtures: list[dict], from_event: int, to_event: int
) -> dict[int, int]:
    counts: dict[int, int] = {}
    for event in range(from_event, to_event + 1):
        clubs_with_fixture = {
            club_id for f in fixtures if f["event"] == event for club_id in (f["team_h"], f["team_a"])
        }
        counts[event] = sum(1 for club_id in squad_club_ids if club_id not in clubs_with_fixture)
    return counts


def free_hit_advice(
    squad_club_ids: list[int],
    fixtures: list[dict],
    current_gw: int,
    status: ChipStatus,
) -> ChipAdvice:
    """Recommends Free Hit for the worst upcoming Blank Gameweek within the
    scan horizon, if it hits enough of the squad to be worth burning the chip.
    """
    if not status.is_available:
        return ChipAdvice("freehit", False, False, None, [_unavailable_reason(status)])

    scan_to = min(status.stop_event, current_gw + FREE_HIT_SCAN_HORIZON)
    counts = _blank_gw_counts(squad_club_ids, fixtures, current_gw + 1, scan_to)
    worst_event = max(counts, key=lambda e: counts[e], default=None)

    if worst_event is None or counts[worst_event] < BLANK_GW_SQUAD_THRESHOLD:
        return ChipAdvice(
            "freehit",
            True,
            False,
            None,
            [
                (
                    f"No blank gameweek hits {BLANK_GW_SQUAD_THRESHOLD}+ of your squad's clubs in the "
                    f"next {FREE_HIT_SCAN_HORIZON} gameweeks -- save it."
                )
            ],
        )

    return ChipAdvice(
        "freehit",
        True,
        True,
        worst_event,
        [
            f"{counts[worst_event]} of your squad's clubs have no fixture in GW{worst_event} (blank gameweek).",
            (
                "Free Hit lets you field a full replacement XI for that gameweek only; your squad "
                "reverts automatically afterwards."
            ),
        ],
    )
