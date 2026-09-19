"""Fixture-difficulty lookups for the app's 3-gameweek look-ahead horizon."""

from __future__ import annotations

from fpl_analysis.models import FixtureDifficulty

DEFAULT_HORIZON = 3


def next_n_fixtures(
    fixtures: list[dict], club_id: int, from_event: int, horizon: int = DEFAULT_HORIZON
) -> list[FixtureDifficulty]:
    """A club's next `horizon` gameweeks of fixtures, from `from_event` onward.

    Blank gameweeks are skipped naturally (no fixture that event). Double
    gameweeks contribute two entries for the same event, and both count
    towards the fixture list but only one towards the horizon count.
    """
    relevant = sorted(
        (
            f
            for f in fixtures
            if f["event"] is not None
            and f["event"] >= from_event
            and club_id in (f["team_h"], f["team_a"])
        ),
        key=lambda f: f["event"],
    )

    result: list[FixtureDifficulty] = []
    events_seen: set[int] = set()
    for fixture in relevant:
        if fixture["event"] not in events_seen and len(events_seen) >= horizon:
            break
        is_home = fixture["team_h"] == club_id
        result.append(
            FixtureDifficulty(
                event=fixture["event"],
                opponent_club_id=fixture["team_a"] if is_home else fixture["team_h"],
                is_home=is_home,
                difficulty=fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"],
            )
        )
        events_seen.add(fixture["event"])
    return result


# FPL difficulty is 1 (easiest) - 5 (hardest); this maps it to a multiplier
# on expected points, so an easy run of fixtures inflates a candidate's
# projected return and a hard run deflates it.
_DIFFICULTY_MULTIPLIER = {1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}


def fixture_ease_multiplier(fixture_difficulties: list[FixtureDifficulty]) -> float:
    """Average expected-points multiplier across a set of upcoming fixtures."""
    if not fixture_difficulties:
        return 1.0
    multipliers = [_DIFFICULTY_MULTIPLIER[fd.difficulty] for fd in fixture_difficulties]
    return sum(multipliers) / len(multipliers)
