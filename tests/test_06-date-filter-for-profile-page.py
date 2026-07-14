"""Tests for Step 6 — Date Filter for Profile Page (spec DoD).

Written from `.claude/specs/06-date-filter-for-profile-page.md`, NOT from the
implementation. The seed expenses are all dated in July 2026 with known
descriptions, so range assertions use those descriptions rather than
hardcoding absolute totals (the local DB may hold extra rows beyond the seed).
"""

from database.db import get_db

from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def _logged_in_client():
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    return client


def _expense_count():
    db = get_db()
    n = db.execute("SELECT COUNT(*) AS c FROM expenses").fetchone()["c"]
    db.close()
    return n


# --- Happy path: no filter shows the full (seed) data ----------------------

def test_no_filter_returns_200_and_seed_rows():
    resp = _logged_in_client().get("/profile")
    assert resp.status_code == 200
    # A spread of known July-2026 seed descriptions must be present.
    for desc in [b"Lunch with friends", b"Metro card recharge",
                 b"Electricity bill", b"Pharmacy", b"Movie tickets",
                 b"Groceries", b"Coffee"]:
        assert desc in resp.data


# --- Range filter narrows to the inclusive window ---------------------------

def test_range_narrows_transactions():
    resp = _logged_in_client().get(
        "/profile?start=2026-07-01&end=2026-07-05"
    )
    assert resp.status_code == 200
    # Inside the window (07-01 .. 07-05).
    assert b"Lunch with friends" in resp.data
    assert b"Electricity bill" in resp.data
    # Outside the window (07-07, 07-09, 07-11).
    assert b"Movie tickets" not in resp.data
    assert b"Groceries" not in resp.data
    assert b"Coffee" not in resp.data


def test_range_narrows_category_breakdown():
    # "Food" appears (Lunch on 07-01) but "Entertainment" (Movie on 07-07) must
    # be absent, proving the breakdown reflects the filtered set.
    resp = _logged_in_client().get(
        "/profile?start=2026-07-01&end=2026-07-05"
    )
    assert b"Food" in resp.data
    assert b"Entertainment" not in resp.data


def test_full_month_range_shows_everything():
    resp = _logged_in_client().get(
        "/profile?start=2026-07-01&end=2026-07-31"
    )
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data
    assert b"Coffee" in resp.data


# --- Month filter (whole month) ---------------------------------------------

def test_month_filter_shows_that_month():
    resp = _logged_in_client().get("/profile?month=2026-07")
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data          # July expense present
    assert b"Entertainment" in resp.data          # category breakdown present


def test_month_with_no_data_is_empty():
    resp = _logged_in_client().get("/profile?month=2020-01")
    assert resp.status_code == 200
    assert b"No transactions found" in resp.data
    # No category rows either.
    assert b"Food" not in resp.data


# --- Edge cases -------------------------------------------------------------

def test_empty_range_shows_empty_state():
    resp = _logged_in_client().get(
        "/profile?start=2020-01-01&end=2020-01-31"
    )
    assert resp.status_code == 200
    assert b"No transactions found" in resp.data


def test_invalid_date_is_ignored():
    # Malformed date must not crash and must behave like "no filter".
    resp = _logged_in_client().get("/profile?start=not-a-date")
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data


def test_invalid_month_format_is_ignored():
    resp = _logged_in_client().get("/profile?month=2026-13")
    assert resp.status_code == 200
    assert b"Movie tickets" in resp.data          # treated as no filter


# --- Auth guard -------------------------------------------------------------

def test_unauthenticated_filter_redirects():
    client = app.test_client()
    resp = client.get("/profile?start=2026-07-01&end=2026-07-05")
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", "")


# --- DB side effects: filter must be read-only ------------------------------

def test_filter_does_not_mutate_expenses():
    before = _expense_count()
    client = _logged_in_client()
    for _ in range(3):
        client.get("/profile?start=2026-07-01&end=2026-07-05")
        client.get("/profile?month=2020-01")
        client.get("/profile?start=not-a-date")
    after = _expense_count()
    assert before == after
