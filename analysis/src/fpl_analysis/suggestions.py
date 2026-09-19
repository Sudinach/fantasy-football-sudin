"""Scores players and ranks candidate replacements into Transfer Suggestions.

Suggestions are advisory only (see docs/adr/0002) -- this module never talks
to the API or executes anything, it just ranks already-fetched PlayerAnalysis
data. Each suggestion is a single, independent swap; this app doesn't reason
about bundling several transfers together in v1.
"""

from __future__ import annotations

from fpl_analysis.fixtures import fixture_ease_multiplier
from fpl_analysis.models import PlayerAnalysis, TransferSuggestion
from fpl_analysis.sell_price import compute_sell_price

WEIGHTS = {
    "trend": 0.40,
    "consistency": 0.25,
    "fixture_ease": 0.20,
    "defcon_hit_rate": 0.10,
    "minutes_reliability": 0.05,
}

HIT_COST_PER_TRANSFER = 4
HIT_SAFETY_MARGIN = 2.0
MAX_SUGGESTIONS = 5
MAX_PER_CLUB = 3


def _normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def _metric(player: PlayerAnalysis, name: str) -> float:
    if name == "fixture_ease":
        return fixture_ease_multiplier(player.fixture_difficulty_next)
    value = getattr(player, name)
    return value if value is not None else 0.0


def score_pool(pool: list[PlayerAnalysis]) -> dict[int, float]:
    """quality_score (0-100) for every player in `pool`, normalized against each other."""
    if not pool:
        return {}
    normalized_by_metric = {name: _normalize([_metric(p, name) for p in pool]) for name in WEIGHTS}
    return {
        player.player_id: 100 * sum(WEIGHTS[name] * normalized_by_metric[name][i] for name in WEIGHTS)
        for i, player in enumerate(pool)
    }


def _expected_points_per_gw(player: PlayerAnalysis) -> float:
    base = player.trend if player.trend is not None else 0.0
    return base * fixture_ease_multiplier(player.fixture_difficulty_next)


def _build_rationale(sell: PlayerAnalysis, buy: PlayerAnalysis, hit_cost: int) -> list[str]:
    lines = []
    if sell.trend is not None and buy.trend is not None:
        lines.append(
            f"{sell.web_name}'s recent trend ({sell.trend:.1f}) trails {buy.web_name}'s ({buy.trend:.1f})."
        )
    if buy.fixture_difficulty_next:
        difficulties = ", ".join(str(f.difficulty) for f in buy.fixture_difficulty_next)
        lines.append(f"{buy.web_name}'s next fixtures: difficulty {difficulties}.")
    lines.append(f"Costs a {hit_cost}-point hit, but projected gain still clears it." if hit_cost else "No hit required.")
    return lines


def suggest_transfers(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    free_transfers: int,
    bank: int,
    bought_prices: dict[int, int],
    club_counts: dict[int, int],
    horizon: int = 3,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> list[TransferSuggestion]:
    """Rank potential single-player swaps.

    `bank` and `bought_prices` values are in FPL's native tenths-of-£m units.
    `club_counts` reflects the *current* squad's club composition.
    """
    scores = score_pool(squad + candidate_pool)
    squad_ids = {p.player_id for p in squad}
    sell_candidates = sorted(squad, key=lambda p: scores[p.player_id])

    suggestions: list[TransferSuggestion] = []
    for sell_candidate in sell_candidates:
        sell_price = compute_sell_price(bought_prices[sell_candidate.player_id], sell_candidate.now_cost)
        available_budget = sell_price + bank

        buy_candidates = sorted(
            (
                c
                for c in candidate_pool
                if c.player_id not in squad_ids
                and c.position == sell_candidate.position
                and c.now_cost <= available_budget
                and (c.club_id == sell_candidate.club_id or club_counts.get(c.club_id, 0) < MAX_PER_CLUB)
                and scores[c.player_id] > scores[sell_candidate.player_id]
            ),
            key=lambda c: scores[c.player_id],
            reverse=True,
        )
        if not buy_candidates:
            continue
        buy_candidate = buy_candidates[0]

        projected_gain = (
            _expected_points_per_gw(buy_candidate) - _expected_points_per_gw(sell_candidate)
        ) * horizon
        hit_cost = HIT_COST_PER_TRANSFER if free_transfers < 1 else 0
        if hit_cost and projected_gain < hit_cost + HIT_SAFETY_MARGIN:
            continue

        suggestions.append(
            TransferSuggestion(
                player_out=sell_candidate,
                player_in=buy_candidate,
                cost_delta=(buy_candidate.now_cost - sell_price) / 10,
                projected_point_gain=round(projected_gain, 1),
                hit_cost=hit_cost,
                net_projected_gain=round(projected_gain - hit_cost, 1),
                free_transfers_available=free_transfers,
                rationale=_build_rationale(sell_candidate, buy_candidate, hit_cost),
            )
        )

    suggestions.sort(key=lambda s: s.net_projected_gain, reverse=True)
    return suggestions[:max_suggestions]
