from factories import player, squad_player

from fpl_analysis.pipeline import AnalysisResult
from fpl_analysis.snapshot import SCHEMA_VERSION, build_snapshot


def _make_result(suggestions=()) -> AnalysisResult:
    sp = squad_player(1, web_name="Haaland", club="Man City", club_id=12, position="FWD", squad_slot=1)
    pa = player(1, web_name="Haaland", position="FWD", club_id=12, now_cost=145, trend=7.4, consistency=0.6)

    return AnalysisResult(
        entry_id=677035,
        manager_name="Sudin Acharya",
        team_name="theRedFreakingDevils",
        overall_rank=9374008,
        total_points=173,
        gameweek=5,
        next_deadline="2026-10-10T10:00:00Z",
        is_current_gw_finished=False,
        bank=32,
        team_value=990,
        free_transfers=3,
        teams={12: "Man City"},
        squad=[sp],
        squad_analysis=[pa],
        squad_quality_scores={1: 88.1},
        bought_prices={1: 140},
        points_trend=[{"event": 1, "points": 62, "overall_rank": 1500000}],
        suggestions=list(suggestions),
    )


def test_snapshot_has_the_expected_top_level_shape():
    snapshot = build_snapshot(_make_result())

    assert snapshot["schema_version"] == SCHEMA_VERSION
    assert set(snapshot.keys()) == {
        "schema_version", "generated_at", "gameweek", "manager", "squad",
        "points_trend", "suggestions", "meta",
    }


def test_money_fields_are_converted_to_decimal_pounds():
    snapshot = build_snapshot(_make_result())

    assert snapshot["manager"]["bank"] == 3.2
    assert snapshot["manager"]["team_value"] == 99.0
    player_dict = snapshot["squad"][0]
    assert player_dict["now_cost"] == 14.5
    assert player_dict["bought_price"] == 14.0
    assert player_dict["sell_price"] == 14.2  # bought 14.0, now 14.5: half the £0.5m rise, floored


def test_squad_role_derived_from_squad_slot():
    result = _make_result()
    starting = build_snapshot(result)["squad"][0]
    assert starting["squad_role"] == "starting"

    benched_sp = squad_player(2, squad_slot=12)
    benched_pa = player(2)
    result.squad.append(benched_sp)
    result.squad_analysis.append(benched_pa)
    result.bought_prices[2] = 50
    result.squad_quality_scores[2] = 50.0

    benched = build_snapshot(result)["squad"][1]
    assert benched["squad_role"] == "bench"


def test_generated_at_is_an_iso8601_utc_timestamp():
    snapshot = build_snapshot(_make_result())
    assert snapshot["generated_at"].endswith("Z")


def test_schema_round_trips_through_json():
    import json

    snapshot = build_snapshot(_make_result())
    reparsed = json.loads(json.dumps(snapshot))

    assert reparsed == snapshot
