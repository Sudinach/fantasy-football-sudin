from conftest import load_fixture

from fpl_analysis.fixtures import fixture_ease_multiplier, next_n_fixtures


def _fixture(event, team_h, team_a, team_h_difficulty=3, team_a_difficulty=3):
    return {
        "event": event,
        "team_h": team_h,
        "team_a": team_a,
        "team_h_difficulty": team_h_difficulty,
        "team_a_difficulty": team_a_difficulty,
    }


def test_returns_next_horizon_fixtures_for_the_clubs_events_only():
    fixtures = [
        _fixture(1, team_h=1, team_a=2),
        _fixture(2, team_h=3, team_a=1),
        _fixture(3, team_h=1, team_a=4),
        _fixture(4, team_h=5, team_a=1),
        _fixture(5, team_h=1, team_a=6),  # beyond horizon of 3
    ]

    result = next_n_fixtures(fixtures, club_id=1, from_event=1, horizon=3)

    assert [f.event for f in result] == [1, 2, 3]


def test_skips_blank_gameweeks():
    fixtures = [
        _fixture(1, team_h=1, team_a=2),
        # event 2: club 1 has no fixture (blank gameweek)
        _fixture(3, team_h=1, team_a=4),
        _fixture(4, team_h=5, team_a=1),
    ]

    result = next_n_fixtures(fixtures, club_id=1, from_event=1, horizon=3)

    assert [f.event for f in result] == [1, 3, 4]


def test_double_gameweek_contributes_two_entries_but_one_horizon_slot():
    fixtures = [
        _fixture(1, team_h=1, team_a=2),
        _fixture(1, team_h=3, team_a=1),  # same event, double gameweek
        _fixture(2, team_h=1, team_a=4),
    ]

    result = next_n_fixtures(fixtures, club_id=1, from_event=1, horizon=2)

    assert [f.event for f in result] == [1, 1, 2]


def test_home_and_away_difficulty_and_opponent_resolved_correctly():
    fixtures = [_fixture(1, team_h=1, team_a=2, team_h_difficulty=2, team_a_difficulty=4)]

    [home_view] = next_n_fixtures(fixtures, club_id=1, from_event=1, horizon=1)
    [away_view] = next_n_fixtures(fixtures, club_id=2, from_event=1, horizon=1)

    assert home_view.is_home is True and home_view.opponent_club_id == 2 and home_view.difficulty == 2
    assert away_view.is_home is False and away_view.opponent_club_id == 1 and away_view.difficulty == 4


def test_easier_fixtures_score_a_higher_multiplier():
    easy = next_n_fixtures([_fixture(1, 1, 2, team_h_difficulty=1)], club_id=1, from_event=1, horizon=1)
    hard = next_n_fixtures([_fixture(1, 1, 2, team_h_difficulty=5)], club_id=1, from_event=1, horizon=1)

    assert fixture_ease_multiplier(easy) > fixture_ease_multiplier(hard)


def test_empty_fixture_list_defaults_to_neutral_multiplier():
    assert fixture_ease_multiplier([]) == 1.0


def test_against_real_recorded_fixtures():
    real_fixtures = load_fixture("fixtures")

    result = next_n_fixtures(real_fixtures, club_id=1, from_event=1, horizon=3)

    assert len(result) >= 3
    assert all(1 <= f.difficulty <= 5 for f in result)
