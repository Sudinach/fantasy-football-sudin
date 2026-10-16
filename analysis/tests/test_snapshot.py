from factories import player, squad_player

from fpl_analysis.models import ChipAdvice, ChipPlan, PlannedTransfer
from fpl_analysis.pipeline import AnalysisResult
from fpl_analysis.snapshot import SCHEMA_VERSION, build_snapshot

_DEFAULT_CHIP_ADVICE = [
    ChipAdvice("wildcard", True, False, None, ["Only 0 squad player(s) are clearly outclassed."]),
    ChipAdvice("freehit", True, False, None, ["No blank gameweek severe enough -- save it."]),
]


def _make_result(suggestions=(), chip_advice=_DEFAULT_CHIP_ADVICE) -> AnalysisResult:
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
        chip_advice=list(chip_advice),
    )


def test_snapshot_has_the_expected_top_level_shape():
    snapshot = build_snapshot(_make_result())

    assert snapshot["schema_version"] == SCHEMA_VERSION
    assert set(snapshot.keys()) == {
        "schema_version", "generated_at", "gameweek", "manager", "squad",
        "points_trend", "suggestions", "chip_advice", "meta",
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


def test_chip_advice_has_no_plan_when_the_chip_is_not_recommended():
    snapshot = build_snapshot(_make_result())

    assert all(advice["plan"] is None for advice in snapshot["chip_advice"])


def test_recommended_chip_serializes_its_plan_with_decimal_money():
    plan = ChipPlan(
        chip="wildcard",
        target_gameweek=6,
        horizon=3,
        transfers=[
            PlannedTransfer(
                player_out=player(1, web_name="Haaland", position="FWD", now_cost=145),
                player_in=player(2, web_name="Salah", position="MID", now_cost=130),
                sell_price=142,
                projected_point_gain=8.3,
                rationale=["Haaland projects 12.0 pts over the next 3 gameweeks; Salah projects 20.3."],
            )
        ],
        bank_before=32,
        bank_after=44,
        projected_point_gain=8.3,
    )
    advice = [ChipAdvice("wildcard", True, True, 6, ["Rebuild time."], plan)]

    plan_dict = build_snapshot(_make_result(chip_advice=advice))["chip_advice"][0]["plan"]

    assert plan_dict["target_gameweek"] == 6
    assert plan_dict["horizon_gws"] == 3
    assert plan_dict["transfer_count"] == 1
    assert plan_dict["bank_before"] == 3.2
    assert plan_dict["bank_after"] == 4.4
    assert plan_dict["projected_point_gain"] == 8.3

    [transfer] = plan_dict["transfers"]
    assert transfer["player_out"]["web_name"] == "Haaland"
    assert transfer["player_in"]["web_name"] == "Salah"
    assert transfer["sell_price"] == 14.2
    assert transfer["buy_price"] == 13.0
