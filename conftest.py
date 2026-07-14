import os
import tempfile

import pytest

# Isolate the test run from the developer's real expense_tracker.db.
# Spendly reads its DB path from SPENDLLY_DB at import time in database/db.py,
# so this must be set before `app` (and thus database.db) is first imported —
# which is why it lives in a root conftest.py loaded ahead of any test module.
_TEST_DB = os.path.join(tempfile.gettempdir(), "spendly_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["SPENDLLY_DB"] = _TEST_DB

from database.db import get_db

# The 8 sample expenses seeded by database.db.seed_db. Mirrored here so the
# isolation fixture below can restore a pristine expense set before each test.
SEED_EXPENSES = [
    (320.50, "Food", "2026-07-01", "Lunch with friends"),
    (200.00, "Transport", "2026-07-02", "Metro card recharge"),
    (1450.75, "Bills", "2026-07-03", "Electricity bill"),
    (250.00, "Health", "2026-07-05", "Pharmacy"),
    (600.00, "Entertainment", "2026-07-07", "Movie tickets"),
    (890.20, "Shopping", "2026-07-09", "Groceries"),
    (150.00, "Other", "2026-07-10", "Miscellaneous"),
    (120.00, "Food", "2026-07-11", "Coffee"),
]


@pytest.fixture(autouse=True, scope="function")
def _isolate_expenses():
    """Reset the expenses table to the seeded 8 rows before every test.

    The test DB is shared across all test modules in a session, but some tests
    (e.g. the add-expense POST suite) insert rows while others (e.g. the profile
    summary-stats test) assert a pristine 8-row seed. Resetting per test keeps
    every module independent of run order.
    """
    db = get_db()
    try:
        db.execute("DELETE FROM expenses")
        uid = db.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()["id"]
        db.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [(uid, amount, category, date, description)
             for (amount, category, date, description) in SEED_EXPENSES],
        )
        db.commit()
    finally:
        db.close()
    yield
