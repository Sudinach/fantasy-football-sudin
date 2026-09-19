from factories import gw

from fpl_analysis.trend import compute_trend


def test_returns_none_with_fewer_than_two_played_gameweeks():
    assert compute_trend([gw(1, 5, minutes=0)]) is None
    assert compute_trend([]) is None


def test_ignores_gameweeks_with_zero_minutes():
    played = [gw(1, 2), gw(2, 2), gw(3, 2)]
    benched = [gw(4, 99, minutes=0)]  # shouldn't be able to inflate trend
    assert compute_trend(played) == compute_trend(played + benched)


def test_rising_scorer_beats_flat_scorer_with_same_mean():
    flat = [gw(i, 4) for i in range(1, 7)]
    rising = [gw(1, 1), gw(2, 2), gw(3, 3), gw(4, 5), gw(5, 6), gw(6, 7)]

    assert compute_trend(rising) > compute_trend(flat)


def test_only_considers_the_last_window_gameweeks():
    # A terrible start followed by a strong recent run should score higher
    # than if that terrible start were still in the averaging window.
    long_history = [gw(i, 0) for i in range(1, 6)] + [gw(i, 10) for i in range(6, 10)]
    short_window_trend = compute_trend(long_history, window=4)
    full_window_trend = compute_trend(long_history, window=9)

    assert short_window_trend > full_window_trend
