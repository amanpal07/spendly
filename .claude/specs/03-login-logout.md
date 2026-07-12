# Spec: Login and Logout

## Overview
This step introduces real sign-in / sign-out to Spendly. The `/login` route
today only serves `GET` (`login.html`), while the rendered form posts to
`POST /login` with no handler — submitting it returns a 405. The `/logout`
route is a placeholder stub that returns a "coming in Step 3" string. This
step wires up the session layer that Step 2 deliberately deferred: it verifies
a submitted email/password against the existing `users` table (password
checked with werkzeug's `check_password_hash`), establishes a Flask session
on success, and clears it on logout. It closes the registration loop started in
Step 2, letting a newly registered user actually sign in.

## Depends on
- **Step 1 — Database Setup** (`01-database-setup.md`): the `users` table
  (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`) exists and
  `get_db()` / `init_db()` / `seed_db()` are implemented.
- **Step 2 — Registration** (`02-registration.md`): users are persisted with a
  werkzeug `password_hash` and the `email` is normalised with `.lower()`. The
  `/login` template already posts to `POST /login`, so this step only needs to
  add the handler.

## Routes
- `POST /login` — accept `email`, `password`; verify against `users`; set the
  session and redirect to the landing page (`/`) on success — **public**
  (the existing `GET /login` route is extended to also accept POST; no new
  path is introduced)
- `GET /logout` — clear the session and redirect to `/login` — **public**
  (replaces the existing `GET /logout` placeholder stub; the path already
  exists, only its behaviour changes)

## Database changes
No database changes. Login reads from the existing `users` table by `email`
and checks the stored `password_hash`. No new columns or tables are required.

## Templates
- **Create:** none
- **Modify:** `templates/login.html` — it already renders an `{% if error %}`
  block and posts to `/login`. On a failed POST it must be re-rendered with
  `error` set and the previously entered `email` echoed back into the input so
  the user does not lose their typing. No structural markup change is required
  beyond binding the returned `email` value into the email input.

## Files to change
- `app.py` — (1) set `app.secret_key` so the session layer works; (2) import
  `session` from `flask` and `check_password_hash` from `werkzeug.security`;
  (3) extend the `/login` view to handle `POST`: look up the user by normalised
  `email`, verify the password, set `session["user_id"]` and
  `session["user_name"]` on success and `redirect` to `/`, otherwise re-render
  `login.html` with an `error`; (4) replace the `/logout` placeholder with a
  real handler that clears the session and redirects to `/login`.

## Files to create
None.

## New dependencies
No new dependencies. `flask` (for `session`) and `werkzeug`
(for `check_password_hash`) are already pinned in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs — use the `get_db()` helper directly.
- Parameterised queries only (`?` placeholders) — never string-format SQL.
- Verify passwords with `werkzeug.security.check_password_hash` against the
  stored `password_hash`; never compare plaintext.
- Use a Flask `session` to track the signed-in user. Set `app.secret_key`
  (a dev key is acceptable for this learning project, but it must be set so
  sessions sign/verify correctly).
- Normalise the submitted email with `.lower()` after stripping before the
  lookup, matching the normalisation applied during registration so
  `Foo@Bar.com` and `foo@bar.com` resolve to the same account.
- Use a single generic error message for invalid credentials (e.g. "Invalid
  email or password.") so the response does not reveal whether the email
  exists — do not distinguish "no such user" from "wrong password".
- Use CSS variables for any markup/styling tweaks — never hardcode hex values
  (the theme tokens live in `static/css/style.css`).
- All templates extend `base.html` (already true for `login.html`).
- On logout, call `session.clear()` (or `pop` the keys) and redirect to
  `/login`; do not leave stale session data behind.

## Definition of done
- [ ] `GET /login` still renders `login.html`.
- [ ] Submitting the correct email + password for a registered user signs them
      in (a session is created) and redirects to `/`.
- [ ] The seeded demo user (`demo@spendly.com` / `demo123`) can sign in.
- [ ] Submitting a wrong password shows the generic "Invalid email or password."
      error and creates no session.
- [ ] Submitting an email not in the `users` table shows the same generic error.
- [ ] Signing in with an email that differs from a stored one only by case
      (e.g. `Demo@Spendly.com`) succeeds and matches the lowercased account.
- [ ] On a failed login the entered `email` is preserved in the re-rendered
      form.
- [ ] `GET /logout` clears the session and redirects to `/login`.
- [ ] After logout, the session no longer identifies a user.
- [ ] All database access uses parameterised queries; no plaintext password
      is ever compared.
- [ ] `pytest` still passes (no regressions).
