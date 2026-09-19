from fpl_analysis.models import build_squad


def test_build_squad_returns_fifteen_players_ordered_by_slot(bootstrap_static, entry_picks):
    squad = build_squad(bootstrap_static, entry_picks)

    assert len(squad) == 15
    assert [p.squad_slot for p in squad] == list(range(1, 16))


def test_build_squad_marks_exactly_one_captain_and_one_vice_captain(bootstrap_static, entry_picks):
    squad = build_squad(bootstrap_static, entry_picks)

    assert sum(p.is_captain for p in squad) == 1
    assert sum(p.is_vice_captain for p in squad) == 1


def test_build_squad_uses_decimal_millions_for_cost(bootstrap_static, entry_picks):
    squad = build_squad(bootstrap_static, entry_picks)

    for player in squad:
        assert 3.5 <= player.now_cost <= 16.0


def test_build_squad_assigns_valid_positions(bootstrap_static, entry_picks):
    squad = build_squad(bootstrap_static, entry_picks)

    positions = {p.position for p in squad}
    assert positions <= {"GK", "DEF", "MID", "FWD"}
    assert sum(p.position == "GK" for p in squad) == 2
