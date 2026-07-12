"""Database helpers for Spendly.

Step 1 — Database Setup. Implements:
  get_db()    — opens a SQLite connection with row_factory + foreign keys on
  init_db()   — creates the users and expenses tables (idempotent)
  seed_db()   — inserts demo user + sample expenses, only if empty
"""

import sqlite3

from werkzeug.security import generate_password_hash

# SQLite file in the project root (ignored by .gitignore).
DATABASE = "expense_tracker.db"


def get_db():
    """Open and return a SQLite connection with the project defaults applied.

    Sets ``row_factory`` for dict-like row access and enables foreign-key
    enforcement via ``PRAGMA foreign_keys = ON``.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the ``users`` and ``expenses`` tables if they do not exist yet.

    Safe to call multiple times.
    """
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    """Seed a demo user and 8 sample expenses.

    Returns early if the ``users`` table already contains data, so re-running
    never duplicates records.
    """
    conn = get_db()

    if conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"] > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )

    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    expenses = [
        (user_id, 320.50, "Food",          "2026-07-01", "Lunch with friends"),
        (user_id, 200.00, "Transport",     "2026-07-02", "Metro card recharge"),
        (user_id, 1450.75, "Bills",        "2026-07-03", "Electricity bill"),
        (user_id, 250.00, "Health",        "2026-07-05", "Pharmacy"),
        (user_id, 600.00, "Entertainment", "2026-07-07", "Movie tickets"),
        (user_id, 890.20, "Shopping",      "2026-07-09", "Groceries"),
        (user_id, 150.00, "Other",         "2026-07-10", "Miscellaneous"),
        (user_id, 120.00, "Food",          "2026-07-11", "Coffee"),
    ]
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        expenses,
    )

    conn.commit()
    conn.close()
