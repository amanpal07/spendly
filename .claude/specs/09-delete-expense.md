# Spec: Delete Expense

## Overview
Delete Expense replaces the current `/expenses/<int:id>/delete` placeholder stub
(returning "Delete expense — coming in Step 9") with a real, ownership-scoped
delete action. It is the final piece of the expense-CRUD trio (after Add, Step 7,
and Edit, Step 8) and lets a logged-in user remove one of their own transactions
from the profile page. Deletion is triggered by a per-row "Delete" button that
opens a hand-written vanilla-JS confirmation modal; on confirm, the browser posts
to the delete route, which removes exactly that one row (scoped to the logged-in
user) and redirects back to the profile. This keeps destructive actions out of
GET requests and reuses the modal pattern already established on the landing page.

## Depends on
- **01 Database Setup** (`expenses` table, `get_db`, `init_db`, `seed_db`)
- **03 Login and Logout** (session-based auth used to scope and guard the delete)
- **04/05 Profile Page** (the page that hosts the delete button + confirmation)
- **07 Add Expense** & **08 Edit Expense** (ownership + validation patterns this
  route mirrors; edit already added the per-row "Edit" action in the same column)
- **Vanilla-JS modal pattern** from the landing page YouTube modal (CLAUDE.md:
  modals must be hand-written vanilla JS, never a library)

## Routes
- `POST /expenses/<int:id>/delete` — delete the expense with `id` **scoped to the
  logged-in `user_id`**, then redirect to the profile — access level: logged-in.

(Replace the existing GET-only `delete_expense` placeholder with a `POST`-only
route. A destructive action must NOT live on GET. The confirm step happens in the
client-side vanilla-JS modal before the POST is issued.)

## Database changes
No database changes. The `expenses` table in `database/db.py` already has every
required column (`id`, `user_id`, `amount`, `category`, `date`, `description`).
Delete Expense only removes one row via a parameterised `DELETE WHERE id = ? AND
user_id = ?`. Note `init_db()` enables `PRAGMA foreign_keys = ON`, so a deleting
user (parent `users` row) is unaffected; the expense is simply removed.

## Templates
- **Modify:** `templates/profile.html`
  - Add a "Delete" button/link per transaction row in the existing `Actions`
    column (next to the "Edit" link at `profile.html:94`), carrying the expense
    `id` (e.g. `data-id="{{ t.id }}"`).
  - Add a single vanilla-JS confirmation modal markup block (hidden by default)
    near the end of the content block: a backdrop + a dialog with the expense
    summary text, a "Cancel" button, and a "Delete" confirm button. Mirrors the
    landing-page YouTube modal structure (open on trigger, close on button or
    backdrop click). The modal is shared across all rows — it is populated with
    the clicked row's id at click time.
- **No new template files created** — modal markup lives inside `profile.html`
  and the global modal logic in `main.js` (see Files to change), keeping scope
  tight to the profile page.

## Files to change
- `app.py` — replace the `delete_expense` GET stub (lines 492-494) with a
  `POST`-only handler that:
  - guards with `session.get("user_id")`; redirect to `login` if absent (match the
    `add_expense`/`edit_expense` guards);
  - runs a parameterised `DELETE FROM expenses WHERE id = ? AND user_id = ?` bound
    to `(id, session["user_id"])`; commits; `db.close()` in a `finally`;
  - redirects back to the profile. Preserve the active date filter if present by
    carrying the incoming `start`/`end`/`month` query args (read from
    `request.args`) onto the redirect, matching how a user landed on that filtered
    view. If no row matches (wrong id or not owned by this user) just redirect to
    the profile — do not 404-leak.
- `templates/profile.html` — add the per-row Delete trigger and the confirmation
  modal markup (see Templates above).
- `static/css/style.css` — reuse the existing modal/button styles where possible;
  add only the delete-specific tweaks (danger button, modal layout) using CSS
  variables (`--ink`, `--paper`, `--accent`, `--danger*` if present, `--radius-*`)
  — never hardcode hex values.
- `static/js/main.js` — add the profile delete-modal behaviour: open the modal on
  a row's Delete trigger, capture that row's expense id, close on Cancel/backdrop
  click, and on confirm issue a `POST` to `/expenses/<id>/delete` (e.g. submit a
  hidden form or `fetch`) carrying the current filter query string so the redirect
  lands back on the same filtered view. Follow the landing-page modal's open/close
  + backdrop-click conventions; no libraries.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use `database/db.py`'s `get_db()` directly.
- Parameterised queries only — never interpolate values into SQL. The `DELETE`
  must bind both `id` and `user_id` so one user can never delete another's
  expenses.
- Passwords hashed with werkzeug — N/A here; keep the habit, store nothing in
  plain text.
- Use CSS variables (`--ink`, `--paper`, `--accent`, `--radius-*`, etc.) — never
  hardcode hex values for core UI.
- All templates extend `base.html` and fill `{% block content %}`.
- Require `session.get("user_id")`; redirect to `login` if absent (match the
  `profile`/`add_expense`/`edit_expense` guards).
- **Destructive action on POST only.** No `GET` delete. The confirmation happens
  in the vanilla-JS modal before the POST is sent. This is a deliberate security
  and correctness rule (GET requests can be prefetched/crawled and must stay
  non-destructive).
- Ownership enforcement is mandatory: every DB delete must include
  `user_id = ?` bound to `session["user_id"]`. If `WHERE id = ? AND user_id = ?`
  removes 0 rows (id missing or owned by another user), still redirect to
  `profile` (don't 404-leak existence).
- Always `db.close()` in a `finally` block; `db.commit()` only on a successful
  delete.
- After deletion, redirect to `url_for("profile")` and preserve the active
  `start`/`end`/`month` filter args so the user returns to the same filtered
  list they were viewing.
- The confirmation modal must be hand-written vanilla JS (no library), reusing the
  landing-page modal conventions: opened by a trigger click, closed by the
  Cancel button or a backdrop click, and it must not leave a stray click handler
  that deletes the wrong row.

## Definition of done
- [ ] `POST /expenses/<int:id>/delete` (logged in) removes exactly that one row
      scoped to the logged-in `user_id`, commits, and redirects to `/profile`
      (preserving the active date filter if any).
- [ ] Visiting `POST /expenses/<int:id>/delete` while logged out redirects to
      `/login` and deletes nothing.
- [ ] `GET /expenses/<int:id>/delete` no longer performs a delete (it is either
      removed or returns a safe redirect to `profile` with no DB change).
- [ ] A user cannot delete another user's expense: a row whose `user_id` differs
      from the session removes 0 rows and just redirects to `/profile`.
- [ ] The profile transaction list shows a working "Delete" trigger per expense,
      next to the existing "Edit" link in the Actions column.
- [ ] Clicking Delete opens a vanilla-JS confirmation modal; clicking Cancel or the
      backdrop closes it without deleting anything.
- [ ] Confirming in the modal sends a `POST` to `/expenses/<id>/delete` and the row
      disappears from the profile list after the redirect.
- [ ] No other expense row is affected by a delete, and the summary stats /
      category breakdown on the profile recompute correctly afterwards.
- [ ] The modal and delete button use only CSS variables — no hardcoded hex values.
- [ ] `pytest` still passes and no new pip dependencies were added.
