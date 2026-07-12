# Spec: Registration

## Overview
This step implements user self-registration for Spendly. The `/register`
route currently only serves `GET` (rendering `register.html`), while the
form posts to `POST /register` with no handler — submitting it returns a
405 today. This step wires up that POST handler: validate the submitted
name/email/password, reject duplicates and weak input, hash the password
with werkzeug, persist the row in the already-existing `users` table, and
redirect the new user to the sign-in page on success. It is the first
piece of real authentication and depends on the data layer from Step 1.

## Depends on
- **Step 1 — Database Setup** (`01-database-setup.md`): the `users`
  table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`)
  already exists and `get_db()` / `init_db()` / `seed_db()` are implemented.
  `werkzeug.security.generate_password_hash` is installed.

## Routes
- `POST /register` — accept `name`, `email`, `password`; validate,
  hash, insert, and redirect to `/login` on success — **public**
  (the existing `GET /register` route is extended to also accept POST;
  no new path is introduced)

## Database changes
No database changes. The `users` table required by this step already
exists in `database/db.py` with the necessary `email` UNIQUE constraint.

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — it already renders an
  `{% if error %}` block. On a failed POST it must be re-rendered with
  `error` set and the previously entered `name`/`email` echoed back into
  the inputs so the user does not lose their typing. No structural change
  to the markup is required beyond binding those values.

## Files to change
- `app.py` — extend the `/register` view to handle `POST`: parse form
  fields, validate, insert via `get_db()`, and redirect on success.
- `templates/register.html` — bind returned `name`/`email` values into
  the inputs so they survive a validation error.

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug` is already pinned in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs — use the `get_db()` helper directly.
- Parameterised queries only (`?` placeholders) — never string-format SQL.
- Passwords hashed with `werkzeug.security.generate_password_hash`.
- Use CSS variables for any markup/styling tweaks — never hardcode hex
  values (the theme tokens live in `static/css/style.css`).
- All templates extend `base.html` (already true for `register.html`).
- Enforce the same password minimum the UI promises: **≥ 8 characters**.
- Validate that `name` and `email` are non-empty and that `email` is
  plausibly an email address before touching the database.
- Normalise the email with `.lower()` after stripping (before the UNIQUE
  check) so `Foo@Bar.com` and `foo@bar.com` resolve to the same identity.
  SQLite's UNIQUE on TEXT is case-sensitive, so an un-normalised email would
  let near-duplicate accounts slip through and break later login matching.
- Catch the `email` UNIQUE violation and surface a friendly "that email is
  already registered" error rather than a 500.
- On success, `redirect` to `/login` (do **not** auto-log-in; there is
  no session layer yet and login remains a stub).

## Definition of done
- [ ] `GET /register` still renders `register.html`.
- [ ] Submitting valid name/email/password creates a `users` row whose
      `password_hash` is a werkzeug hash (never plaintext).
- [ ] After a successful registration the browser is redirected to `/login`.
- [ ] Submitting an email already in the `users` table shows an error and
      inserts no row.
- [ ] Submitting a password shorter than 8 characters shows an error.
- [ ] Submitting an empty name or empty/invalid email shows an error.
- [ ] On any validation error the entered `name`/`email` are preserved in
      the re-rendered form.
- [ ] Registering an email that differs from an existing one only by case
      (e.g. `Test@Example.com` vs `test@example.com`) is rejected as a
      duplicate.
- [ ] All database access uses parameterised queries.
- [ ] `pytest` still passes (no regressions).
