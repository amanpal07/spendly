"""Smoke tests for Step 4 — Profile Page (spec DoD #1-#7)."""

from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def test_profile_redirects_anonymous():
    # DoD #1 — unauthenticated visitors are sent to /login
    client = app.test_client()
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_profile_renders_for_logged_in():
    # DoD #2-#6 — signed-in demo user sees the four sections
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"Demo User" in resp.data            # user info card (real seeded user)
    assert b"demo@spendly.com" in resp.data      # user info card
    assert b"Recent transactions" in resp.data   # table
    assert b"Spending by category" in resp.data  # breakdown
