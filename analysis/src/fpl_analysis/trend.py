"""This app's own measure of a player's point-scoring trajectory.

Deliberately distinct from FPL's built-in `form` stat (a flat last-4-gameweek
average, see CONTEXT.md) -- Trend blends a longer recency-weighted average with
an explicit trajectory term, so a player who is heating up or cooling off is
distinguishable from one who is merely averaging the same points.
"""

from __future__ import annotations

from statistics import mean

from fpl_analysis.models import GwStatLine

MIN_PLAYED_GAMEWEEKS = 2


def _ewma(points: list[int], span: int) -> float:
    alpha = 2 / (span + 1)
    smoothed = float(points[0])
    for value in points[1:]:
        smoothed = alpha * value + (1 - alpha) * smoothed
    return smoothed


def _trajectory(points: list[int]) -> float:
    """Second-half average minus first-half average of the window: positive
    means recent gameweeks are scoring better than earlier ones in the window.
    """
    midpoint = len(points) // 2
    return mean(points[midpoint:]) - mean(points[:midpoint])


def compute_trend(gw_stats: list[GwStatLine], window: int = 8) -> float | None:
    played_points = [g.points for g in gw_stats if g.minutes > 0][-window:]
    if len(played_points) < MIN_PLAYED_GAMEWEEKS:
        return None
    return 0.7 * _ewma(played_points, span=8) + 0.3 * _trajectory(played_points)
