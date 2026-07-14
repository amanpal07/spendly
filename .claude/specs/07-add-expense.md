# Spec: Add Expense

## Overview
Add Expense implements the `/expenses/add` form that lets a logged-in user record a
new transaction in Spendly. It replaces the current placeholder stub (returning
"Add expense — coming in Step 7") with a real GET form and a POST handler that
inserts a row into the already-existing `expenses` table. This is the first of the
expense-CRUD steps and makes the data the profile/analytics pages already display
actually editable by the user rather than only seeded.

## Depends on
- **01 Database Setup** (`expenses` table, `get_db`, `init_db`, `seed_db`)
- **03 Login and Logout** (session-based auth used to scope expenses to a user)
- **04/05 Profile Page** (the page that will link here and shows the inserted data)

## Routes
- `GET /expenses/add` — render the add-expense form — access level: logged-in
- `POST /expenses/add` — validate and insert a new expense, then redirect — access level: logged-in

(Merge the existing `GET /expenses/add` placeholder into a single `methods=["GET", "POST"]` route, matching the `register`/`login` pattern already in `app.py`.)

## Database changes
No database changes. The `expenses` table in `database/db.py` already provides every
required column: `id`, `user_id`, `amount`, `category`, `date`, `description`,
`created_at`. Add Expense only inserts rows via parameterised `INSERT`.

## Templates
- **Create:** `templates/add_expense.html` — the add-expense form page (extends `base.html`).
  Fields: amount, category (dropdown), date (defaults to today), description (optional).
- **Modify:** `templates/base.html` — add an "Add expense" link in the logged-in nav
  block (next to Analytics / Log out), marked active on the `expenses.add` endpoint.
- **Modify:** `templates/profile.html` — add a "Add expense" call-to-action that links
  to `url_for('add_expense')`, so users can reach the form from their profile.

## Files to change
- `app.py` — replace the `add_expense` placeholder with a `GET`/`POST` handler that
  validates input, scopes the row to `session["user_id"]`, and inserts via `get_db()`.
- `templates/base.html` — add logged-in nav link to the add-expense page.
- `templates/profile.html` — add an "Add expense" CTA link.
- `static/css/style.css` — add scoped styles for the form (use existing CSS variables;
  reuse the form/input styles already used by `login.html`/`register.html`).

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use `database/db.py`'s `get_db()` directly.
- Parameterised queries only — never interpolate values into SQL strings.
- Passwords are hashed with werkzeug — N/A here (no auth form), but keep the habit; do
  not store plain text anywhere.
- Use CSS variables (`--ink`, `--paper`, `--accent`, `--radius-*`, etc.) — never
  hardcode hex values for core UI.
- All templates extend `base.html` and fill `{% block content %}`.
- Require `session.get("user_id")`; redirect to `login` if absent (match the `profile`
  and `analytics` guards).
- The category dropdown must use the same fixed set used by `seed_db`: Food, Transport,
  Bills, Health, Entertainment, Shopping, Other.
- Validate on the server: amount must be a positive number; category must be one of the
  allowed values; date must be a valid `YYYY-MM-DD` string; description is optional and
  length-bounded. Re-render the form with the user's input + an error message on failure
  (mirror the `register` route's re-render pattern).
- On success, `db.commit()` then `redirect(url_for("profile"))` (or `analytics`).
- Always `db.close()` in a `finally` block.

## Definition of done
- [ ] `GET /expenses/add` (logged in) renders `add_expense.html` with an amount field, a
      category dropdown containing exactly the 7 seeded categories, a date field
      defaulting to today, and an optional description field.
- [ ] Visiting `GET /expenses/add` while logged out redirects to `/login`.
- [ ] `POST /expenses/add` with valid data inserts exactly one row into `expenses` scoped
      to the logged-in `user_id`, then redirects to a page that lists it (profile/analytics).
- [ ] `POST /expenses/add` with an invalid amount (e.g. 0, negative, non-numeric) or an
      out-of-set category re-renders the form with an error and inserts no row.
- [ ] `POST /expenses/add` with a malformed date inserts no row and shows an error.
- [ ] The new expense appears on the profile/analytics page immediately after redirect.
- [ ] The base navbar shows an "Add expense" link when logged in, and the profile page
      shows a working "Add expense" CTA.
- [ ] `pytest` still passes and no new pip dependencies were added.
