<p align="center">
  <img src="static/banner.png" alt="Spendly — Minimalist Personal Expense Tracker" width="100%">
</p>

<h1 align="center">Spendly</h1>

<p align="center">
  <strong>Track every rupee. Know where it goes.</strong><br>
  A clean, minimalist personal expense tracker built with Flask &amp; SQLite.
</p>

<p align="center">
  <a href="https://expense-tracker-production-ed4c.up.railway.app/"><img src="https://img.shields.io/badge/🚀%20Live%20Demo-Visit%20Spendly-brightgreen?style=for-the-badge" alt="Live Demo"></a>
  <br><br>
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/flask-3.x-black?logo=flask&logoColor=white" alt="Flask 3.x">
  <img src="https://img.shields.io/badge/database-SQLite-07405e?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/deployed%20on-Railway-blueviolet?logo=railway&logoColor=white" alt="Railway">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/currency-₹%20INR-orange" alt="Currency INR">
</p>

---

## 🌐 Live Demo

**👉 [expense-tracker-production-ed4c.up.railway.app](https://expense-tracker-production-ed4c.up.railway.app/)**

Use the demo account to explore instantly:
- **Email:** `demo@spendly.com`
- **Password:** `demo123`

---

## ✨ Features

| Feature | Description |
|---|---|
| **🔐 User Authentication** | Secure registration & login with hashed passwords (Werkzeug) |
| **💸 Full CRUD Expenses** | Add, edit, and delete expenses with validation |
| **📊 Dashboard Profile** | Summary stats, category breakdowns, and transaction history |
| **📅 Date Filtering** | Filter expenses by month or custom date range |
| **🏷️ Category Tracking** | 7 built-in categories — Food, Transport, Bills, Health, Entertainment, Shopping, Other |
| **📈 Analytics** | Coming Soon — Advanced analytics dashboard |
| **🎨 Premium UI** | Dark-mode-ready design with DM Serif Display & DM Sans typography |
| **🧪 Tested** | Comprehensive test suite with pytest & pytest-flask |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.13 · Flask 3.x
- **Templating:** Jinja2 (all pages extend `base.html`)
- **Frontend:** Vanilla HTML/CSS/JS — no frameworks, no jQuery
- **Database:** SQLite via `database/db.py`
- **Auth:** Werkzeug password hashing
- **Testing:** pytest + pytest-flask
- **Deployment:** Gunicorn (Procfile included)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/amanpal07/spendly.git
cd spendly

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app will be running at **http://127.0.0.1:5001** 🎉

### Demo Account

A demo account is automatically seeded on first run:

| Field | Value |
|---|---|
| **Email** | `demo@spendly.com` |
| **Password** | `demo123` |

> [!NOTE]
> The demo user comes with 8 sample transactions pre-loaded so you can explore the dashboard immediately.

---

## 📁 Project Structure

```
spendly/
├── app.py                  # Flask app — all routes defined here
├── database/
│   └── db.py               # DB helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html            # Shared layout (navbar + footer)
│   ├── landing.html         # Hero landing page
│   ├── login.html           # Login form
│   ├── register.html        # Registration form
│   ├── profile.html         # Dashboard with stats & transactions
│   ├── add_expense.html     # Add expense form
│   ├── edit_expense.html    # Edit expense form
│   ├── analytics.html       # Coming Soon page
│   ├── terms.html           # Terms & Conditions
│   └── privacy.html         # Privacy Policy
├── static/
│   ├── css/style.css        # Global theme with CSS custom properties
│   └── js/main.js           # Client-side JavaScript
├── tests/                   # pytest test suite
├── requirements.txt         # Pinned dependencies
├── Procfile                 # Gunicorn config for deployment
└── CLAUDE.md                # AI pair-programming context
```

---

## 🗺️ Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/register` | GET, POST | User registration |
| `/login` | GET, POST | User login |
| `/logout` | GET | Clear session & redirect |
| `/profile` | GET | Dashboard — stats, transactions, filters |
| `/expenses/add` | GET, POST | Add a new expense |
| `/expenses/<id>/edit` | GET, POST | Edit an existing expense |
| `/expenses/<id>/delete` | POST | Delete an expense (with confirmation) |
| `/analytics` | GET | Coming Soon page |
| `/terms` | GET | Terms & Conditions |
| `/privacy` | GET | Privacy Policy |

---

## 🧪 Running Tests

```bash
source venv/bin/activate
pytest
```

The test suite covers authentication, CRUD operations, date filtering, and ownership scoping.

---

## 🎨 Design System

Spendly uses a CSS custom property-based theme defined in `static/css/style.css`:

- **Fonts:** DM Serif Display (headings) + DM Sans (body) via Google Fonts
- **Colors:** CSS variables (`--ink`, `--paper`, `--accent`, etc.)
- **Radius:** Consistent border-radius tokens (`--radius-sm`, `--radius-md`, `--radius-lg`)
- **Currency:** Indian Rupees (₹) throughout the UI

---

## 🚢 Deployment

Spendly includes a `Procfile` for easy deployment to platforms like Railway or Heroku:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

**Environment variables:**

| Variable | Description | Default |
|---|---|---|
| `SPENDLLY_SECRET_KEY` | Flask session secret key | Dev fallback (change in prod!) |
| `SPENDLLY_DB` | SQLite database file path | `expense_tracker.db` |
| `PORT` | Server port | `5001` |

> [!WARNING]
> Always set a unique `SPENDLLY_SECRET_KEY` in production. The default value is for development only.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ and ₹ tracking in mind
</p>
