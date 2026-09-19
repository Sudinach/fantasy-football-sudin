"""Thin wrapper over the public, unofficial Fantasy Premier League API.

All endpoints used here are publicly readable with no authentication. See
docs/adr/0002-suggestions-are-advisory-only.md for why this project never
touches the authenticated (login-required) endpoints.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE_URL = "https://fantasy.premierleague.com/api"


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "fantasy-football-sudin/0.1 (personal dashboard project)"
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


class FplClient:
    """Read-only client for the public FPL JSON API."""

    def __init__(self, session: requests.Session | None = None, base_url: str = BASE_URL) -> None:
        self._session = session or _build_session()
        self._base_url = base_url

    def _get(self, path: str) -> dict:
        response = self._session.get(f"{self._base_url}{path}", timeout=15)
        response.raise_for_status()
        return response.json()

    def get_bootstrap_static(self) -> dict:
        """All players, teams, gameweeks/events, and stat field definitions."""
        return self._get("/bootstrap-static/")

    def get_fixtures(self) -> list[dict]:
        """Every fixture this season, with difficulty ratings per team."""
        return self._get("/fixtures/")

    def get_entry(self, entry_id: int) -> dict:
        """A manager's profile: team name, overall rank, leagues joined."""
        return self._get(f"/entry/{entry_id}/")

    def get_entry_history(self, entry_id: int) -> dict:
        """A manager's gameweek-by-gameweek history this season, plus chips used."""
        return self._get(f"/entry/{entry_id}/history/")

    def get_entry_transfers(self, entry_id: int) -> list[dict]:
        """A manager's full transfer history for the season."""
        return self._get(f"/entry/{entry_id}/transfers/")

    def get_entry_picks(self, entry_id: int, gw: int) -> dict:
        """A manager's 15-man squad and captaincy for a given gameweek."""
        return self._get(f"/entry/{entry_id}/event/{gw}/picks/")

    def get_element_summary(self, player_id: int) -> dict:
        """A player's per-gameweek history this season and upcoming fixtures."""
        return self._get(f"/element-summary/{player_id}/")
