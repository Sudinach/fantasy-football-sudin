from factories import fixture_difficulty, player

from fpl_analysis.suggestions import suggest_transfers


def test_suggests_a_clear_upgrade_within_budget():
    sell = player(1, web_name="Weak", position="MID", club_id=1, now_cost=50, trend=2.0)
    buy = player(2, web_name="Strong", position="MID", club_id=2, now_cost=50, trend=6.0)

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[buy],
        free_transfers=1,
        bank=0,
        bought_prices={1: 50},
        club_counts={1: 1},
    )

    assert len(suggestions) == 1
    assert suggestions[0].player_out.player_id == 1
    assert suggestions[0].player_in.player_id == 2
    assert suggestions[0].hit_cost == 0
    assert suggestions[0].projected_point_gain == 12.0  # (6.0 - 2.0) * horizon(3)


def test_rejects_a_buy_candidate_outside_budget():
    sell = player(1, position="MID", club_id=1, now_cost=50, trend=2.0)
    too_expensive = player(2, position="MID", club_id=2, now_cost=51, trend=10.0)

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[too_expensive],
        free_transfers=1,
        bank=0,  # sell price (50) + bank (0) = budget of 50, candidate costs 51
        bought_prices={1: 50},
        club_counts={1: 1},
    )

    assert suggestions == []


def test_rejects_a_buy_candidate_in_a_different_position():
    sell = player(1, position="MID", club_id=1, now_cost=50, trend=2.0)
    wrong_position = player(2, position="FWD", club_id=2, now_cost=50, trend=10.0)

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[wrong_position],
        free_transfers=1,
        bank=0,
        bought_prices={1: 50},
        club_counts={1: 1},
    )

    assert suggestions == []


def test_rejects_a_buy_candidate_that_would_breach_the_club_limit():
    sell = player(1, position="MID", club_id=1, now_cost=50, trend=2.0)
    over_the_limit = player(2, position="MID", club_id=2, now_cost=50, trend=10.0)

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[over_the_limit],
        free_transfers=1,
        bank=0,
        bought_prices={1: 50},
        club_counts={1: 1, 2: 3},  # already at the cap for club 2
    )

    assert suggestions == []


def test_allows_a_same_club_swap_even_at_the_clubs_cap():
    sell = player(1, position="MID", club_id=2, now_cost=50, trend=2.0)
    same_club = player(2, position="MID", club_id=2, now_cost=50, trend=10.0)

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[same_club],
        free_transfers=1,
        bank=0,
        bought_prices={1: 50},
        club_counts={2: 3},  # at cap, but swapping within the same club is a net-zero change
    )

    assert len(suggestions) == 1


def test_hit_is_gated_behind_a_safety_margin_over_its_cost():
    sell = player(1, position="MID", club_id=1, now_cost=50, trend=2.0)
    marginal = player(2, position="MID", club_id=2, now_cost=50, trend=3.9)  # gain 5.7, below 4+2
    clear = player(3, position="MID", club_id=2, now_cost=50, trend=4.1)  # gain 6.3, clears 4+2

    no_suggestion = suggest_transfers(
        squad=[sell], candidate_pool=[marginal], free_transfers=0, bank=0,
        bought_prices={1: 50}, club_counts={1: 1},
    )
    with_hit = suggest_transfers(
        squad=[sell], candidate_pool=[clear], free_transfers=0, bank=0,
        bought_prices={1: 50}, club_counts={1: 1},
    )

    assert no_suggestion == []
    assert len(with_hit) == 1
    assert with_hit[0].hit_cost == 4
    assert with_hit[0].net_projected_gain == with_hit[0].projected_point_gain - 4


def test_suggestions_are_ordered_by_net_projected_gain_descending():
    sell_a = player(1, web_name="A", position="MID", club_id=1, now_cost=50, trend=2.0)
    sell_b = player(2, web_name="B", position="DEF", club_id=1, now_cost=50, trend=2.0)
    small_gain = player(3, web_name="SmallGain", position="MID", club_id=2, now_cost=50, trend=4.0)
    big_gain = player(4, web_name="BigGain", position="DEF", club_id=2, now_cost=50, trend=9.0)

    suggestions = suggest_transfers(
        squad=[sell_a, sell_b],
        candidate_pool=[small_gain, big_gain],
        free_transfers=2,
        bank=0,
        bought_prices={1: 50, 2: 50},
        club_counts={1: 2},
    )

    assert [s.player_in.web_name for s in suggestions] == ["BigGain", "SmallGain"]


def test_uses_fixture_difficulty_to_favour_an_easier_run():
    sell = player(1, position="MID", club_id=1, now_cost=50, trend=5.0)
    hard_fixtures = player(
        2, web_name="HardRun", position="MID", club_id=2, now_cost=50, trend=5.0,
        fixture_difficulty_next=[fixture_difficulty(difficulty=5)],
    )
    easy_fixtures = player(
        3, web_name="EasyRun", position="MID", club_id=3, now_cost=50, trend=5.0,
        fixture_difficulty_next=[fixture_difficulty(difficulty=1)],
    )

    suggestions = suggest_transfers(
        squad=[sell],
        candidate_pool=[hard_fixtures, easy_fixtures],
        free_transfers=1,
        bank=0,
        bought_prices={1: 50},
        club_counts={1: 1},
    )

    assert suggestions[0].player_in.web_name == "EasyRun"
