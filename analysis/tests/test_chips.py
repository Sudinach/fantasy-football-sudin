from factories import activity

from fpl_analysis.chips import chip_status_for_manager, chip_windows_from_bootstrap, relevant_status
from fpl_analysis.models import ChipWindow


def test_chip_windows_from_bootstrap_finds_both_wildcard_windows(bootstrap_static):
    windows = chip_windows_from_bootstrap(bootstrap_static)

    wildcards = sorted((w for w in windows if w.name == "wildcard"), key=lambda w: w.window_number)
    assert [w.window_number for w in wildcards] == [1, 2]
    assert wildcards[0].start_event == 2
    assert wildcards[0].stop_event == 19
    assert wildcards[1].start_event == 20
    assert wildcards[1].stop_event == 38


def test_chip_windows_from_bootstrap_finds_both_freehit_windows(bootstrap_static):
    windows = chip_windows_from_bootstrap(bootstrap_static)

    freehits = sorted((w for w in windows if w.name == "freehit"), key=lambda w: w.window_number)
    assert [w.window_number for w in freehits] == [1, 2]


def test_chip_windows_from_bootstrap_excludes_scoring_only_chips(bootstrap_static):
    windows = chip_windows_from_bootstrap(bootstrap_static)

    assert {w.name for w in windows} == {"wildcard", "freehit"}


def test_chip_status_marks_unplayed_current_window_as_available():
    windows = [ChipWindow("wildcard", 1, start_event=2, stop_event=19)]
    statuses = chip_status_for_manager(windows, activity=[activity(1)], current_gw=5)

    assert statuses[0].is_available is True
    assert statuses[0].played_event is None


def test_chip_status_marks_played_window_as_unavailable():
    windows = [ChipWindow("wildcard", 1, start_event=2, stop_event=19)]
    played = [activity(1), activity(4, transfers_made=8, chip_played="wildcard")]
    statuses = chip_status_for_manager(windows, activity=played, current_gw=5)

    assert statuses[0].is_available is False
    assert statuses[0].played_event == 4


def test_chip_status_marks_a_window_outside_the_current_gameweek_as_unavailable():
    windows = [ChipWindow("wildcard", 2, start_event=20, stop_event=38)]
    statuses = chip_status_for_manager(windows, activity=[activity(1)], current_gw=5)

    assert statuses[0].is_available is False
    assert statuses[0].played_event is None


def test_relevant_status_picks_the_window_containing_the_current_gameweek():
    windows = [
        ChipWindow("wildcard", 1, start_event=2, stop_event=19),
        ChipWindow("wildcard", 2, start_event=20, stop_event=38),
    ]
    statuses = chip_status_for_manager(windows, activity=[activity(1)], current_gw=5)

    assert relevant_status(statuses, "wildcard", current_gw=5).window_number == 1


def test_relevant_status_stays_on_the_current_window_even_once_played():
    # Playing it early in window 1 doesn't unlock window 2 -- that one stays
    # closed until GW20 regardless.
    windows = [
        ChipWindow("wildcard", 1, start_event=2, stop_event=19),
        ChipWindow("wildcard", 2, start_event=20, stop_event=38),
    ]
    played = [activity(1), activity(5, transfers_made=8, chip_played="wildcard")]
    statuses = chip_status_for_manager(windows, activity=played, current_gw=5)

    status = relevant_status(statuses, "wildcard", current_gw=5)
    assert status.window_number == 1
    assert status.is_available is False
    assert status.played_event == 5


def test_relevant_status_moves_to_the_next_window_once_the_first_closes():
    windows = [
        ChipWindow("wildcard", 1, start_event=2, stop_event=19),
        ChipWindow("wildcard", 2, start_event=20, stop_event=38),
    ]
    played = [activity(1), activity(5, transfers_made=8, chip_played="wildcard")]
    statuses = chip_status_for_manager(windows, activity=played, current_gw=25)

    assert relevant_status(statuses, "wildcard", current_gw=25).window_number == 2
