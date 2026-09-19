import requests
from conftest import load_fixture

from fpl_analysis.fpl_client import BASE_URL, FplClient


def make_client() -> FplClient:
    return FplClient()


def test_get_bootstrap_static(requests_mock):
    recorded = load_fixture("bootstrap_static")
    requests_mock.get(f"{BASE_URL}/bootstrap-static/", json=recorded)

    result = make_client().get_bootstrap_static()

    assert result["elements"][0]["id"] == recorded["elements"][0]["id"]


def test_get_fixtures(requests_mock):
    recorded = load_fixture("fixtures")
    requests_mock.get(f"{BASE_URL}/fixtures/", json=recorded)

    result = make_client().get_fixtures()

    assert result == recorded


def test_get_entry(requests_mock):
    recorded = load_fixture("entry")
    requests_mock.get(f"{BASE_URL}/entry/677035/", json=recorded)

    result = make_client().get_entry(677035)

    assert result["id"] == recorded["id"]


def test_get_entry_history(requests_mock):
    recorded = load_fixture("entry_history")
    requests_mock.get(f"{BASE_URL}/entry/677035/history/", json=recorded)

    result = make_client().get_entry_history(677035)

    assert result == recorded


def test_get_entry_transfers(requests_mock):
    recorded = load_fixture("entry_transfers")
    requests_mock.get(f"{BASE_URL}/entry/677035/transfers/", json=recorded)

    result = make_client().get_entry_transfers(677035)

    assert result == recorded


def test_get_entry_picks(requests_mock):
    recorded = load_fixture("entry_picks")
    requests_mock.get(f"{BASE_URL}/entry/677035/event/5/picks/", json=recorded)

    result = make_client().get_entry_picks(677035, 5)

    assert result == recorded


def test_get_element_summary(requests_mock):
    recorded = load_fixture("element_summary_412")
    requests_mock.get(f"{BASE_URL}/element-summary/412/", json=recorded)

    result = make_client().get_element_summary(412)

    assert result == recorded


def test_raises_on_http_error(requests_mock):
    requests_mock.get(f"{BASE_URL}/entry/1/", status_code=404)

    try:
        make_client().get_entry(1)
    except requests.HTTPError as exc:
        assert "404" in str(exc)
    else:
        raise AssertionError("expected an exception on HTTP 404")
