# Spec: Date Filter for Profile Page

## Overview
Step 6 adds an optional date-range filter to the already-implemented profile
page. The current `/profile` route renders every expense for the logged-in
user — transaction history, summary stats, and category breakdown — with no
way to narrow the window. This step adds `from`/`to` date inputs on the page
that restrict all three sections to a chosen range (e.g. "this month" or a
custom span). The filter is read from the query string so the view is
bookmarkable and shareable, and it is applied consistently to every data
section so the stats and breakdown always match the visible transactions.

## Depends on
- Step 1: Database setup (`expenses.date` column exists, `get_db()` available)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 4: Profile page static UI (`templates/profile.html` renders all four sections)
- Step 5: Backend connection (`/profile` already queries real expenses)

## Routes
No new routes. The existing `GET /profile` route is modified to accept optional
query parameters:
- `GET /profile?start=YYYY-MM-DD&end=YYYY-MM-DD` — render the profile page with
  expenses filtered to the inclusive date range — logged-in only (redirect to
  `/login` if not authenticated). When `start`/`end` are absent or invalid, the
  route behaves exactly as today (all expenses shown).

## Database changes
No database changes. The `expenses` table already stores `date` as `TEXT` in
`YYYY-MM-DD` form, which sorts correctly under lexicographic comparison, so a
range filter needs only `date >= ? AND date <= ?`.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date-filter bar (a `GET` form) above the transaction-history section
    with two native `<input type="date">` fields named `start` and `end`, an
    "Apply" submit button, and a "Clear" link back to `/profile` (shown only
    when a filter is active). Pre-fill the inputs with the current `start`/`end`
    values so the selection persists across submits.
  - The four existing sections (user info, summary stats, transaction list,
    category breakdown) stay structurally the same; they simply receive the
    already-filtered data from the route.
  - Show an empty-state line ("No transactions found in the selected date
    range.") inside the transaction section when the filter yields zero rows.

## Files to change
- `app.py` — modify the `profile()` view function:
  - Read `request.args.get("start")` and `request.args.get("end")`.
  - Validate each against `^\d{4}-\d{2}-\d{2}$`; ignore any value that does not
    match (treat as unset).
  - Build a single `WHERE` clause (`user_id = ?` plus `AND date >= ?` /
    `AND date <= ?` when bounds are present) and reuse it for all three expense
    queries (transaction history, summary stats, category breakdown) so every
    section reflects the same range.
  - Pass `start` and `end` (or empty strings) into the template context.
  - Keep the existing auth guard (`session.get("user_id")` → redirect to
    `/login`) and the existing user-info query untouched.
- `templates/profile.html` — add the filter bar and empty state (see Templates).
- `static/css/style.css` — add filter-bar styles (inputs, labels, Apply button,
  Clear link, empty-state text) using only the existing theme tokens
  (`--paper-card`, `--border`, `--accent`, `--ink*`, `--radius-*`, etc.).

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`.
- Parameterised queries only. The `WHERE` clause *structure* may be assembled in
  Python, but every value (including the date bounds) must be passed as a `?`
  placeholder — never string-format user input into the SQL text.
- Validate `start`/`end` as `YYYY-MM-DD` before using them; reject malformed or
  empty values rather than letting them reach the query.
- Apply the same filter to all three expense queries (transactions, stats,
  category breakdown) so the displayed numbers stay internally consistent.
- The filter form must use `method="get"` (no POST, no new route); the "Clear"
  control is a plain link to `/profile`.
- Frontend is plain HTML + CSS only. Use native `<input type="date">`; no JS
  framework or date-picker library. A few lines of vanilla JS are permitted only
  if strictly needed (e.g. none required for the basic version).
- Use CSS variables — never hardcode hex values. Add new component styles to
  `static/css/style.css`, never inline.
- All templates extend `base.html`.
- Currency must always display as ₹.
- Preserve the auth guard: unauthenticated visits still redirect to `/login`.

## Tests to write

### Route tests
`GET /profile` — authenticated as seed user, no filter:
- Returns 200
- Shows all 8 seed transactions
- `total_spent` reflects the full unfiltered total

`GET /profile?start=2026-07-01&end=2026-07-05` — authenticated as seed user:
- Returns 200
- Transaction list contains only expenses dated 2026-07-01 through 2026-07-05
- `transaction_count` equals the number of expenses in that range
- `total_spent` equals the sum of expenses in that range
- Category breakdown totals sum to the same filtered `total_spent`

`GET /profile?start=2026-07-01&end=2026-07-31` — full month:
- Returns 200
- Shows all 8 seed transactions (all fall in July 2026)

`GET /profile?start=2020-01-01&end=2020-01-31` — range with no data:
- Returns 200
- Transaction list is empty
- `total_spent` is ₹0.00 and `transaction_count` is 0
- Empty-state message is shown

`GET /profile?start=not-a-date` — invalid input:
- Returns 200
- Invalid `start` is ignored; all expenses shown (same as no filter)

`GET /profile` — unauthenticated:
- Redirects to `/login` (302), regardless of any query params

## Definition of done
- [ ] The profile page shows a date-filter bar with `from` and `to` date inputs and an Apply button.
- [ ] Submitting a valid range narrows the transaction table to expenses within (and including) those dates.
- [ ] The summary stats (total spent, transaction count, top category) update to match the filtered range.
- [ ] The category breakdown updates to match the filtered range and its totals sum to the filtered total spent.
- [ ] The selected `from`/`to` values are preserved in the inputs after submitting.
- [ ] A "Clear" link resets the filter and shows all expenses again.
- [ ] An invalid or empty date value is ignored (no crash, full list shown).
- [ ] A range with no matching expenses shows an empty-state message and zeroed stats without error.
- [ ] Visiting `/profile` while logged out still redirects to `/login`.
- [ ] No hex colour values are hardcoded; the filter bar uses only CSS variables from `style.css`.
- [ ] All SQL uses parameterised `?` placeholders — no user input is string-formatted into the query.
