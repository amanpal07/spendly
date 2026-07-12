"""Insert a single random Indian demo user into the users table.

Uses the project's get_db() helper so the connection/scoping matches db.py.
Regenerates the email until it is unique against the existing table.
"""

import random
import sys
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.db import get_db

FIRST_NAMES = [
    "Aarav", "Vihaan", "Krishna", "Reyansh", "Aditya", "Vivaan", "Arjun",
    "Sai", "Ananya", "Diya", "Pari", "Aadhya", "Ishaan", "Kabir", "Rohan",
    "Arnav", "Yash", "Dhruv", "Karthik", "Rahul", "Priya", "Neha", "Anjali",
    "Meera", "Saanvi", "Myra", "Sara", "Kiara", "Riya", "Ira",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Mehta", "Reddy", "Nair", "Iyer", "Patel",
    "Kumar", "Singh", "Joshi", "Bhat", "Das", "Banerjee", "Chatterjee",
    "Menon", "Pillai", "Rao", "Choudhary", "Kapoor", "Malhotra", "Bose",
    "Iyengar", "Deshmukh", "Kulkarni", "Hegde", "Shetty", "Nair", "Thomas",
    "George",
]


def make_user():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    suffix = random.randint(10, 999)
    email = f"{first.lower()}.{last.lower()}{suffix}@gmail.com"
    return first + " " + last, email


def main():
    conn = get_db()
    try:
        while True:
            name, email = make_user()
            exists = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if not exists:
                break

        password_hash = generate_password_hash("password123")
        created_at = datetime.now().isoformat(timespec="seconds")

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) "
            "VALUES (?, ?, ?, ?)",
            (name, email, password_hash, created_at),
        )
        conn.commit()
        user_id = cur.lastrowid

        print("User created successfully:")
        print(f"  id:   {user_id}")
        print(f"  name: {name}")
        print(f"  email: {email}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
