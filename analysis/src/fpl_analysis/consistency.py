"""This app's own measure of how reliably a player returns points week-to-week,
as opposed to a boom-bust profile with the same average (see CONTEXT.md).
"""

from __future__ import annotations

from statistics import pstdev

from fpl_analysis.models import GwStatLine
from fpl_analysis.trend import MIN_PLAYED_GAMEWEEKS


def compute_consistency(gw_stats: list[GwStatLine], window: int = 8) -> float | None:
    played_points = [g.points for g in gw_stats if g.minutes > 0][-window:]
    if len(played_points) < MIN_PLAYED_GAMEWEEKS:
        return None
    return 1 / (1 + pstdev(played_points))
