"""Sell-price derivation, respecting FPL's 50%-profit-on-price-rise rule.

All prices here are in FPL's native tenths-of-£m integers to avoid float
rounding bugs; conversion to decimal £m happens only at the Snapshot boundary.
"""

from __future__ import annotations

from fpl_analysis.models import TransferRecord


def compute_sell_price(bought_price: int, current_price: int) -> int:
    """Losses are absorbed in full; only half of any price rise (floored to
    the nearest tenth) is recouped on sale.
    """
    if current_price <= bought_price:
        return current_price
    profit = current_price - bought_price
    return bought_price + profit // 2


def derive_bought_price(
    transfers: list[TransferRecord], player_id: int, gw1_price: int
) -> int:
    """The price the manager paid for `player_id`.

    Uses the most recent transfer-in record for this player; falls back to
    the player's Gameweek 1 price for players held since the original squad,
    who have no transfer-in record at all.
    """
    transfers_in = [t for t in transfers if t.element_in == player_id]
    if not transfers_in:
        return gw1_price
    most_recent = max(transfers_in, key=lambda t: t.event)
    return most_recent.element_in_cost
