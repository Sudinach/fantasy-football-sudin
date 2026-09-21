"""Scores players and ranks candidate replacements into Transfer Suggestions.

Suggestions are advisory only (see docs/adr/0002) -- this module never talks
to the API or executes anything, it just ranks already-fetched PlayerAnalysis
data. Each suggestion is a single, independent sell decision paired with a
ranked shortlist of replacements; this app doesn't reason about bundling
several *sells* together in v1.
"""

from __future__ import annotations

from fpl_analysis.fixtures import fixture_ease_multiplier
from fpl_analysis.models import BuyOption, PlayerAnalysis, TransferSuggestion
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
MAX_ALTERNATIVES = 3


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


def _buy_option(
    sell_candidate: PlayerAnalysis,
    buy_candidate: PlayerAnalysis,
    sell_price: int,
    hit_cost: int,
    scores: dict[int, float],
    horizon: int,
) -> BuyOption:
    projected_gain = (_expected_points_per_gw(buy_candidate) - _expected_points_per_gw(sell_candidate)) * horizon
    return BuyOption(
        player_in=buy_candidate,
        cost_delta=round((buy_candidate.now_cost - sell_price) / 10, 1),
        projected_point_gain=round(projected_gain, 1),
        net_projected_gain=round(projected_gain - hit_cost, 1),
        quality_score=round(scores[buy_candidate.player_id], 1),
        rationale=_build_rationale(sell_candidate, buy_candidate, hit_cost),
    )


def suggest_transfers(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    free_transfers: int,
    bank: int,
    bought_prices: dict[int, int],
    club_counts: dict[int, int],
    horizon: int = 3,
    max_suggestions: int = MAX_SUGGESTIONS,
    max_alternatives: int = MAX_ALTERNATIVES,
) -> list[TransferSuggestion]:
    """Rank which squad players are worth selling, each with a ranked shortlist
    of replacements (best first) rather than a single fixed pick -- so the
    same in-demand replacement can show up as an option under more than one
    sell candidate without the list reading as flatly duplicated suggestions.

    `bank` and `bought_prices` values are in FPL's native tenths-of-£m units.
    `club_counts` reflects the *current* squad's club composition.
    """
    scores = score_pool(squad + candidate_pool)
    squad_ids = {p.player_id for p in squad}
    sell_candidates = sorted(squad, key=lambda p: scores[p.player_id])
    hit_cost = HIT_COST_PER_TRANSFER if free_transfers < 1 else 0

    suggestions: list[TransferSuggestion] = []
    for sell_candidate in sell_candidates:
        sell_price = compute_sell_price(bought_prices[sell_candidate.player_id], sell_candidate.now_cost)
        available_budget = sell_price + bank

        buy_candidates = (
            c
            for c in candidate_pool
            if c.player_id not in squad_ids
            and c.position == sell_candidate.position
            and c.now_cost <= available_budget
            and (c.club_id == sell_candidate.club_id or club_counts.get(c.club_id, 0) < MAX_PER_CLUB)
            and scores[c.player_id] > scores[sell_candidate.player_id]
        )

        # Rank by this swap's own net_projected_gain (not quality_score, which
        # is a generic all-round rating) -- that's the number actually being
        # compared, so it's what "best" needs to mean here.
        options = sorted(
            (_buy_option(sell_candidate, c, sell_price, hit_cost, scores, horizon) for c in buy_candidates),
            key=lambda o: o.net_projected_gain,
            reverse=True,
        )
        if hit_cost:
            options = [o for o in options if o.projected_point_gain >= hit_cost + HIT_SAFETY_MARGIN]
        options = options[:max_alternatives]
        if not options:
            continue

        suggestions.append(
            TransferSuggestion(
                player_out=sell_candidate,
                options=options,
                hit_cost=hit_cost,
                free_transfers_available=free_transfers,
            )
        )

    suggestions.sort(key=lambda s: s.options[0].net_projected_gain, reverse=True)
    return suggestions[:max_suggestions]
