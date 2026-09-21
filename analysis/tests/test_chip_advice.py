from factories import chip_status, player

from fpl_analysis.chip_advice import free_hit_advice, wildcard_advice
from fpl_analysis.suggestions import score_pool


def test_wildcard_not_recommended_when_chip_is_unavailable():
    advice = wildcard_advice(
        squad=[player(1)],
        candidate_pool=[],
        scores={},
        free_transfers=1,
        status=chip_status(is_available=False, played_event=4),
    )

    assert advice.is_available is False
    assert advice.recommended is False
    assert "GW4" in advice.reasoning[0]


def test_wildcard_not_recommended_when_squad_has_few_weak_links():
    squad = [player(i, position="MID", now_cost=50) for i in range(1, 5)]
    pool = [player(100, position="MID", now_cost=50)]
    scores = score_pool(squad + pool)

    advice = wildcard_advice(
        squad=squad, candidate_pool=pool, scores=scores, free_transfers=2, status=chip_status()
    )

    assert advice.is_available is True
    assert advice.recommended is False


def test_wildcard_recommended_when_several_squad_players_are_outclassed():
    weak = [player(i, web_name=f"Weak{i}", position="MID", club_id=i, now_cost=50, trend=1.0) for i in range(1, 4)]
    pool = [player(100, web_name="Star", position="MID", club_id=100, now_cost=50, trend=10.0)]
    scores = score_pool(weak + pool)

    advice = wildcard_advice(
        squad=weak,
        candidate_pool=pool,
        scores=scores,
        free_transfers=1,
        status=chip_status(),
    )

    assert advice.recommended is True
    assert all(w.web_name in advice.reasoning[0] for w in weak)
    assert "8 points" in advice.reasoning[1]  # (3 weak - 1 free transfer) * 4


def test_free_hit_not_recommended_when_chip_is_unavailable():
    advice = free_hit_advice(
        squad_club_ids=[1, 2, 3],
        fixtures=[],
        current_gw=5,
        status=chip_status(name="freehit", is_available=False, played_event=None, start_event=2),
    )

    assert advice.is_available is False
    assert advice.recommended is False
    assert "GW2" in advice.reasoning[0]


def test_free_hit_not_recommended_with_no_blank_gameweek():
    fixtures = [
        {"event": 6, "team_h": 1, "team_a": 2},
        {"event": 6, "team_h": 3, "team_a": 4},
    ]

    advice = free_hit_advice(
        squad_club_ids=[1, 2, 3, 4],
        fixtures=fixtures,
        current_gw=5,
        status=chip_status(name="freehit", stop_event=6),
    )

    assert advice.is_available is True
    assert advice.recommended is False


def test_free_hit_recommended_for_the_worst_blank_gameweek_in_the_horizon():
    # GW6: clubs 3, 4, 5 have no fixture (only 1 v 2 plays). GW7: only 4 and 5 blank.
    fixtures = [
        {"event": 6, "team_h": 1, "team_a": 2},
        {"event": 7, "team_h": 1, "team_a": 2},
        {"event": 7, "team_h": 3, "team_a": 6},
    ]

    advice = free_hit_advice(
        squad_club_ids=[1, 2, 3, 4, 5],
        fixtures=fixtures,
        current_gw=5,
        status=chip_status(name="freehit", stop_event=7),
    )

    assert advice.recommended is True
    assert advice.target_gameweek == 6
    assert "3 of your squad's clubs" in advice.reasoning[0]
