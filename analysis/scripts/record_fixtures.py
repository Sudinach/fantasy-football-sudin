"""Manual (non-CI) utility: refresh the recorded real API responses used by tests.

Run with: uv run python scripts/record_fixtures.py <entry_id>

Not run automatically -- re-run by hand when the recorded fixtures need refreshing
(e.g. a new season, or to capture a new edge case like a wildcard gameweek).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import requests

from fpl_analysis.fpl_client import FplClient

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def _current_event(bootstrap_static: dict) -> int:
    for event in bootstrap_static["events"]:
        if event["is_current"]:
            return event["id"]
    # Season hasn't started yet, or we're between GW1's deadline and kickoff.
    return bootstrap_static["events"][0]["id"]


def _save(name: str, data: object) -> None:
    path = FIXTURES_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"wrote {path}")


def main(entry_id: int) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    client = FplClient()

    bootstrap_static = client.get_bootstrap_static()
    _save("bootstrap_static", bootstrap_static)

    _save("fixtures", client.get_fixtures())
    _save("entry", client.get_entry(entry_id))
    _save("entry_history", client.get_entry_history(entry_id))
    _save("entry_transfers", client.get_entry_transfers(entry_id))

    event = _current_event(bootstrap_static)
    try:
        picks = client.get_entry_picks(entry_id, event)
    except requests.HTTPError:  # current GW picks 404 until its deadline passes
        picks = client.get_entry_picks(entry_id, event - 1)
        event -= 1
    _save("entry_picks", picks)
    print(f"(picks recorded for gameweek {event})")

    # A couple of players from the squad, so element-summary has real data too.
    sample_player_ids = [pick["element"] for pick in picks["picks"][:3]]
    for player_id in sample_player_ids:
        _save(f"element_summary_{player_id}", client.get_element_summary(player_id))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: record_fixtures.py <entry_id>")
        raise SystemExit(1)
    main(int(sys.argv[1]))
