"""BUG-13: /quarters/current must not 502 when the UCSB API is down."""

from fastapi.testclient import TestClient

from api.main import app
from api.routers.quarters import reset_quarter_cache
from ucsb_api.client import UCSBApiError
from ucsb_api.quarters import current_and_next_quarter_codes


def _client():
    return TestClient(app)


def setup_function():
    reset_quarter_cache()


def test_quarters_current_returns_ucsb_payload(monkeypatch):
    class FakeClient:
        def fetch_current_quarter(self):
            return {"quarter": "20264", "name": "Fall 2026"}

        def fetch_quarter_calendar(self, code):
            assert code == "20271"
            return {
                "name": "Winter 2027",
                "pass1Begin": "2026-11-10",
                "pass2Begin": "2026-11-17",
                "pass3Begin": "2026-11-24",
                "firstDayOfClasses": "2027-01-05",
                "lastDayOfClasses": "2027-03-13",
            }

    monkeypatch.setattr("api.routers.quarters.UCSBApiClient", FakeClient)
    resp = _client().get("/quarters/current")
    assert resp.status_code == 200
    data = resp.json()
    assert data["quarter_code"] == "20264"
    assert data["next_quarter_code"] == "20271"
    assert data["pass1_begin"] == "2026-11-10"


def test_quarters_current_falls_back_instead_of_502(monkeypatch):
    class BrokenClient:
        def fetch_current_quarter(self):
            raise UCSBApiError("Failed to fetch current quarter (status=401): 401")

    monkeypatch.setattr("api.routers.quarters.UCSBApiClient", BrokenClient)
    resp = _client().get("/quarters/current")
    assert resp.status_code == 200
    data = resp.json()
    current, nxt = current_and_next_quarter_codes()
    assert data["quarter_code"] == current
    assert data["next_quarter_code"] == nxt
    assert data["pass1_begin"] is None


def test_quarters_current_serves_last_good_on_outage(monkeypatch):
    class FlipClient:
        calls = 0

        def fetch_current_quarter(self):
            FlipClient.calls += 1
            if FlipClient.calls > 1:
                raise UCSBApiError("Failed to fetch current quarter (status=503): 503")
            return {"quarter": "20264", "name": "Fall 2026"}

        def fetch_quarter_calendar(self, _code):
            return {"name": "Winter 2027", "pass1Begin": "2026-11-10"}

    monkeypatch.setattr("api.routers.quarters.UCSBApiClient", FlipClient)
    first = _client().get("/quarters/current")
    assert first.status_code == 200
    assert first.json()["pass1_begin"] == "2026-11-10"

    second = _client().get("/quarters/current")
    assert second.status_code == 200
    assert second.json()["pass1_begin"] == "2026-11-10"
    assert second.json()["quarter_code"] == "20264"


def test_missing_key_falls_back_instead_of_503(monkeypatch):
    def boom():
        raise UCSBApiError("UCSB_API_KEY is not configured")

    monkeypatch.setattr("api.routers.quarters.UCSBApiClient", boom)
    resp = _client().get("/quarters/current")
    assert resp.status_code == 200
    current, _nxt = current_and_next_quarter_codes()
    assert resp.json()["quarter_code"] == current
