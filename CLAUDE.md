# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview

**Spendly** (formerly "Jeb-Kharch") — a personal expense tracking web app
built with Flask. Users log expenses, view category breakdowns, and track
budgets. This is a **student learning project** structured as a sequence of
numbered build steps; several routes are intentional placeholders to be
implemented in later steps.

## Tech stack

- **Backend:** Python + Flask 3.x
- **Templating:** Jinja2 (templates extend `base.html`)
- **Frontend:** Plain HTML/CSS + **vanilla JavaScript only** — no JS frameworks
  or page libraries (e.g. no React, jQuery, or modal libraries). Any
  interactive behavior (modals, etc.) must be hand-written vanilla JS.
- **Styling approach:** A single global stylesheet `static/css/style.css`
  defines the theme via CSS custom properties (`--ink`, `--paper`, `--accent`,
  `--radius-*`, etc.). Match these tokens rather than hardcoding colors.
- **Fonts:** DM Serif Display (headings) + DM Sans (body), loaded via Google
  Fonts in `base.html`.
- **Database:** SQLite via `database/db.py` (see status below).
- **Tests:** pytest + pytest-flask.

## Project structure

```
app.py                 # Flask app entry point; all routes defined here
database/db.py         # DB helpers (PLACEHOLDER — students implement)
templates/
  base.html            # Shared layout: navbar + footer + block hooks
  landing.html         # Marketing/hero landing page (home at "/")
  login.html           # Login page
  register.html        # Registration page
  terms.html           # Terms & Conditions (extends base.html)
  privacy.html         # Privacy Policy (extends base.html)
static/
  css/style.css        # Global theme + all component styles
  js/main.js           # Global client-side JS
.claude/settings.local.json  # Pre-approved permission rules for this repo
```

## How to run

Activate the virtualenv first, then run the app:

```bash
source venv/bin/activate
python app.py          # serves on http://127.0.0.1:5001, debug=True
```

Use the venv's `python`/`pip` (already allowlisted in settings). Installed
deps are pinned in `requirements.txt` (flask, werkzeug, pytest, pytest-flask).

## Routes

Defined in `app.py`:
- `/` → landing page
- `/register`, `/login` → auth pages
- `/terms`, `/privacy` → legal pages
- `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`,
  `/expenses/<id>/delete` → **placeholder stubs** returning "coming in Step X"
  strings. These are expected to be replaced with real implementations later.

Add new routes in `app.py` next to the existing ones, following the same
`render_template(...)` pattern.

## Conventions

- **Templates** should `{% extends "base.html" %}` and fill `{% block content %}`
  (and `{% block head %}` / `{% block scripts %}` as needed). Legal pages
  (`terms.html`, `privacy.html`) set their own scoped `<style>` in the `head`
  block using the shared CSS variables — follow that pattern for similar
  standalone pages.
- **Footer links** for Terms/Privacy live in `base.html` (shared across pages)
  and should point to `/terms` and `/privacy`.
- **JavaScript** must stay vanilla. The "See how it works" YouTube modal on the
  landing page is a reference example: opens on click, embeds a placeholder
  YouTube `<iframe>`, closes on close-button or backdrop click, and **clears
  the iframe `src` on close** so the video stops playing in the background.
- **Color/theme:** always reference the CSS variables in `style.css`; do not
  introduce off-palette hex values for core UI.
- **Currency:** shown as Indian Rupees (₹) throughout the UI.

## Database status

`database/db.py` is currently a **placeholder**. Per the in-file comment,
students will implement:
- `get_db()` — SQLite connection with `row_factory` and foreign keys enabled
- `init_db()` — create tables via `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — insert sample data for development

Do not assume these exist yet when writing features that touch the DB.

## Tests

Run from the repo root with the venv active:

```bash
pytest
```

## Notes for AI assistance

- This is a teaching project: when asked to "implement a step," expect to wire
  up the corresponding placeholder route and its template/DB logic.
- Keep changes scoped to what's asked; the landing-page tasks in git history
  demonstrate the expected pattern (small, single-purpose commits).
- `CLAUDE.md` and `README.md` may not both exist at all times — `README.md`
  was intentionally removed and will be recreated later.
