from factories import gw

from fpl_analysis.defcon import defcon_hit_rate


def test_goalkeepers_have_no_defcon_signal():
    assert defcon_hit_rate([gw(1, 5, cbi=20, tackles=10)], position="GK") is None


def test_no_played_gameweeks_returns_none():
    assert defcon_hit_rate([gw(1, 0, minutes=0)], position="DEF") is None


def test_defender_threshold_is_ten_combined_actions():
    meets = [gw(1, 2, cbi=8, tackles=2)]  # 10 total
    misses = [gw(1, 2, cbi=8, tackles=1)]  # 9 total

    assert defcon_hit_rate(meets, position="DEF") == 1.0
    assert defcon_hit_rate(misses, position="DEF") == 0.0


def test_midfielder_and_forward_threshold_is_twelve_including_recoveries():
    meets = [gw(1, 2, cbi=5, tackles=2, recoveries=5)]  # 12 total
    misses = [gw(1, 2, cbi=5, tackles=2, recoveries=4)]  # 11 total

    assert defcon_hit_rate(meets, position="MID") == 1.0
    assert defcon_hit_rate(misses, position="FWD") == 0.0


def test_defender_threshold_ignores_recoveries():
    # 8 CBIT + 5 recoveries = 13 combined, but recoveries don't count for DEF
    just_under = [gw(1, 2, cbi=8, tackles=0, recoveries=5)]

    assert defcon_hit_rate(just_under, position="DEF") == 0.0


def test_hit_rate_is_fraction_of_played_gameweeks():
    stats = [
        gw(1, 2, cbi=10),  # meets
        gw(2, 2, cbi=0),  # misses
        gw(3, 0, minutes=0),  # unplayed, excluded from denominator
        gw(4, 2, cbi=10),  # meets
    ]

    assert defcon_hit_rate(stats, position="DEF") == 2 / 3
