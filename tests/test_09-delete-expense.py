"""Tests for Step 09 — Delete Expense (spec DoD).

Validates the POST ``/expenses/<int:id>/delete`` route against the spec's
acceptance criteria, independent of implementation details:

  * Auth guard (logged-out POST redirects to /login and deletes nothing)
  * Destructive action lives on POST only — GET must NOT delete (405 or a safe
    non-deleting redirect)
  * POST (logged in) removes exactly that one row scoped to the logged-in
    user, commits, and redirects to /profile
  * Filter preservation — the redirect Location carries the active
    start/end/month query args (and is a bare /profile when none are active)
  * Ownership enforcement — a user cannot delete another user's expense (0 rows
    removed, safe redirect, other user's row untouched)
  * Unknown id — redirects to /profile and removes 0 rows (no 404-leak)
  * DB side effects — the demo user's row count drops by exactly 1, no other
    row is affected, and the deleted expense disappears from the profile list
  * The profile transaction list shows a working "Delete" trigger per expense

The root conftest.py isolates the DB via SPENDLLY_DB and seeds a demo user
(demo@spendly.com / demo123) plus 8 sample expenses, resetting the expenses
table before each test. We therefore log in as that user and fetch expense ids
dynamically (never hardcoded).
"""

from app import app
from database.db import get_db
from werkzeug.security import generate_password_hash

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #


def _logged_in_client():
    """Return a test client already authenticated as the seeded demo user."""
    client = app.test_client()
    client.post("/login", data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    return client


def _demo_user_id():
    db = get_db()
    try:
        uid = db.execute(
            "SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)
        ).fetchone()["id"]
    finally:
        db.close()
    return uid


def _expense_count(user_id):
    db = get_db()
    try:
        c = db.execute(
            "SELECT COUNT(*) AS c FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()["c"]
    finally:
        db.close()
    return c


def _fetch_demo_expenses():
    """Return the demo user's currently-seeded expenses as a list of dicts."""
    uid = _demo_user_id()
    db = get_db()
    try:
        rows = db.execute(
            "SELECT id, amount, category, date, description "
            "FROM expenses WHERE user_id = ? ORDER BY id",
            (uid,),
        ).fetchall()
    finally:
        db.close()
    return [dict(r) for r in rows]


def _expense_by_id(expense_id):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        db.close()
    return dict(row) if row is not None else None


def _delete_url(expense_id):
    """Build the delete-expense URL via url_for (never hardcode dynamic paths)."""
    with app.test_request_context():
        from flask import url_for

        return url_for("delete_expense", id=expense_id)


def _create_other_user_expense():
    """Insert a second user plus one expense owned by them.

    Returns ``(other_user_id, other_expense_id)``. The caller must delete these
    in a finally block for isolation (the conftest fixture wipes the expenses
    table before the next test, but the users row must be removed too).
    """
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other User", "other@spendly.com", generate_password_hash("other1234")),
        )
        db.commit()
        oid = db.execute(
            "SELECT id FROM users WHERE email = ?", ("other@spendly.com",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (oid, 999.99, "Food", "2026-07-01", "OTHER_USER_EXPENSE"),
        )
        db.commit()
        eid = db.execute(
            "SELECT id FROM expenses WHERE description = ?", ("OTHER_USER_EXPENSE",)
        ).fetchone()["id"]
    finally:
        db.close()
    return oid, eid


def _delete_other_user(oid):
    db = get_db()
    try:
        db.execute("DELETE FROM expenses WHERE user_id = ?", (oid,))
        db.execute("DELETE FROM users WHERE id = ?", (oid,))
        db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------ #
# Auth guard                                                         #
# ------------------------------------------------------------------ #


def test_post_delete_expense_logged_out_redirects_to_login():
    # DoD — a logged-out POST redirects to /login and deletes nothing
    client = app.test_client()
    uid = _demo_user_id()
    target_id = _fetch_demo_expenses()[0]["id"]
    before = _expense_count(uid)

    resp = client.post(_delete_url(target_id))

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/login"
    # absolutely nothing was deleted
    assert _expense_count(uid) == before
    assert _expense_by_id(target_id) is not None


# ------------------------------------------------------------------ #
# Method restriction: GET must not delete                            #
# ------------------------------------------------------------------ #


def test_get_delete_expense_does_not_delete():
    # DoD — GET on the delete route must NOT perform a delete (405 or a safe
    # non-deleting redirect); the targeted row must remain untouched.
    client = _logged_in_client()
    uid = _demo_user_id()
    target = _fetch_demo_expenses()[0]
    before = _expense_count(uid)

    resp = client.get(_delete_url(target["id"]))

    # Either a 405 Method Not Allowed (route is POST-only) or a safe redirect
    # back to profile — but in no case a deletion.
    assert resp.status_code in (302, 405), "GET must not be a destructive 200"
    if resp.status_code == 302:
        assert resp.headers.get("Location") == "/profile"
    assert _expense_count(uid) == before, "GET delete must not remove any row"
    assert _expense_by_id(target["id"]) is not None, "row must survive a GET"


# ------------------------------------------------------------------ #
# POST happy path + DB side effects                                  #
# ------------------------------------------------------------------ #


def test_post_delete_expense_valid_deletes_one_row_and_redirects():
    # DoD — valid POST removes exactly that one row and redirects to /profile
    client = _logged_in_client()
    uid = _demo_user_id()
    expenses = _fetch_demo_expenses()
    target = expenses[0]
    before = _expense_count(uid)

    resp = client.post(_delete_url(target["id"]))

    assert resp.status_code == 302
    # With no active filter the redirect target is exactly /profile
    assert resp.headers.get("Location") == "/profile"

    # exactly one row removed
    assert _expense_count(uid) == before - 1, "exactly one row should be deleted"


def test_post_delete_expense_removes_only_the_targeted_row():
    # DoD — the deleted row is gone while every other row is untouched
    client = _logged_in_client()
    uid = _demo_user_id()
    expenses = _fetch_demo_expenses()
    target = expenses[0]
    other = expenses[1]

    client.post(_delete_url(target["id"]))

    # the targeted row no longer exists
    assert _expense_by_id(target["id"]) is None
    # a sibling row is completely unaffected (proves "exactly that one row")
    assert _expense_by_id(other["id"]) is not None
    assert math_isclose_amount(other["id"], other["amount"])
    assert _expense_by_id(other["id"])["category"] == other["category"]
    assert _expense_by_id(other["id"])["date"] == other["date"]


def test_post_delete_expense_deleted_row_disappears_from_profile():
    # DoD — after the redirect the deleted expense is no longer on the profile list
    client = _logged_in_client()
    target = _fetch_demo_expenses()[0]
    desc = target["description"]

    client.post(_delete_url(target["id"]))

    resp = client.get("/profile")
    assert resp.status_code == 200
    # the deleted transaction must not be listed anymore
    assert desc.encode() not in resp.data, "deleted expense should vanish from profile"
    # the profile still renders the remaining transactions (summary intact)
    assert b"profile-actions" in resp.data


def test_post_delete_expense_unknown_id_redirects_and_removes_zero_rows():
    # Ownership/no-leak rule: a missing row (any id) redirects, no DELETE occurs
    client = _logged_in_client()
    uid = _demo_user_id()
    before = _expense_count(uid)

    resp = client.post(_delete_url(999999))

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"
    assert _expense_count(uid) == before, "no row should be removed for a bogus id"


# ------------------------------------------------------------------ #
# Filter preservation on redirect                                     #
# ------------------------------------------------------------------ #


def test_post_delete_expense_without_filters_redirects_to_bare_profile():
    # DoD — no active filter means a plain /profile redirect (no stray query args)
    client = _logged_in_client()
    target = _fetch_demo_expenses()[0]

    resp = client.post(_delete_url(target["id"]))

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"


def test_post_delete_expense_preserves_filter_args_in_redirect():
    # DoD — the active start/end/month filter args are carried onto the redirect
    client = _logged_in_client()
    target = _fetch_demo_expenses()[0]

    resp = client.post(
        _delete_url(target["id"]),
        query_string={
            "start": "2026-07-01",
            "end": "2026-07-31",
            "month": "2026-07",
        },
    )

    assert resp.status_code == 302
    location = resp.headers.get("Location")
    assert location is not None
    assert location.startswith("/profile"), "must redirect to profile"
    # each active filter arg must be preserved on the redirect target
    assert "start=2026-07-01" in location
    assert "end=2026-07-31" in location
    assert "month=2026-07" in location
    # and exactly one row was still deleted
    uid = _demo_user_id()
    assert _expense_count(uid) == 8 - 1


# ------------------------------------------------------------------ #
# Ownership enforcement: another user's expense                      #
# ------------------------------------------------------------------ #


def test_post_delete_other_users_expense_removes_zero_rows_and_redirects():
    # DoD — a user cannot delete another user's expense; 0 rows removed, safe
    # redirect to /profile, and the other user's row stays intact.
    client = _logged_in_client()
    oid, eid = _create_other_user_expense()
    try:
        uid = _demo_user_id()
        demo_before = _expense_count(uid)
        other_before = _expense_by_id(eid)
        assert other_before is not None

        resp = client.post(_delete_url(eid))

        assert resp.status_code == 302
        assert resp.headers.get("Location") == "/profile"

        # the demo user lost no rows of their own
        assert _expense_count(uid) == demo_before
        # the other user's expense is completely untouched and still owned by them
        after = _expense_by_id(eid)
        assert after is not None
        assert after["user_id"] == other_before["user_id"]
        assert math_isclose_amount(eid, other_before["amount"])
        assert after["category"] == other_before["category"]
        assert after["date"] == other_before["date"]
        assert after["description"] == other_before["description"]
    finally:
        _delete_other_user(oid)


# ------------------------------------------------------------------ #
# Profile "Delete" trigger per expense                               #
# ------------------------------------------------------------------ #


def test_profile_shows_delete_trigger_per_expense():
    # DoD — the profile transaction list shows a "Delete" trigger per expense,
    # carrying that expense's id (data-id), next to the existing Edit link.
    client = _logged_in_client()
    expenses = _fetch_demo_expenses()
    resp = client.get("/profile")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # the "Edit" link and a "Delete" trigger both exist in the Actions column
    assert "Edit" in html
    assert "Delete" in html

    for expense in expenses:
        # each row carries its own id on the delete trigger (data-id="<id>")
        needle = 'data-id="%d"' % expense["id"]
        assert needle in html, "missing delete trigger for expense %d" % expense["id"]
        # and the trigger is a real button styled as the delete control
        assert (
            'class="profile-delete-trigger"' in html
        ), "delete trigger should use the profile-delete-trigger class"


def test_profile_delete_trigger_resolves_to_post_only_route():
    # The delete trigger drives a POST-only route; a GET on it must not delete,
    # confirming the destructive action is not exposed on GET.
    client = _logged_in_client()
    target = _fetch_demo_expenses()[0]
    uid = _demo_user_id()
    before = _expense_count(uid)

    # Hitting the route via GET (as the trigger's underlying URL) leaves data intact
    resp = client.get(_delete_url(target["id"]))
    assert resp.status_code in (302, 405)
    assert _expense_count(uid) == before


# ------------------------------------------------------------------ #
# Small local helper (float compare without importing math at module top) #
# ------------------------------------------------------------------ #


def math_isclose_amount(expense_id, expected):
    row = _expense_by_id(expense_id)
    if row is None:
        return False
    return abs(row["amount"] - expected) < 1e-9
