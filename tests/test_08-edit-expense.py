"""Tests for Step 08 — Edit Expense (spec DoD).

Validates the GET/POST ``/expenses/<id>/edit`` route against the spec's
acceptance criteria, independent of implementation details:

  * Auth guard (logged-out redirect to /login) for both GET and POST
  * GET (logged in) renders edit_expense.html with every field pre-filled from
    the existing expense, including the correct category ``selected`` in a
    dropdown of exactly the 7 seeded categories
  * POST with valid data updates exactly that one row (scoped to the logged-in
    user) and redirects to /profile
  * POST validation failures (bad amount / category / date) re-render the form
    with an error and change zero rows
  * Edited values appear on the profile page immediately, and no other row is
    affected
  * A user cannot edit another user's expense (ownership enforcement): the row
    is never matched, so GET/POST redirect to /profile and nothing is changed
  * The profile transaction list shows a working "Edit" link per expense

The root conftest.py isolates the DB via SPENDLLY_DB and seeds a demo user
(demo@spendly.com / demo123) plus 8 sample expenses, resetting the expenses
table before each test. We therefore log in as that user and fetch expense ids
dynamically (never hardcoded).
"""

import math
import re

import pytest

from app import app
from database.db import get_db
from werkzeug.security import generate_password_hash

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

SEVEN_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)


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


def _edit_url(expense_id):
    """Build the edit-expense URL via url_for (never hardcode dynamic paths)."""
    with app.test_request_context():
        from flask import url_for

        return url_for("edit_expense", id=expense_id)


def _create_other_user_expense():
    """Insert a second user plus one expense owned by them.

    Returns ``(other_user_id, other_expense_id)``. The caller must delete these
    in a finally block; the expenses table is wiped by the conftest fixture
    before the next test, but the users row must be removed too for isolation.
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


def test_get_edit_expense_logged_out_redirects_to_login():
    # DoD — visiting GET /expenses/<id>/edit while logged out redirects to /login
    client = app.test_client()
    resp = client.get(_edit_url(1))
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/login"


def test_post_edit_expense_logged_out_redirects_to_login():
    # The auth guard must also block the POST handler for anonymous sessions.
    client = app.test_client()
    resp = client.post(
        _edit_url(1),
        data={
            "amount": "10.00",
            "category": "Food",
            "date": "2026-07-01",
            "description": "",
        },
    )
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/login"


# ------------------------------------------------------------------ #
# GET form rendering (happy path / pre-fill)                         #
# ------------------------------------------------------------------ #


def test_get_edit_expense_renders_prefilled_form():
    # DoD — GET (logged in) renders edit_expense.html with required fields
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    url = _edit_url(expense["id"])
    resp = client.get(url)

    assert resp.status_code == 200
    assert b'name="amount"' in resp.data
    assert b'name="category"' in resp.data
    assert b'name="date"' in resp.data
    assert b'name="description"' in resp.data
    # the form posts back to the edit route for this expense id
    assert ('action="%s"' % url).encode() in resp.data


def test_get_edit_expense_prefills_amount_date_description():
    # DoD — every field is pre-filled from the loaded row on GET
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    resp = client.get(_edit_url(expense["id"]))
    html = resp.data.decode("utf-8")

    assert (
        'value="%.2f"' % expense["amount"]
    ).encode() in resp.data, "amount should be pre-filled (2dp)"
    assert (
        'value="%s"' % expense["date"]
    ).encode() in resp.data, "date should be pre-filled"
    # description is pre-filled (checked against the raw html so surrounding
    # attribute quoting/whitespace cannot cause a false negative)
    assert expense["description"] in html, "description should be pre-filled"


def test_get_edit_expense_category_dropdown_has_exactly_seven_categories():
    # DoD — the category dropdown contains exactly the 7 seeded categories
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    resp = client.get(_edit_url(expense["id"]))

    present = 0
    for cat in SEVEN_CATEGORIES:
        needle = ('<option value="%s"' % cat).encode()
        assert needle in resp.data, "expected category option %r" % cat
        present += 1
    assert present == 7
    # and no out-of-set category leaks into the dropdown
    assert b'<option value="Rent"' not in resp.data
    assert b'<option value="Salary"' not in resp.data


def test_get_edit_expense_current_category_is_selected():
    # DoD — the expense's current category is the only one marked `selected`
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    html = client.get(_edit_url(expense["id"])).data.decode("utf-8")

    current = expense["category"]
    m = re.search(r'<option[^>]*value="%s"[^>]*>' % re.escape(current), html)
    assert m, "option for current category %r not found" % current
    assert "selected" in m.group(0), "current category should be selected"

    # a different category must NOT be selected
    other = next(c for c in SEVEN_CATEGORIES if c != current)
    m2 = re.search(r'<option[^>]*value="%s"[^>]*>' % re.escape(other), html)
    assert m2, "option for category %r not found" % other
    assert "selected" not in m2.group(0), "wrong category must not be selected"


def test_get_edit_expense_unknown_id_redirects_to_profile():
    # Ownership/no-leak rule: a missing row (any id) redirects to profile, never 404
    client = _logged_in_client()
    uid = _demo_user_id()
    before = _expense_count(uid)
    resp = client.get(_edit_url(999999))
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"
    assert _expense_count(uid) == before


# ------------------------------------------------------------------ #
# POST happy path + DB side effects                                  #
# ------------------------------------------------------------------ #


def test_post_edit_expense_valid_updates_one_row_and_redirects():
    # DoD — valid POST updates exactly that one row and redirects to profile
    client = _logged_in_client()
    uid = _demo_user_id()
    expenses = _fetch_demo_expenses()
    target = expenses[0]
    other = expenses[1]
    before_count = _expense_count(uid)

    resp = client.post(
        _edit_url(target["id"]),
        data={
            "amount": "543.21",
            "category": "Shopping",
            "date": "2026-06-15",
            "description": "EDITED_DESC_UNIQUE_543",
        },
    )

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"

    # an edit, not an insert — total row count is unchanged
    assert _expense_count(uid) == before_count

    updated = _expense_by_id(target["id"])
    assert updated is not None
    assert updated["user_id"] == uid, "row must remain owned by the logged-in user"
    assert math.isclose(updated["amount"], 543.21), "amount not updated"
    assert updated["category"] == "Shopping"
    assert updated["date"] == "2026-06-15"
    assert updated["description"] == "EDITED_DESC_UNIQUE_543"

    # a different row is completely untouched (proves "exactly that one row")
    untouched = _expense_by_id(other["id"])
    assert math.isclose(untouched["amount"], other["amount"])
    assert untouched["category"] == other["category"]
    assert untouched["date"] == other["date"]
    assert untouched["description"] == other["description"]


def test_post_edit_expense_empty_description_stored_as_null():
    # Mirror of Add Expense: description is optional and an empty one is NULL
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    client.post(
        _edit_url(expense["id"]),
        data={
            "amount": "40.00",
            "category": "Other",
            "date": "2026-07-01",
            "description": "",
        },
    )
    row = _expense_by_id(expense["id"])
    assert row["description"] is None


def test_edited_expense_appears_on_profile_after_redirect():
    # DoD — edited values show up on the profile page immediately
    client = _logged_in_client()
    target = _fetch_demo_expenses()[0]
    new_desc = "PROFILE_EDIT_UNIQUE_998"
    new_amount = "888.88"

    client.post(
        _edit_url(target["id"]),
        data={
            "amount": new_amount,
            "category": "Health",
            "date": "2026-05-05",
            "description": new_desc,
        },
    )

    resp = client.get("/profile")
    assert resp.status_code == 200
    assert new_desc.encode() in resp.data, "edited description must appear on profile"
    assert new_amount.encode() in resp.data, "edited amount must appear on profile"


def test_post_edit_expense_unknown_id_redirects_and_changes_nothing():
    # Ownership/no-leak rule for POST: a missing row redirects, no UPDATE occurs
    client = _logged_in_client()
    uid = _demo_user_id()
    before_count = _expense_count(uid)

    resp = client.post(
        _edit_url(999999),
        data={
            "amount": "10.00",
            "category": "Food",
            "date": "2026-07-01",
            "description": "SHOULD_NOT_PERSIST",
        },
    )
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"
    assert _expense_count(uid) == before_count

    # the bogus description must not have been written anywhere
    db = get_db()
    try:
        leaked = db.execute(
            "SELECT COUNT(*) AS c FROM expenses WHERE description = ?",
            ("SHOULD_NOT_PERSIST",),
        ).fetchone()["c"]
    finally:
        db.close()
    assert leaked == 0


# ------------------------------------------------------------------ #
# POST validation errors (parametrised)                              #
# ------------------------------------------------------------------ #

INVALID_EDIT_PAYLOADS = [
    # non-numeric amount
    {"amount": "abc", "category": "Food", "date": "2026-07-01", "description": ""},
    # zero amount (non-positive)
    {"amount": "0", "category": "Food", "date": "2026-07-01", "description": ""},
    # negative amount
    {"amount": "-10", "category": "Food", "date": "2026-07-01", "description": ""},
    # non-finite: +inf
    {"amount": "inf", "category": "Food", "date": "2026-07-01", "description": ""},
    # non-finite: nan
    {"amount": "nan", "category": "Food", "date": "2026-07-01", "description": ""},
    # out-of-set category
    {"amount": "10", "category": "Rent", "date": "2026-07-01", "description": ""},
    # malformed date (wrong format)
    {"amount": "10", "category": "Food", "date": "not-a-date", "description": ""},
    # malformed date (invalid calendar date)
    {"amount": "10", "category": "Food", "date": "2026-13-40", "description": ""},
]


@pytest.mark.parametrize("payload", INVALID_EDIT_PAYLOADS)
def test_post_edit_expense_validation_error_rerenders_and_changes_no_row(payload):
    # DoD — any validation failure re-renders the form and changes zero rows
    client = _logged_in_client()
    uid = _demo_user_id()
    target = _fetch_demo_expenses()[0]
    before_count = _expense_count(uid)
    before = _expense_by_id(target["id"])

    resp = client.post(_edit_url(target["id"]), data=payload)

    # form is re-rendered, not redirected
    assert resp.status_code == 200, "form should re-render on validation error"
    assert b'name="category"' in resp.data, "edit-expense form should be re-rendered"
    # the submitted (invalid) amount is echoed back into the form
    assert (
        'value="%s"' % payload["amount"]
    ).encode() in resp.data, "user input should be echoed back on validation error"

    # no row inserted, and the targeted row is completely unchanged
    assert (
        _expense_count(uid) == before_count
    ), "no expense row should change on validation error"
    after = _expense_by_id(target["id"])
    assert after is not None
    assert math.isclose(after["amount"], before["amount"])
    assert after["category"] == before["category"]
    assert after["date"] == before["date"]
    assert after["description"] == before["description"]


# ------------------------------------------------------------------ #
# Ownership enforcement: another user's expense                      #
# ------------------------------------------------------------------ #


def test_get_edit_other_users_expense_redirects_to_profile():
    # DoD — a row owned by another user yields no match, so GET redirects to /profile
    client = _logged_in_client()
    oid, eid = _create_other_user_expense()
    try:
        resp = client.get(_edit_url(eid))
        assert resp.status_code == 302
        assert resp.headers.get("Location") == "/profile"
    finally:
        _delete_other_user(oid)


def test_post_edit_other_users_expense_redirects_and_changes_nothing():
    # DoD — a user cannot edit another user's expense; no update occurs
    client = _logged_in_client()
    oid, eid = _create_other_user_expense()
    try:
        before = _expense_by_id(eid)
        assert before is not None

        resp = client.post(
            _edit_url(eid),
            data={
                "amount": "1.00",
                "category": "Food",
                "date": "2026-01-01",
                "description": "HACKED_DESCRIPTION",
            },
        )
        assert resp.status_code == 302
        assert resp.headers.get("Location") == "/profile"

        after = _expense_by_id(eid)
        assert after is not None
        # the other user's row is completely unchanged and still owned by them
        assert after["user_id"] == before["user_id"]
        assert math.isclose(after["amount"], before["amount"])
        assert after["category"] == before["category"]
        assert after["date"] == before["date"]
        assert after["description"] == before["description"]
    finally:
        _delete_other_user(oid)


# ------------------------------------------------------------------ #
# Profile "Edit" link per expense                                    #
# ------------------------------------------------------------------ #


def test_profile_shows_edit_link_per_expense():
    # DoD — the profile transaction list shows a working "Edit" link per expense
    client = _logged_in_client()
    expenses = _fetch_demo_expenses()
    resp = client.get("/profile")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    for expense in expenses:
        link = _edit_url(expense["id"])
        assert link in html, "missing edit link for expense %d" % expense["id"]


def test_profile_edit_link_resolves_to_prefilled_form():
    # The edit link must lead to a real, pre-filled edit form (not a 404/redirect)
    client = _logged_in_client()
    expense = _fetch_demo_expenses()[0]
    link = _edit_url(expense["id"])
    resp = client.get(link)
    assert resp.status_code == 200
    assert b'name="amount"' in resp.data
