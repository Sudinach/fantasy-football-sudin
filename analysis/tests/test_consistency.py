from factories import gw

from fpl_analysis.consistency import compute_consistency


def test_returns_none_with_fewer_than_two_played_gameweeks():
    assert compute_consistency([gw(1, 5, minutes=0)]) is None
    assert compute_consistency([]) is None


def test_steady_scorer_beats_boom_bust_scorer_with_same_mean():
    steady = [gw(i, 5) for i in range(1, 7)]
    boom_bust = [gw(1, 0), gw(2, 10), gw(3, 0), gw(4, 10), gw(5, 0), gw(6, 10)]

    assert compute_consistency(steady) > compute_consistency(boom_bust)


def test_ignores_gameweeks_with_zero_minutes():
    played = [gw(1, 5), gw(2, 5), gw(3, 5)]
    benched = [gw(4, 0, minutes=0)]
    assert compute_consistency(played) == compute_consistency(played + benched)
