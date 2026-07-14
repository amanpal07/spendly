import math
import os
import re
import sqlite3
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

CATEGORIES = (
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other",
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

app = Flask(__name__)
# Dev-only default; set SPENDLLY_SECRET_KEY (a random value) in any real deployment.
app.secret_key = os.environ.get("SPENDLLY_SECRET_KEY", "spendly-dev-key-change-in-production")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name:
        return render_template(
            "register.html", error="Name is required.", name=name, email=email
        )
    if not email:
        return render_template(
            "register.html", error="Email is required.", name=name, email=email
        )
    if "@" not in email:
        return render_template(
            "register.html",
            error="Please enter a valid email address.",
            name=name,
            email=email,
        )
    if len(password) < 8:
        return render_template(
            "register.html",
            error="Password must be at least 8 characters.",
            name=name,
            email=email,
        )

    password_hash = generate_password_hash(password)

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return render_template(
            "register.html",
            error="That email is already registered.",
            name=name,
            email=email,
        )
    finally:
        db.close()

    return redirect(url_for("login"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    db = get_db()
    user = db.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    db.close()

    GENERIC_ERROR = "Invalid email or password."
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error=GENERIC_ERROR, email=email)

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/debug")
def debug():
    """Dev-only live view of the database. Not for production use."""
    db = get_db()
    users = [
        dict(r)
        for r in db.execute(
            "SELECT id, name, email, created_at FROM users ORDER BY id"
        ).fetchall()
    ]
    expenses = [
        dict(r)
        for r in db.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses ORDER BY id"
        ).fetchall()
    ]
    db.close()
    return render_template("debug.html", users=users, expenses=expenses)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Months offered in the dropdown: the current month plus the previous 11.
    # An empty value means "All time".
    now = datetime.now()
    months = []
    y, m = now.year, now.month
    for _ in range(12):
        months.append({"value": f"{y}-{m:02d}", "label": f"{MONTH_NAMES[m - 1]} {y}"})
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    # Parse the optional filter. A chosen month takes precedence and is expanded
    # to that month's first/last day; otherwise the explicit from/to bounds are
    # used. All values are validated as YYYY-MM-DD so the lexicographic date
    # comparison below stays correct; invalid/empty values are ignored.
    DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    selected_month = request.args.get("month", "").strip()
    if MONTH_RE.match(selected_month):
        my, mm = int(selected_month[:4]), int(selected_month[5:7])
        if 1 <= mm <= 12:
            start = f"{my}-{mm:02d}-01"
            # Last day of the month via datetime arithmetic (no string formatting,
            # so an out-of-range month can never produce an invalid date string).
            nxt = datetime(my + 1, 1, 1) if mm == 12 else datetime(my, mm + 1, 1)
            end = (nxt - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            selected_month = ""
    else:
        selected_month = ""

    start = start if DATE_RE.match(start) else ""
    end = end if DATE_RE.match(end) else ""

    where = "user_id = ?"
    params = [user_id]
    if start:
        where += " AND date >= ?"
        params.append(start)
    if end:
        where += " AND date <= ?"
        params.append(end)

    db = get_db()
    try:
        # SECTION: user-info (orchestrator)
        user_row = db.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user_row is None:
            session.clear()
            return redirect(url_for("login"))
        name = user_row["name"]
        created = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S")
        user = {
            "name": name,
            "email": user_row["email"],
            "initials": "".join(p[0].upper() for p in name.split()[:2]) or name[:2].upper(),
            "member_since": created.strftime("%B %Y"),
        }

        # === SECTION START: transaction-history (subagent 1) ===
        rows = db.execute(
            f"SELECT date, description, category, amount "
            f"FROM expenses WHERE {where} ORDER BY date DESC, id DESC",
            params,
        ).fetchall()
        transactions = [
            {
                "date": r["date"],
                "description": r["description"],
                "category": r["category"],
                "amount": r["amount"],
            }
            for r in rows
        ]
        # === SECTION END: transaction-history ===

        # === SECTION START: summary-stats (subagent 2) ===
        totals_row = db.execute(
            f"SELECT COALESCE(SUM(amount), 0) AS total_spent, "
            f"COUNT(*) AS transaction_count FROM expenses WHERE {where}",
            params,
        ).fetchone()
        total_spent = float(totals_row["total_spent"])
        transaction_count = int(totals_row["transaction_count"])

        cat_rows = db.execute(
            f"SELECT category, SUM(amount) AS total FROM expenses "
            f"WHERE {where} GROUP BY category",
            params,
        ).fetchall()
        top_category = ""
        if cat_rows:
            top_category = max(cat_rows, key=lambda r: r["total"])["category"]

        stats = {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
        # === SECTION END: summary-stats ===

        # === SECTION START: category-breakdown (subagent 3) ===
        cat_totals = db.execute(
            f"SELECT category, SUM(amount) AS total FROM expenses "
            f"WHERE {where} GROUP BY category",
            params,
        ).fetchall()
        categories = []
        if cat_totals:
            max_total = max(r["total"] for r in cat_totals)
            if max_total > 0:
                categories = [
                    {
                        "name": r["category"],
                        "total": float(r["total"]),
                        "percent": round(r["total"] / max_total * 100),
                        "share": round(r["total"] / total_spent * 100) if total_spent else 0,
                    }
                    for r in sorted(cat_totals, key=lambda r: r["total"], reverse=True)
                ]
        # === SECTION END: category-breakdown ===
    finally:
        db.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        start=start,
        end=end,
        months=months,
        selected_month=selected_month,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        today = datetime.now().strftime("%Y-%m-%d")
        return render_template(
            "add_expense.html",
            categories=CATEGORIES,
            date=today,
            amount="",
            category="",
            description="",
        )

    # --- POST: extract and trim form fields ---
    raw_amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()[:200]

    def fail(msg):
        return render_template(
            "add_expense.html",
            error=msg,
            categories=CATEGORIES,
            amount=raw_amount,
            category=category,
            date=date,
            description=description,
        )

    # --- Validate amount ---
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        return fail("Please enter a valid amount.")
    if not math.isfinite(amount) or amount <= 0:
        return fail("Amount must be a positive number.")

    # --- Validate category ---
    if category not in CATEGORIES:
        return fail("Please select a valid category.")

    # --- Validate date (format + real calendar date) ---
    if not DATE_RE.match(date):
        return fail("Please enter a valid date (YYYY-MM-DD).")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return fail("Please enter a valid date.")

    # --- Insert, scoped to the logged-in user ---
    db = get_db()
    try:
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], round(amount, 2), category, date, description or None),
        )
        db.commit()
    finally:
        db.close()

    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
