"""Tests for Step 5 — Backend Routes for Profile Page (spec DoD).

Confirms /profile now renders LIVE data from the database rather than the
hardcoded demo dicts it used in Step 4.
"""

from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def _logged_in_client():
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    return client


def test_profile_uses_real_user():
    # DoD #2 — shows the seeded user, not the old hardcoded "Aanya Sharma"
    resp = _logged_in_client().get("/profile")
    assert resp.status_code == 200
    assert b"Demo User" in resp.data
    assert b"demo@spendly.com" in resp.data
    assert b"Aanya Sharma" not in resp.data


def test_profile_summary_stats():
    # DoD #3/#4/#5 — total spent, transaction count, top category
    resp = _logged_in_client().get("/profile")
    assert b"3,981.45" in resp.data          # total_spent formatted with comma
    assert b"Bills" in resp.data             # top_category
    # one <tr> header + 8 body rows == 9 total table rows
    assert resp.data.count(b"<tr>") == 9


def test_transactions_newest_first():
    # DoD #6 — newest date appears before the oldest in the rendered HTML
    resp = _logged_in_client().get("/profile")
    assert resp.data.find(b"2026-07-11") < resp.data.find(b"2026-07-01")


def test_category_breakdown_top_is_100():
    # DoD #7 — largest category bar width is 100%
    resp = _logged_in_client().get("/profile")
    assert b"--w: 100%" in resp.data
