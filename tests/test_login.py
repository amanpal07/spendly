"""Smoke tests for Step 3 — Login and Logout (spec DoD #1-#9).

These exercise the Flask test client against the real app (importing ``app``
runs ``init_db()``/``seed_db()``, so the demo user ``demo@spendly.com`` /
``demo123`` is available). They are smoke tests, not security tests: CSRF and
password-length checks are intentionally out of scope.
"""

from app import app

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
GENERIC_ERROR = "Invalid email or password."


def test_login_get_renders():
    # DoD #1
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data


def test_login_valid_demo():
    # DoD #2, #3 — correct creds sign in and redirect to "/"
    client = app.test_client()
    resp = client.post(
        "/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"
    assert "Set-Cookie" in resp.headers  # session established


def test_login_wrong_password():
    # DoD #4 — wrong password shows generic error, no session
    client = app.test_client()
    resp = client.post(
        "/login", data={"email": DEMO_EMAIL, "password": "wrongpass"}
    )
    assert resp.status_code == 200
    assert GENERIC_ERROR.encode() in resp.data
    assert "Set-Cookie" not in resp.headers


def test_login_unknown_email():
    # DoD #5 — unknown email shows the SAME generic error
    client = app.test_client()
    resp = client.post(
        "/login", data={"email": "nobody@example.com", "password": "anything"}
    )
    assert resp.status_code == 200
    assert GENERIC_ERROR.encode() in resp.data


def test_login_case_insensitive_email():
    # DoD #6 — email differing only by case still matches
    client = app.test_client()
    resp = client.post(
        "/login", data={"email": "Demo@Spendly.com", "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_login_error_preserves_email():
    # DoD #7 — entered email echoed back into the form on failure
    client = app.test_client()
    resp = client.post(
        "/login", data={"email": "nobody@example.com", "password": "x"}
    )
    assert b'value="nobody@example.com"' in resp.data


def test_logout_clears_session():
    # DoD #8, #9 — logout redirects to /login and drops the session
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
