"""Turns a recommended Chip into the actual transfers to make with it.

chip_advice.py answers *whether* to burn Wildcard or Free Hit; this module
answers what to do with it -- the concrete out/in pairs that get the manager
from their current squad to the one the chip pays for. Advisory only, like
suggestions.py (see docs/adr/0002): nothing here talks to the API or submits
anything.

The search is a greedy hill-climb: repeatedly apply the single highest-gain
affordable swap, until no improving swap is left. That is not a provably
optimal squad -- picking 15 players under a budget is a knapsack problem, and
an exhaustive search over the candidate pool would be far more machinery than
a personal dashboard warrants -- but it is cheap, deterministic, and never
proposes a swap that is worse than doing nothing. Its one real blind spot is
budget myopia: an early expensive upgrade can crowd out two cheaper ones that
would together have been worth more.

Every swap is same-position, so a plan that starts from the manager's (valid)
squad can't break FPL's 2/5/5/3 positional split -- only the max-3-per-club
rule needs checking as swaps are applied.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean

from fpl_analysis.fixtures import DEFAULT_HORIZON, fixture_ease_multiplier, fixtures_in_event
from fpl_analysis.models import ChipPlan, FixtureDifficulty, PlannedTransfer, PlayerAnalysis
from fpl_analysis.sell_price import compute_sell_price
from fpl_analysis.suggestions import MAX_PER_CLUB

FREE_HIT_HORIZON = 1  # the squad reverts after the target gameweek, so only it counts

# How much of a player's projection comes from Trend (form, trajectory-aware)
# rather than their raw recent per-gameweek scoring. An even split: Trend sees
# a player heating up or cooling off, raw scoring keeps a short hot streak
# from being mistaken for a new baseline.
TREND_WEIGHT = 0.5

# Below this, a swap is churn rather than an upgrade: the projections aren't
# precise enough for a fraction of a point per gameweek to mean anything.
MIN_GAIN_PER_GW = 0.5

# A plan can't sell more than the squad it starts from.
MAX_PLAN_TRANSFERS = 15

WindowFixtures = dict[int, list[FixtureDifficulty]]


def _points_per_gameweek(player: PlayerAnalysis) -> float:
    """A fixture-neutral estimate of what this player scores in a gameweek.

    Trend alone is the wrong base for a rebuild. It's computed over *played*
    gameweeks only (see trend.py) and leans on trajectory, so a £4.5m squad
    filler who has just started two games out-trends a cooling premium -- a
    bias suggestions.py can live with over one or two swaps, but one that
    compounds into an absurd squad once a plan makes a dozen. So Trend is
    first made unconditional (times the share of gameweeks the player
    actually starts) and then averaged with their raw recent scoring,
    unplayed gameweeks and all, which is already an honest per-gameweek rate.
    """
    starts = player.minutes_reliability if player.minutes_reliability is not None else 0.0
    per_start = (player.trend or 0.0) * starts
    recent = mean(player.recent_points) if player.recent_points else 0.0
    return TREND_WEIGHT * per_start + (1 - TREND_WEIGHT) * recent


def _projected_points(player: PlayerAnalysis, window_fixtures: list[FixtureDifficulty]) -> float:
    """What this player projects over the plan's whole window.

    Counts fixtures rather than gameweeks, and sums their difficulty
    multipliers rather than averaging: a Double Gameweek is two chances to
    score and a Blank Gameweek is none, which is exactly the asymmetry both
    chips exist to exploit. (suggestions.py averages instead, because it
    compares two players over the same shared horizon, where match count
    mostly cancels out.) No fixtures in the window means no points -- not
    "unknown", the way a bare fixture_ease_multiplier([]) would read it.
    """
    return _points_per_gameweek(player) * sum(fixture_ease_multiplier([f]) for f in window_fixtures)


def _window_label(target_gameweek: int, horizon: int) -> str:
    if horizon == 1:
        return f"in GW{target_gameweek}"
    return f"over the next {horizon} gameweeks"


def _rationale(
    player_out: PlayerAnalysis,
    player_in: PlayerAnalysis,
    out_projection: float,
    in_projection: float,
    window_fixtures: WindowFixtures,
    window_label: str,
) -> list[str]:
    lines = []
    if not window_fixtures[player_out.player_id]:
        lines.append(f"{player_out.web_name}'s club has no fixture {window_label} (blank gameweek).")
    lines.append(
        f"{player_out.web_name} projects {out_projection:.1f} pts {window_label}; "
        f"{player_in.web_name} projects {in_projection:.1f}."
    )
    difficulties = ", ".join(str(f.difficulty) for f in window_fixtures[player_in.player_id])
    if difficulties:
        lines.append(f"{player_in.web_name}'s fixtures {window_label}: difficulty {difficulties}.")
    return lines


def _plan_transfers(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    window_fixtures: WindowFixtures,
    bank: int,
    bought_prices: dict[int, int],
    horizon: int,
    window_label: str,
    min_gain_per_gw: float,
) -> tuple[list[PlannedTransfer], int]:
    """Greedily swap squad players for better candidates while the budget holds.

    Returns the transfers in the order they were chosen (best first, since
    each round takes the biggest remaining gain) and the leftover bank.
    `horizon` only sizes the churn threshold here -- the projections it
    compares already span the whole window.
    """
    projected = {
        p.player_id: _projected_points(p, window_fixtures[p.player_id])
        for p in squad + candidate_pool
    }
    min_gain = min_gain_per_gw * horizon

    held = {p.player_id: p for p in squad}
    club_counts = Counter(p.club_id for p in squad)
    # Only the original squad is sellable: a player the plan has just bought
    # was the best available for that slot, and re-selling them would also
    # muddy the sell-price rules (they'd go at the price the plan just paid).
    sellable = list(squad)
    budget = bank

    transfers: list[PlannedTransfer] = []
    while len(transfers) < MAX_PLAN_TRANSFERS:
        best: tuple[float, int, PlayerAnalysis, PlayerAnalysis, int] | None = None
        for player_out in sellable:
            sell_price = compute_sell_price(bought_prices[player_out.player_id], player_out.now_cost)
            affordable = sell_price + budget
            for player_in in candidate_pool:
                if player_in.player_id in held or player_in.position != player_out.position:
                    continue
                if player_in.now_cost > affordable:
                    continue
                if (
                    player_in.club_id != player_out.club_id
                    and club_counts[player_in.club_id] >= MAX_PER_CLUB
                ):
                    continue
                gain = projected[player_in.player_id] - projected[player_out.player_id]
                if gain < min_gain:
                    continue
                # Ties go to the cheaper buy, which leaves more in the bank
                # for the swaps the following rounds will look at.
                key = (gain, -player_in.now_cost)
                if best is None or key > (best[0], best[1]):
                    best = (gain, -player_in.now_cost, player_out, player_in, sell_price)

        if best is None:
            break

        gain, _, player_out, player_in, sell_price = best
        budget += sell_price - player_in.now_cost
        del held[player_out.player_id]
        held[player_in.player_id] = player_in
        club_counts[player_out.club_id] -= 1
        club_counts[player_in.club_id] += 1
        sellable.remove(player_out)
        transfers.append(
            PlannedTransfer(
                player_out=player_out,
                player_in=player_in,
                sell_price=sell_price,
                projected_point_gain=round(gain, 1),
                rationale=_rationale(
                    player_out,
                    player_in,
                    projected[player_out.player_id],
                    projected[player_in.player_id],
                    window_fixtures,
                    window_label,
                ),
            )
        )

    return transfers, budget


def _build_plan(
    chip: str,
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    window_fixtures: WindowFixtures,
    bank: int,
    bought_prices: dict[int, int],
    target_gameweek: int,
    horizon: int,
    min_gain_per_gw: float,
) -> ChipPlan:
    window_label = _window_label(target_gameweek, horizon)
    transfers, bank_after = _plan_transfers(
        squad=squad,
        candidate_pool=candidate_pool,
        window_fixtures=window_fixtures,
        bank=bank,
        bought_prices=bought_prices,
        horizon=horizon,
        window_label=window_label,
        min_gain_per_gw=min_gain_per_gw,
    )
    return ChipPlan(
        chip=chip,
        target_gameweek=target_gameweek,
        horizon=horizon,
        transfers=transfers,
        bank_before=bank,
        bank_after=bank_after,
        projected_point_gain=round(sum(t.projected_point_gain for t in transfers), 1),
    )


def wildcard_plan(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    bank: int,
    bought_prices: dict[int, int],
    target_gameweek: int,
    horizon: int = DEFAULT_HORIZON,
    min_gain_per_gw: float = MIN_GAIN_PER_GW,
) -> ChipPlan:
    """The transfers to make if the Wildcard is played for `target_gameweek`.

    Wildcard changes stick, so this optimises over the usual look-ahead
    horizon and can reuse each player's already-computed next-N fixtures.
    """
    window_fixtures = {p.player_id: p.fixture_difficulty_next for p in squad + candidate_pool}
    return _build_plan(
        chip="wildcard",
        squad=squad,
        candidate_pool=candidate_pool,
        window_fixtures=window_fixtures,
        bank=bank,
        bought_prices=bought_prices,
        target_gameweek=target_gameweek,
        horizon=horizon,
        min_gain_per_gw=min_gain_per_gw,
    )


def free_hit_plan(
    squad: list[PlayerAnalysis],
    candidate_pool: list[PlayerAnalysis],
    bank: int,
    bought_prices: dict[int, int],
    fixtures: list[dict],
    target_gameweek: int,
    min_gain_per_gw: float = MIN_GAIN_PER_GW,
) -> ChipPlan:
    """The transfers to make if the Free Hit is played for `target_gameweek`.

    The squad reverts straight afterwards, so only that one gameweek counts --
    which means PlayerAnalysis.fixture_difficulty_next (the next 3 from *now*)
    is the wrong window, and the target gameweek's own fixtures are looked up
    fresh. Players whose club blanks that week project zero and so sort
    themselves to the front of the sell list.
    """
    window_fixtures = {
        p.player_id: fixtures_in_event(fixtures, p.club_id, target_gameweek)
        for p in squad + candidate_pool
    }
    return _build_plan(
        chip="freehit",
        squad=squad,
        candidate_pool=candidate_pool,
        window_fixtures=window_fixtures,
        bank=bank,
        bought_prices=bought_prices,
        target_gameweek=target_gameweek,
        horizon=FREE_HIT_HORIZON,
        min_gain_per_gw=min_gain_per_gw,
    )
