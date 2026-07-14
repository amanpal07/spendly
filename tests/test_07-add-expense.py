"""Tests for Step 07 — Add Expense (spec DoD).

Validates the GET/POST ``/expenses/add`` route against the spec's acceptance
criteria, independent of implementation details:

  * Auth guard (logged-out redirect to /login)
  * GET renders the form (amount, category dropdown of exactly the 7 seeded
    categories, date defaulting to today, optional description)
  * POST with valid data inserts exactly one row scoped to the logged-in user
    and redirects to the profile page
  * POST validation failures (bad amount / category / date) re-render the form
    and insert zero rows
  * DB side effects confirm ownership and field values

The root conftest.py isolates the DB via SPENDLLY_DB and seeds a demo user
(demo@spendly.com / demo123) plus 8 sample expenses, so we log in as that user.
"""

import math
from datetime import datetime

import pytest

from app import app
from database.db import get_db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

SEVEN_CATEGORIES = (
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other",
)

TODAY = datetime.now().strftime("%Y-%m-%d")


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


# ------------------------------------------------------------------ #
# Auth guard                                                         #
# ------------------------------------------------------------------ #

def test_get_add_expense_logged_out_redirects_to_login():
    # DoD — visiting GET /expenses/add while logged out redirects to /login
    client = app.test_client()
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/login"


# ------------------------------------------------------------------ #
# GET form rendering (happy path)                                    #
# ------------------------------------------------------------------ #

def test_get_add_expense_form_renders_required_fields():
    # DoD — GET (logged in) renders add_expense.html with the required fields
    resp = _logged_in_client().get("/expenses/add")
    assert resp.status_code == 200
    assert b'name="amount"' in resp.data
    assert b'name="category"' in resp.data
    assert b'name="date"' in resp.data
    assert b'name="description"' in resp.data


def test_get_add_expense_category_dropdown_has_exactly_seven_categories():
    # DoD — the category dropdown contains exactly the 7 seeded categories
    resp = _logged_in_client().get("/expenses/add")
    present = 0
    for cat in SEVEN_CATEGORIES:
        needle = ('<option value="%s"' % cat).encode()
        assert needle in resp.data, "expected category option %r" % cat
        present += 1
    assert present == 7
    # and no out-of-set category leaks into the dropdown
    assert b'<option value="Rent"' not in resp.data
    assert b'<option value="Salary"' not in resp.data


def test_get_add_expense_date_field_defaults_to_today():
    # DoD — the date field defaults to today
    resp = _logged_in_client().get("/expenses/add")
    assert ('value="%s"' % TODAY).encode() in resp.data


def test_get_add_expense_description_field_is_optional():
    # DoD — description is optional (present but not required); page renders 200
    resp = _logged_in_client().get("/expenses/add")
    assert resp.status_code == 200
    assert b'name="description"' in resp.data


# ------------------------------------------------------------------ #
# POST happy path + DB side effects                                  #
# ------------------------------------------------------------------ #

def test_post_add_expense_valid_inserts_one_row_and_redirects():
    # DoD — valid POST inserts exactly one row and redirects to profile
    client = _logged_in_client()
    uid = _demo_user_id()
    before = _expense_count(uid)

    resp = client.post("/expenses/add", data={
        "amount": "50.00",
        "category": "Food",
        "date": TODAY,
        "description": "Lunch test",
    })

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/profile"

    after = _expense_count(uid)
    assert after == before + 1, "expected exactly one new expense row"


def test_post_add_expense_inserted_row_belongs_to_user_with_correct_fields():
    # DoD — the new row is scoped to the logged-in user with correct values
    client = _logged_in_client()
    uid = _demo_user_id()

    client.post("/expenses/add", data={
        "amount": "1234.56",
        "category": "Transport",
        "date": TODAY,
        "description": "Cab ride unique 1234",
    })

    db = get_db()
    try:
        row = db.execute(
            "SELECT user_id, amount, category, date, description "
            "FROM expenses WHERE description = ? ORDER BY id DESC LIMIT 1",
            ("Cab ride unique 1234",),
        ).fetchone()
    finally:
        db.close()

    assert row is not None
    assert row["user_id"] == uid, "row must belong to the logged-in user"
    assert math.isclose(row["amount"], 1234.56), "amount stored incorrectly"
    assert row["category"] == "Transport"
    assert row["date"] == TODAY
    assert row["description"] == "Cab ride unique 1234"


def test_post_add_expense_empty_description_stored_as_null():
    # DoD — description is optional; an empty one is stored as NULL
    client = _logged_in_client()

    client.post("/expenses/add", data={
        "amount": "25.00",
        "category": "Other",
        "date": TODAY,
        "description": "",
    })

    db = get_db()
    try:
        row = db.execute(
            "SELECT description FROM expenses "
            "WHERE amount = ? AND category = ? AND date = ? ORDER BY id DESC LIMIT 1",
            (25.0, "Other", TODAY),
        ).fetchone()
    finally:
        db.close()

    assert row is not None
    assert row["description"] is None


def test_new_expense_appears_on_profile_after_redirect():
    # DoD — the new expense shows up on the profile page immediately
    client = _logged_in_client()

    client.post("/expenses/add", data={
        "amount": "77.77",
        "category": "Health",
        "date": TODAY,
        "description": "PHARMACY_UNIQUE_77",
    })

    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"PHARMACY_UNIQUE_77" in resp.data


# ------------------------------------------------------------------ #
# POST validation errors                                             #
# ------------------------------------------------------------------ #

INVALID_PAYLOADS = [
    # non-numeric amount
    {"amount": "abc", "category": "Food", "date": TODAY, "description": ""},
    # zero amount (non-positive)
    {"amount": "0", "category": "Food", "date": TODAY, "description": ""},
    # negative amount
    {"amount": "-10", "category": "Food", "date": TODAY, "description": ""},
    # non-finite: +inf
    {"amount": "inf", "category": "Food", "date": TODAY, "description": ""},
    # non-finite: nan
    {"amount": "nan", "category": "Food", "date": TODAY, "description": ""},
    # out-of-set category
    {"amount": "10", "category": "Rent", "date": TODAY, "description": ""},
    # malformed date (wrong format)
    {"amount": "10", "category": "Food", "date": "not-a-date", "description": ""},
    # malformed date (invalid calendar date)
    {"amount": "10", "category": "Food", "date": "2026-13-40", "description": ""},
]


@pytest.mark.parametrize("payload", INVALID_PAYLOADS)
def test_post_add_expense_validation_error_rerenders_and_inserts_no_row(payload):
    # DoD — any validation failure re-renders the form and inserts zero rows
    client = _logged_in_client()
    uid = _demo_user_id()
    before = _expense_count(uid)

    resp = client.post("/expenses/add", data=payload)

    # form is re-rendered, not redirected
    assert resp.status_code == 200, "form should re-render on validation error"
    assert b'name="category"' in resp.data, "add-expense form should be re-rendered"
    # the submitted amount is echoed back into the form
    assert ('value="%s"' % payload["amount"]).encode() in resp.data

    after = _expense_count(uid)
    assert after == before, "no expense row should be inserted on validation error"
