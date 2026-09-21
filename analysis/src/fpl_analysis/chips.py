"""Derives Wildcard/Free Hit availability from FPL's own chip-window data.

bootstrap-static's `chips` list publishes exactly when each Chip Window opens
and closes this season (see CONTEXT.md's "Chip Window") -- no need to
hard-code deadlines the way free_transfers.py has to for the FT top-up.
"""

from __future__ import annotations

from fpl_analysis.models import ChipStatus, ChipWindow, GwTransferActivity

_TRANSFER_CHIPS = {"wildcard", "freehit"}


def chip_windows_from_bootstrap(bootstrap_static: dict) -> list[ChipWindow]:
    """The Wildcard/Free Hit windows FPL has defined this season, in order."""
    by_name: dict[str, list[dict]] = {}
    for chip in bootstrap_static["chips"]:
        if chip["name"] not in _TRANSFER_CHIPS:
            continue
        by_name.setdefault(chip["name"], []).append(chip)

    windows: list[ChipWindow] = []
    for name, chips in by_name.items():
        ordered = sorted(chips, key=lambda c: c["start_event"])
        for window_number, chip in enumerate(ordered, start=1):
            windows.append(
                ChipWindow(
                    name=name,
                    window_number=window_number,
                    start_event=chip["start_event"],
                    stop_event=chip["stop_event"],
                )
            )
    return windows


def chip_status_for_manager(
    windows: list[ChipWindow], activity: list[GwTransferActivity], current_gw: int
) -> list[ChipStatus]:
    """Each Window cross-referenced with whether/when this manager played it."""
    statuses = []
    for window in windows:
        played_event = next(
            (
                a.event
                for a in activity
                if a.chip_played == window.name and window.start_event <= a.event <= window.stop_event
            ),
            None,
        )
        statuses.append(
            ChipStatus(
                name=window.name,
                window_number=window.window_number,
                start_event=window.start_event,
                stop_event=window.stop_event,
                played_event=played_event,
                is_available=played_event is None and window.start_event <= current_gw <= window.stop_event,
            )
        )
    return statuses


def relevant_status(statuses: list[ChipStatus], name: str, current_gw: int) -> ChipStatus:
    """The one ChipStatus for `name` that matters right now: the Window the
    manager is currently inside, else the next upcoming Window, else the last.
    """
    matches = sorted((s for s in statuses if s.name == name), key=lambda s: s.start_event)
    for status in matches:
        if status.start_event <= current_gw <= status.stop_event:
            return status
    for status in matches:
        if current_gw < status.start_event:
            return status
    return matches[-1]
