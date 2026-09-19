"""Derives a manager's banked Free Transfer count.

The public FPL API has no endpoint exposing this directly -- it only appears
in the authenticated `my-team` endpoint, which this project deliberately
avoids (see docs/adr/0002). Instead we simulate the season's FT rules against
the manager's public transfer/chip history (entry/history).
"""

from __future__ import annotations

from fpl_analysis.models import GwTransferActivity

FT_CAP = 5

# 2025/26-specific: a one-off top-up to 5 FTs at Gameweek 16, to help managers
# absorb AFCON squad disruption. Data-driven rather than baked into the loop
# so future seasons' equivalents are a one-line change.
SEASON_TOPUPS: dict[int, int] = {16: FT_CAP}

_NON_CONSUMING_CHIPS = {"wildcard", "freehit"}


def derive_ft_bank(
    activity: list[GwTransferActivity], cap: int = FT_CAP, topups: dict[int, int] = SEASON_TOPUPS
) -> int:
    """The FT bank available going into the gameweek *after* the last one in `activity`."""
    bank = 1  # FT accrual starts entering GW2; GW1 carries no free-transfer concept
    for gw in sorted(activity, key=lambda g: g.event):
        if gw.event in topups:
            bank = max(bank, topups[gw.event])
        if gw.chip_played in _NON_CONSUMING_CHIPS:
            continue
        used = min(gw.transfers_made, bank)
        bank = min(bank - used + 1, cap)
    return bank
