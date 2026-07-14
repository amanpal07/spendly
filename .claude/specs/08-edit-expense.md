# Spec: Edit Expense

## Overview
Edit Expense implements the `/expenses/<id>/edit` form that lets a logged-in user
change the amount, category, date, or description of one of their existing
transactions in Spendly. It replaces the current placeholder stub (returning
"Edit expense — coming in Step 8") with a real GET form pre-filled from the row
and a POST handler that updates it. This is the second of the expense-CRUD steps
and reuses the validation patterns established by Add Expense (Step 7); it makes
the data the profile page already displays actually correctable by the user.

## Depends on
- **01 Database Setup** (`expenses` table, `get_db`, `init_db`, `seed_db`)
- **03 Login and Logout** (session-based auth used to scope and guard the edit)
- **04/05 Profile Page** (the page that links here and shows the edited data)
- **07 Add Expense** (validation rules + form styling this route mirrors)

## Routes
- `GET /expenses/<int:id>/edit` — load the expense and render the edit form
  pre-filled with its current values — access level: logged-in
- `POST /expenses/<int:id>/edit` — validate and UPDATE the expense, then redirect
  — access level: logged-in

(Replace the existing GET-only `edit_expense` placeholder with a single
`methods=["GET", "POST"]` route, matching the `add_expense`/`register`/`login`
pattern already in `app.py`.)

## Database changes
No database changes. The `expenses` table in `database/db.py` already provides
every required column: `id`, `user_id`, `amount`, `category`, `date`,
`description`, `created_at`. Edit Expense only reads one row (by `id`) and updates
the editable columns via a parameterised `UPDATE`.

## Templates
- **Create:** `templates/edit_expense.html` — the edit-expense form page
  (extends `base.html`). Fields mirror `add_expense.html`: amount, category
  (dropdown), date, description (optional), plus a "Cancel" link back to the
  profile. The form action posts to `url_for('edit_expense', id=expense.id)`.
- **Modify:** `templates/profile.html` — add an "Edit" link per transaction in the
  transaction-history list pointing to `url_for('edit_expense', id=t.id)`, so users
  can reach the form from their profile. Link only shows for the logged-in user's
  own expenses (the profile query is already scoped to `user_id`).

## Files to change
- `app.py` — replace the `edit_expense` placeholder with a `GET`/`POST` handler that:
  - guards with `session.get("user_id")` (redirect to `login` if absent);
  - on `GET`, loads the expense by `id` **scoped to the logged-in `user_id`** and
    renders the form pre-filled; if no row is found, redirect to `profile`;
  - on `POST`, re-validates exactly like `add_expense`, and on success runs a
    parameterised `UPDATE ... WHERE id = ? AND user_id = ?`, commits, and
    redirects to `profile`.
- `templates/profile.html` — add an "Edit" link per transaction row.
- `static/css/style.css` — reuses the existing form/input styles (no new design
  tokens needed); add only layout tweaks to the edit form if required (still use
  CSS variables, never hardcode hex).

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use `database/db.py`'s `get_db()` directly.
- Parameterised queries only — never interpolate values into SQL strings. The
  `UPDATE` must bind both `id` and `user_id` so one user can never edit another's
  expenses.
- Passwords are hashed with werkzeug — N/A here, but keep the habit; do not store
  plain text anywhere.
- Use CSS variables (`--ink`, `--paper`, `--accent`, `--radius-*`, etc.) — never
  hardcode hex values for core UI.
- All templates extend `base.html` and fill `{% block content %}`.
- Require `session.get("user_id")`; redirect to `login` if absent (match the
  `profile`/`analytics`/`add_expense` guards).
- Ownership enforcement is mandatory: every DB lookup/update for the expense must
  include `user_id = ?` bound to `session["user_id"]`. If the `WHERE id = ? AND
  user_id = ?` lookup returns no row, redirect to `profile` (don't 404 leak).
- The category dropdown must use the same fixed set used by `seed_db` (also defined
  as `CATEGORIES` in `app.py`): Food, Transport, Bills, Health, Entertainment,
  Shopping, Other. The current category must be marked `selected`.
- Validate on the server, mirroring `add_expense`: amount must be a positive finite
  number; category must be one of the allowed values; date must be a valid
  `YYYY-MM-DD` string; description optional, length-bounded to 200 chars. Re-render
  the form with the user's input + an error message on failure.
- On success, `db.commit()` then `redirect(url_for("profile"))`.
- Always `db.close()` in a `finally` block.
- Pre-fill every field on `GET` from the loaded row (amount rounded to 2 dp,
  category, date, description) so the user sees current values.

## Definition of done
- [ ] `GET /expenses/<int:id>/edit` (logged in) renders `edit_expense.html` with all
      fields pre-filled from the existing expense, including the correct category
      `selected` in the dropdown (exactly the 7 seeded categories present).
- [ ] Visiting `GET /expenses/<int:id>/edit` while logged out redirects to `/login`.
- [ ] `POST /expenses/<int:id>/edit` with valid data updates exactly that one row
      (scoped to the logged-in `user_id`) and then redirects to `/profile`.
- [ ] `POST` with an invalid amount (0, negative, non-numeric) or an out-of-set
      category re-renders the form with an error and changes no rows.
- [ ] `POST` with a malformed date changes no rows and shows an error.
- [ ] The edited values appear on the profile page immediately after redirect, and
      no other expense row is affected.
- [ ] A user cannot edit another user's expense: a row whose `user_id` differs from
      the session returns no match and redirects to `/profile` (no update occurs).
- [ ] The profile transaction list shows a working "Edit" link per expense.
- [ ] `pytest` still passes and no new pip dependencies were added.
