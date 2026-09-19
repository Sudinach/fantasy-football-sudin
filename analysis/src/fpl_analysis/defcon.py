"""Defensive Contribution (DEFCON) signal -- new for the 2025/26 season.

DEFCON points already flow into official `total_points`, so Trend/Consistency
(points-based) already reflect them -- this module is a *separate* signal
surfacing players who are consistently close to the threshold, which raw
points can miss for a player having an otherwise quiet scoring run.
"""

from __future__ import annotations

from fpl_analysis.models import GwStatLine

# DEF need 10+ combined clearances/blocks/interceptions/tackles (CBIT).
# MID/FWD need 12+ of the same plus recoveries (CBIRT).
_THRESHOLDS = {"DEF": 10, "MID": 12, "FWD": 12}


def defcon_hit_rate(gw_stats: list[GwStatLine], position: str) -> float | None:
    """Fraction of played gameweeks meeting the position's DEFCON threshold.

    Goalkeepers don't earn DEFCON points -- returns None for them.
    """
    threshold = _THRESHOLDS.get(position)
    if threshold is None:
        return None
    played = [g for g in gw_stats if g.minutes > 0]
    if not played:
        return None

    def _actions(g: GwStatLine) -> int:
        base = g.clearances_blocks_interceptions + g.tackles
        return base + g.recoveries if position != "DEF" else base

    hits = sum(1 for g in played if _actions(g) >= threshold)
    return hits / len(played)
