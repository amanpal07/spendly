"""Seed <count> random expenses for <user_id> across the past <months> months.

Usage: python scripts/seed_expenses.py <user_id> <count> <months>

- Uses the project's get_db() helper (no hardcoded db filename).
- Parameterised queries only.
- All inserts run inside one transaction; rolls back on any failure.
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.db import get_db

# Category -> (min_amount, max_amount, weight, sample descriptions).
# Weights make Food most common and Health/Entertainment least common.
CATEGORIES = {
    "Food": (50, 800, 30, [
        "Lunch at local dhaba", "Chai and samosa", "Swiggy order",
        "Dinner at Udupi", "Vegetables from market", "Biryani takeaway",
    ]),
    "Transport": (20, 500, 18, [
        "Metro recharge", "Auto rickshaw", "Ola ride",
        "Bus pass", "Fuel top-up",
    ]),
    "Shopping": (200, 5000, 14, [
        "Groceries at DMart", "New clothes", "Amazon order",
        "Shoes", "Diwali gifts",
    ]),
    "Bills": (200, 3000, 12, [
        "Electricity bill", "Mobile recharge", "Broadband bill",
        "Water bill", "Gas cylinder",
    ]),
    "Other": (50, 1000, 12, [
        "Miscellaneous", "Birthday gift", "Stationery",
        "Donation", "Pet supplies",
    ]),
    "Health": (100, 2000, 7, [
        "Pharmacy", "Doctor consultation", "Lab test",
        "Physiotherapy",
    ]),
    "Entertainment": (100, 1500, 7, [
        "Movie tickets", "Netflix subscription", "Concert",
        "Bowling", "Weekend getaway",
    ]),
}


def first_day_n_months_ago(today, n):
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def build_expenses(user_id, count, months):
    today = date.today()
    start = first_day_n_months_ago(today, months)
    span_days = (today - start).days

    cats = list(CATEGORIES.keys())
    weights = [CATEGORIES[c][2] for c in cats]

    rows = []
    for _ in range(count):
        category = random.choices(cats, weights=weights, k=1)[0]
        lo, hi, _, descs = CATEGORIES[category]
        amount = round(random.uniform(lo, hi), 2)
        description = random.choice(descs)
        # Random date in [start, today].
        offset = random.randint(0, span_days)
        exp_date = start + timedelta(days=offset)
        rows.append((user_id, amount, category, exp_date.isoformat(), description))
    return rows


def main():
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            print(f"No user found with id {user_id}.")
            return

        rows = build_expenses(user_id, count, months)
        min_date = min(r[3] for r in rows)
        max_date = max(r[3] for r in rows)

        try:
            inserted_ids = []
            for row in rows:
                cur = conn.execute(
                    """
                    INSERT INTO expenses
                        (user_id, amount, category, date, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    row,
                )
                inserted_ids.append(cur.lastrowid)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Fetch a sample of up to 5 inserted records (parameterised IN list).
        placeholders = ",".join("?" * len(inserted_ids))
        sample = conn.execute(
            f"""
            SELECT id, amount, category, date, description
            FROM expenses
            WHERE id IN ({placeholders})
            ORDER BY id
            LIMIT 5
            """,
            inserted_ids,
        ).fetchall()

        print(f"Inserted {len(rows)} expense(s) for user {user_id}.")
        print(f"Date range spanned: {min_date} to {max_date}")
        print("Sample of inserted records:")
        for r in sample:
            print(
                f"  id={r['id']} | ₹{r['amount']:.2f} | "
                f"{r['category']} | {r['date']} | {r['description']}"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
