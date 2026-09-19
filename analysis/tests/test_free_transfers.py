from factories import activity

from fpl_analysis.free_transfers import derive_ft_bank


def test_never_transferring_accumulates_to_the_cap_of_five():
    history = [activity(event) for event in range(1, 10)]  # GW1-9, never transfers
    assert derive_ft_bank(history) == 5


def test_transferring_every_gameweek_never_banks_more_than_one():
    history = [activity(event, transfers_made=1) for event in range(1, 6)]
    assert derive_ft_bank(history) == 1


def test_wildcard_gameweek_does_not_consume_or_reset_the_bank():
    history = [
        activity(1),
        activity(2, transfers_made=5, chip_played="wildcard"),  # unlimited moves, no cost
    ]
    # Bank going into GW2 was 2 (1 accrued after GW1, plus GW2's own grant);
    # wildcard leaves it untouched rather than consuming 5.
    assert derive_ft_bank(history) == derive_ft_bank([activity(1)])


def test_free_hit_gameweek_does_not_consume_or_reset_the_bank():
    history = [activity(1), activity(2, transfers_made=15, chip_played="freehit")]
    assert derive_ft_bank(history) == derive_ft_bank([activity(1)])


def test_transfer_beyond_the_bank_forces_bank_to_reset_then_accrue_one():
    # Bank is 1 (default) going into GW1; taking 3 transfers there is only
    # possible by paying hits for the 2 beyond the bank (hit-cost isn't this
    # module's concern -- entry/history's event_transfers_cost already
    # reports it directly). The bank itself resets to 0, then grants 1.
    history = [activity(1, transfers_made=3)]
    assert derive_ft_bank(history) == 1


def test_gw16_topup_raises_bank_to_five_but_never_lowers_an_already_higher_bank():
    # Transferring every gameweek keeps the bank pinned at 1, so the GW16
    # top-up is the only thing that can raise it.
    below_cap = [activity(event, transfers_made=1) for event in range(1, 16)]
    assert derive_ft_bank(below_cap) < 5

    topped_up = below_cap + [activity(16)]
    assert derive_ft_bank(topped_up) == 5

    already_at_cap = [activity(event) for event in range(1, 17)]
    assert derive_ft_bank(already_at_cap) == 5


def test_against_real_recorded_history():
    from conftest import load_fixture

    from fpl_analysis.models import transfer_activity_from_history

    entry_history = load_fixture("entry_history")
    real_activity = transfer_activity_from_history(entry_history)

    bank = derive_ft_bank(real_activity)

    assert 0 <= bank <= 5
