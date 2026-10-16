from factories import fixture_difficulty, player

from fpl_analysis.chip_plan import free_hit_plan, wildcard_plan


def _fixture(event, team_h, team_a, team_h_difficulty=3, team_a_difficulty=3):
    return {
        "event": event,
        "team_h": team_h,
        "team_a": team_a,
        "team_h_difficulty": team_h_difficulty,
        "team_a_difficulty": team_a_difficulty,
    }


def _bought_at_now_cost(squad):
    """No price movement, so sell price == now_cost for every squad player."""
    return {p.player_id: p.now_cost for p in squad}


def test_wildcard_plan_swaps_every_outclassed_squad_player():
    squad = [player(i, web_name=f"Weak{i}", club_id=i, now_cost=50, trend=1.0) for i in range(1, 4)]
    pool = [player(100 + i, web_name=f"Star{i}", club_id=100 + i, now_cost=50, trend=8.0) for i in range(3)]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert plan.chip == "wildcard"
    assert plan.target_gameweek == 6
    assert len(plan.transfers) == 3
    assert {t.player_out.web_name for t in plan.transfers} == {"Weak1", "Weak2", "Weak3"}
    assert {t.player_in.web_name for t in plan.transfers} == {"Star0", "Star1", "Star2"}
    assert plan.projected_point_gain > 0


def test_wildcard_plan_is_empty_when_the_squad_is_already_the_best_available():
    squad = [player(i, club_id=i, now_cost=50, trend=8.0) for i in range(1, 4)]
    pool = [player(100, club_id=100, now_cost=50, trend=1.0)]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert plan.transfers == []
    assert plan.projected_point_gain == 0
    assert plan.bank_after == plan.bank_before


def test_wildcard_plan_orders_transfers_by_projected_gain():
    squad = [
        player(1, web_name="Awful", club_id=1, now_cost=50, trend=0.0),
        player(2, web_name="Mediocre", club_id=2, now_cost=50, trend=4.0),
    ]
    pool = [
        player(100, web_name="StarA", club_id=100, now_cost=50, trend=9.0),
        player(101, web_name="StarB", club_id=101, now_cost=50, trend=9.0),
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert [t.player_out.web_name for t in plan.transfers] == ["Awful", "Mediocre"]
    gains = [t.projected_point_gain for t in plan.transfers]
    assert gains == sorted(gains, reverse=True)


def test_wildcard_plan_respects_the_budget():
    squad = [player(1, web_name="Cheap", club_id=1, now_cost=45, trend=1.0)]
    pool = [
        player(100, web_name="Unaffordable", club_id=100, now_cost=130, trend=10.0),
        player(101, web_name="Affordable", club_id=101, now_cost=50, trend=6.0),
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=5,  # £0.5m: 4.5 + 0.5 covers Affordable but not Unaffordable
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert [t.player_in.web_name for t in plan.transfers] == ["Affordable"]
    assert plan.bank_after == 0


def test_wildcard_plan_keeps_positions_and_the_three_per_club_limit():
    squad = [
        player(1, position="MID", club_id=1, now_cost=50, trend=1.0),
        player(2, position="FWD", club_id=2, now_cost=50, trend=1.0),
    ]
    # Three players already at club 7, so no fourth can be bought from it.
    squad += [player(10 + i, position="DEF", club_id=7, now_cost=50, trend=1.0) for i in range(3)]
    pool = [
        player(100, web_name="GoodMid", position="MID", club_id=7, now_cost=50, trend=9.0),
        player(101, web_name="GoodFwd", position="FWD", club_id=8, now_cost=50, trend=9.0),
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert [t.player_in.web_name for t in plan.transfers] == ["GoodFwd"]
    assert all(t.player_out.position == t.player_in.position for t in plan.transfers)


def test_wildcard_plan_never_sells_a_player_it_just_bought():
    squad = [player(1, web_name="Weak", club_id=1, now_cost=50, trend=1.0)]
    pool = [
        player(100, web_name="Good", club_id=100, now_cost=50, trend=5.0),
        player(101, web_name="Better", club_id=101, now_cost=50, trend=9.0),
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert len(plan.transfers) == 1
    assert plan.transfers[0].player_in.web_name == "Better"


def test_wildcard_plan_sell_price_follows_the_half_profit_rule():
    squad = [player(1, club_id=1, now_cost=55, trend=1.0)]
    pool = [player(100, club_id=100, now_cost=52, trend=9.0)]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices={1: 50},  # bought at 5.0, now 5.5: sells at 5.2
        target_gameweek=6,
    )

    assert plan.transfers[0].sell_price == 52
    assert plan.bank_after == 0


def test_wildcard_plan_rationale_cites_both_projections():
    squad = [player(1, web_name="Weak", club_id=1, now_cost=50, trend=1.0)]
    pool = [player(100, web_name="Star", club_id=100, now_cost=50, trend=9.0)]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    rationale = plan.transfers[0].rationale
    assert any("Weak projects" in line and "Star projects" in line for line in rationale)
    assert any("over the next 3 gameweeks" in line for line in rationale)


def test_free_hit_plan_sells_players_blanking_in_the_target_gameweek():
    # Club 1 blanks in GW9; clubs 2 and 100 play.
    fixtures = [_fixture(9, team_h=2, team_a=100)]
    squad = [
        player(1, web_name="Blanking", club_id=1, now_cost=50, trend=9.0),
        player(2, web_name="Playing", club_id=2, now_cost=50, trend=9.0),
    ]
    pool = [player(100, web_name="Replacement", club_id=100, now_cost=50, trend=4.0)]

    plan = free_hit_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        fixtures=fixtures,
        target_gameweek=9,
    )

    assert plan.chip == "freehit"
    assert plan.target_gameweek == 9
    assert plan.horizon == 1
    # Blanking goes despite the better trend; Playing stays despite the pool
    # player being available, because a weaker trend is still a downgrade.
    assert [(t.player_out.web_name, t.player_in.web_name) for t in plan.transfers] == [
        ("Blanking", "Replacement")
    ]
    assert any("no fixture in GW9" in line for line in plan.transfers[0].rationale)


def test_free_hit_plan_ignores_the_next_three_fixtures_and_uses_the_target_gameweek():
    # The squad player has a lovely run over the next 3 GWs but blanks in GW9,
    # which is the only gameweek a Free Hit for GW9 is played over.
    squad = [
        player(
            1,
            web_name="Blanking",
            club_id=1,
            now_cost=50,
            trend=9.0,
            fixture_difficulty_next=[fixture_difficulty(event=6, difficulty=1)],
        )
    ]
    pool = [
        player(
            100,
            web_name="Replacement",
            club_id=100,
            now_cost=50,
            trend=3.0,
            fixture_difficulty_next=[fixture_difficulty(event=6, difficulty=5)],
        )
    ]

    plan = free_hit_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        fixtures=[_fixture(9, team_h=100, team_a=50)],
        target_gameweek=9,
    )

    assert [t.player_in.web_name for t in plan.transfers] == ["Replacement"]


def test_free_hit_plan_will_not_buy_a_player_who_also_blanks():
    fixtures = [_fixture(9, team_h=50, team_a=51)]  # nobody relevant plays
    squad = [player(1, club_id=1, now_cost=50, trend=1.0)]
    pool = [player(100, club_id=100, now_cost=50, trend=9.0)]

    plan = free_hit_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        fixtures=fixtures,
        target_gameweek=9,
    )

    assert plan.transfers == []


def test_free_hit_plan_counts_both_legs_of_a_double_gameweek():
    fixtures = [
        _fixture(9, team_h=1, team_a=50),
        _fixture(9, team_h=100, team_a=51),
        _fixture(9, team_h=52, team_a=100),  # club 100 plays twice
    ]
    squad = [player(1, web_name="Single", club_id=1, now_cost=50, trend=5.0)]
    pool = [player(100, web_name="Double", club_id=100, now_cost=50, trend=5.0)]

    plan = free_hit_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        fixtures=fixtures,
        target_gameweek=9,
    )

    # Equal trend and equal difficulty, but two fixtures beat one.
    assert [t.player_in.web_name for t in plan.transfers] == ["Double"]


def test_marginal_upgrades_are_left_alone_as_churn():
    squad = [player(1, club_id=1, now_cost=50, trend=5.0)]
    pool = [player(100, club_id=100, now_cost=50, trend=5.1)]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert plan.transfers == []


def test_a_fringe_players_hot_streak_does_not_displace_a_steady_starter():
    squad = [
        player(
            1,
            web_name="Steady",
            club_id=1,
            now_cost=120,
            trend=4.0,  # cooling, so Trend alone understates them
            recent_points=[8, 9, 8, 9, 8],
            minutes_reliability=1.0,
        )
    ]
    pool = [
        player(
            100,
            web_name="TwoGoodGames",
            club_id=100,
            now_cost=45,
            trend=8.0,  # red hot, but only across the two gameweeks they started
            recent_points=[0, 0, 0, 9, 8],
            minutes_reliability=0.4,
        )
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert plan.transfers == []


def test_a_genuinely_better_starter_is_still_bought():
    squad = [
        player(
            1,
            web_name="Fading",
            club_id=1,
            now_cost=120,
            trend=2.0,
            recent_points=[3, 2, 2, 1, 2],
            minutes_reliability=1.0,
        )
    ]
    pool = [
        player(
            100,
            web_name="Nailed",
            club_id=100,
            now_cost=120,
            trend=7.0,
            recent_points=[7, 8, 6, 9, 7],
            minutes_reliability=1.0,
        )
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert [t.player_in.web_name for t in plan.transfers] == ["Nailed"]


def test_a_benched_squad_player_projects_nothing_and_is_sold():
    squad = [
        player(
            1,
            web_name="Benched",
            club_id=1,
            now_cost=50,
            trend=6.0,  # decent whenever they do play, which is almost never
            recent_points=[0, 0, 0, 0, 0],
            minutes_reliability=0.0,
        )
    ]
    pool = [
        player(
            100,
            web_name="Rotated",
            club_id=100,
            now_cost=50,
            trend=3.0,
            recent_points=[2, 3, 0, 4, 3],
            minutes_reliability=0.6,
        )
    ]

    plan = wildcard_plan(
        squad=squad,
        candidate_pool=pool,
        bank=0,
        bought_prices=_bought_at_now_cost(squad),
        target_gameweek=6,
    )

    assert [t.player_out.web_name for t in plan.transfers] == ["Benched"]
