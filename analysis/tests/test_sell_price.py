from conftest import load_fixture

from fpl_analysis.models import transfer_records_from_transfers
from fpl_analysis.sell_price import compute_sell_price, derive_bought_price


def test_price_unchanged_sells_at_cost():
    assert compute_sell_price(bought_price=50, current_price=50) == 50


def test_price_fallen_absorbs_the_full_loss():
    assert compute_sell_price(bought_price=50, current_price=45) == 45


def test_price_risen_recoups_only_half_the_gain_floored():
    # +£0.2m gain -> half is £0.1m -> sells at bought + 1 (tenths)
    assert compute_sell_price(bought_price=50, current_price=52) == 51
    # +£0.4m gain -> half is £0.2m
    assert compute_sell_price(bought_price=50, current_price=54) == 52
    # +£0.3m gain -> half floors down from 1.5 to 1
    assert compute_sell_price(bought_price=50, current_price=53) == 51


def test_derive_bought_price_uses_most_recent_transfer_in():
    transfers = transfer_records_from_transfers(
        [
            {"event": 2, "element_in": 99, "element_in_cost": 60, "element_out": 1, "element_out_cost": 60},
            {"event": 5, "element_in": 99, "element_in_cost": 65, "element_out": 2, "element_out_cost": 62},
        ]
    )

    assert derive_bought_price(transfers, player_id=99, gw1_price=55) == 65


def test_derive_bought_price_falls_back_to_gw1_price_for_original_squad_players():
    transfers = transfer_records_from_transfers([])

    assert derive_bought_price(transfers, player_id=99, gw1_price=55) == 55


def test_against_real_recorded_transfers():
    real_transfers = transfer_records_from_transfers(load_fixture("entry_transfers"))
    transferred_in_id = real_transfers[0].element_in
    expected = max(
        (t for t in real_transfers if t.element_in == transferred_in_id), key=lambda t: t.event
    )

    bought_price = derive_bought_price(real_transfers, player_id=transferred_in_id, gw1_price=999)

    assert bought_price == expected.element_in_cost
