"""Tests for Step 6 — Date Filter on the Profile Page (spec DoD).

Verifies the optional ?start=/?end= range filter on GET /profile:
  - a valid range narrows the transaction list and hides out-of-range rows
  - an invalid date value is ignored (full list shown)
  - a range with no matches shows the empty state
  - unauthenticated visits still redirect to /login

These checks are intentionally written against the known seed expense *dates*
(July 2026) rather than absolute totals, so they stay valid even if the local
database has accumulated extra rows beyond the canonical seed.
"""

from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def _logged_in_client():
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    return client


def test_filter_narrows_to_range():
    # 2026-07-01..2026-07-05 includes Lunch(07-01), Metro(07-02),
    # Electricity(07-03), Pharmacy(07-05) but must exclude later rows.
    resp = _logged_in_client().get(
        "/profile?start=2026-07-01&end=2026-07-05"
    )
    assert resp.status_code == 200
    assert b"Lunch with friends" in resp.data
    assert b"Electricity bill" in resp.data
    assert b"Movie tickets" not in resp.data      # 07-07, outside range
    assert b"Groceries" not in resp.data           # 07-09, outside range


def test_filter_inputs_persist_in_form():
    resp = _logged_in_client().get(
        "/profile?start=2026-07-01&end=2026-07-05"
    )
    assert b'value="2026-07-01"' in resp.data
    assert b'value="2026-07-05"' in resp.data
    # Clear link only shows when a filter is active
    assert b"profile-filter-clear" in resp.data


def test_invalid_date_is_ignored():
    # A malformed date must not crash and must behave like "no filter".
    resp = _logged_in_client().get("/profile?start=garbage")
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data           # full list still shown


def test_empty_range_shows_empty_state():
    resp = _logged_in_client().get(
        "/profile?start=2020-01-01&end=2020-01-31"
    )
    assert resp.status_code == 200
    assert b"No transactions found" in resp.data


def test_unauthenticated_filter_redirects():
    client = app.test_client()
    resp = client.get("/profile?start=2026-07-01&end=2026-07-05")
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", "")


def test_month_filter_shows_that_month():
    # month=2026-07 maps to the seed's month -> all seed rows visible, no empty state.
    resp = _logged_in_client().get("/profile?month=2026-07")
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data
    assert b"No transactions found" not in resp.data


def test_month_with_no_data_shows_empty():
    # A valid month with no expenses yields the empty state.
    resp = _logged_in_client().get("/profile?month=2020-01")
    assert resp.status_code == 200
    assert b"No transactions found" in resp.data


def test_month_dropdown_rendered():
    resp = _logged_in_client().get("/profile")
    assert b"profile-filter-month" in resp.data
    assert b"All time" in resp.data
