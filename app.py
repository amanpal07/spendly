import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-dev-key-change-in-production"  # dev-only; use env var in prod


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

    user = {
        "name": "Aanya Sharma",
        "initials": "AS",
        "email": "demo@spendly.com",
        "member_since": "July 2026",
    }
    stats = {
        "total_spent": 3981.45,
        "transaction_count": 8,
        "top_category": "Bills",
    }
    transactions = [
        {"date": "2026-07-11", "description": "Coffee", "category": "Food", "amount": 120.00},
        {"date": "2026-07-10", "description": "Miscellaneous", "category": "Other", "amount": 150.00},
        {"date": "2026-07-09", "description": "Groceries", "category": "Shopping", "amount": 890.20},
        {"date": "2026-07-07", "description": "Movie tickets", "category": "Entertainment", "amount": 600.00},
        {"date": "2026-07-05", "description": "Pharmacy", "category": "Health", "amount": 250.00},
        {"date": "2026-07-03", "description": "Electricity bill", "category": "Bills", "amount": 1450.75},
        {"date": "2026-07-02", "description": "Metro card recharge", "category": "Transport", "amount": 200.00},
        {"date": "2026-07-01", "description": "Lunch with friends", "category": "Food", "amount": 320.50},
    ]
    categories = [
        {"name": "Bills", "total": 1450.75, "percent": 100},
        {"name": "Shopping", "total": 890.20, "percent": 61},
        {"name": "Entertainment", "total": 600.00, "percent": 41},
        {"name": "Food", "total": 440.50, "percent": 30},
        {"name": "Health", "total": 250.00, "percent": 17},
        {"name": "Transport", "total": 200.00, "percent": 14},
        {"name": "Other", "total": 150.00, "percent": 10},
    ]
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


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
