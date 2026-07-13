---
name: spendly-ui-designer
description: Designs and generates modern, production-ready UI for Spendly, a personal expense tracker built on Flask + Jinja2 + vanilla CSS (repo - https://github.com/amanpal07/spendly). Produces clean fintech-style pages and components - cards, forms, tables, dashboards, modals - with consistent spacing, soft shadows, rounded corners, and Unicode decorative icons. Use this skill whenever the user asks to design, build, create, redesign, improve, or style any Spendly page, screen, section, or component - including phrasings like "design the X page", "create UI for X", "build a component for X", "make the X look better", "redesign X", or any request about Spendly's frontend, layout, CSS, or visual polish - even when Spendly isn't named explicitly if the conversation context is clearly about it.
disable-model-invocation: true
---

# Spendly UI Designer

You are designing frontend UI for **Spendly**, a personal expense tracking web app. Spendly is a Flask app with server-rendered Jinja2 templates, vanilla CSS, and vanilla JS. The goal of this skill is to help you generate UI that feels like it belongs in a polished, modern fintech product — warm, editorial, premium — not generic Bootstrap-era output, and not React/Tailwind output that doesn't match the stack.

---

## The Stack (enforced, do not deviate)

| Layer | Technology | Location |
|-------|-----------|----------|
| Backend | Flask 3.x, Python 3 | `app.py` (all routes here) |
| Database | SQLite via `database/db.py` | `get_db()` returns `sqlite3.Row`-factory connections |
| Templates | Jinja2 | `templates/` — all extend `base.html` |
| Styles | Vanilla CSS (single file) | `static/css/style.css` |
| Scripts | Vanilla JS | `static/js/main.js` (+ inline `<script>` blocks in templates) |
| Fonts | Google Fonts — DM Serif Display + DM Sans | Loaded in `base.html` |
| Icons | Unicode characters (₹, ◈, ◎, ◷, ×) | No icon library — use Unicode glyphs or CSS-only decoration |

**Hard rules:**
- No React, Vue, Tailwind, shadcn, Bootstrap, jQuery, or CSS-in-JS
- No icon libraries (no Lucide, no FontAwesome) — Spendly uses Unicode glyphs
- No CSS preprocessors (no Sass/Less)
- No `<style>` attributes / inline styles on HTML elements — all styling via CSS classes
- Exception: legal pages (`terms.html`, `privacy.html`) use scoped `<style>` in `{% block head %}` with CSS variables — that's the established pattern for standalone pages

---

## Before You Design: Check What Exists

Before generating any new template or CSS, read these files to match the existing design:

1. `templates/base.html` — shared layout: navbar, `{% block content %}`, footer, `{% block head %}`, `{% block scripts %}`
2. `static/css/style.css` — every CSS class and variable lives here
3. At least one existing page template (e.g. `templates/login.html`, `templates/landing.html`)

The goal is **consistency** — Spendly should feel like one coherent product, not a collage.

---

## The Exact Design System (extracted from the live codebase)

### Colour Tokens (CSS custom properties defined in `:root`)

```css
/* Inks (text) */
--ink:        #0f0f0f;    /* Primary text */
--ink-soft:   #2d2d2d;    /* Secondary text, body copy */
--ink-muted:  #6b6b6b;    /* Tertiary text, labels */
--ink-faint:  #a0a0a0;    /* Hints, placeholders, metadata */

/* Papers (backgrounds) */
--paper:      #f7f6f3;    /* Page background — warm off-white */
--paper-warm: #f0ede6;    /* Section backgrounds (features band) */
--paper-card: #ffffff;    /* Card/surface background */

/* Accents */
--accent:       #1a472a;  /* Primary green — buttons, links, active states */
--accent-light: #e8f0eb;  /* Green tint — badges, highlights */
--accent-2:       #c17f24;  /* Secondary gold — feature icons, footer brand */
--accent-2-light: #fdf3e3;  /* Gold tint */

/* Semantic */
--danger:       #c0392b;  /* Errors, destructive actions */
--danger-light: #fdecea;  /* Error backgrounds */

/* Borders */
--border:      #e4e1da;   /* Default border */
--border-soft: #eeebe4;   /* Subtle inner borders, dividers */
```

> **Critical rule:** Always use these variables. Never hardcode hex values in templates or new CSS. When you need a new shade (e.g. category colours), add a new CSS custom property to `:root` in `style.css` — don't use one-off hex values in component rules.

### Typography

```css
--font-display: 'DM Serif Display', Georgia, serif;  /* Headings, hero text, stat values */
--font-body:    'DM Sans', system-ui, sans-serif;     /* Everything else */
```

**Type scale used in the codebase:**

| Use case | Size | Weight | Font |
|----------|------|--------|------|
| Hero title | `clamp(2.5rem, 5vw, 3.75rem)` | default | `--font-display` |
| Page title (auth, legal) | `2rem – 2.4rem` | default | `--font-display` |
| Section heading | `1.2rem – 1.35rem` | default | `--font-display` |
| Stat values | `1.65rem` | default | `--font-display` |
| Body text | `0.9rem – 1.05rem` | 400 | `--font-body` |
| Labels, captions | `0.78rem – 0.85rem` | 500 | `--font-body` |
| Eyebrow text | `0.8rem` | 500, `uppercase`, `letter-spacing: 0.12em` | `--font-body` |
| Small metadata | `0.75rem` | 500 | `--font-body` |

For amounts and numbers, use `font-variant-numeric: tabular-nums` to keep columns aligned.

### Spacing

The codebase uses `rem`-based spacing, roughly on a `0.25rem` grid:

| Token | Value | Common use |
|-------|-------|------------|
| Micro | `0.2rem – 0.4rem` | Label-to-input gap, tight vertical gaps |
| Small | `0.75rem – 1rem` | Inside form groups, between list items |
| Medium | `1.25rem – 1.5rem` | Card padding, section gaps |
| Large | `2rem` | Card padding, between sections |
| XL | `3rem – 5rem` | Page section padding-top/bottom |

### Border Radius

```css
--radius-sm: 6px;   /* Inputs, buttons, small badges */
--radius-md: 12px;  /* Cards, containers */
--radius-lg: 20px;  /* Mock cards, hero visuals */
```

Pills/badges use `border-radius: 999px`.

### Shadows

Spendly uses **very subtle shadows** — the aesthetic is flat with borders:
- Cards: `box-shadow: 0 8px 40px rgba(0,0,0,0.06)` (mock-card on hero)
- Modals: `box-shadow: 0 20px 60px rgba(0,0,0,0.4)` (over dark backdrop)
- Default cards: no shadow, just `border: 1px solid var(--border)`

### Layout Constraints

```css
--max-width:  1200px;  /* Page content maximum */
--auth-width: 440px;   /* Auth forms (login, register) */
```

Legal pages use `max-width: 760px`. Use similar `max-width` values for content pages (700–900px).

---

## Template Architecture

### Base layout (`base.html`)

```
┌─────────────────────────────────────────────────┐
│  navbar (.navbar > .nav-inner)                   │
│  ┌────────────────────────────────────────────┐  │
│  │ ◈ Spendly           [Sign in] [Get started]│  │
│  │ — or when logged in:                       │  │
│  │ ◈ Spendly           Hello, Name  [Log out] │  │
│  └────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  <main class="main-content">                     │
│    {% block content %}{% endblock %}              │
│  </main>                                         │
├─────────────────────────────────────────────────┤
│  footer (.footer — dark bg)                      │
│  ◈ Spendly · Terms · Privacy                     │
└─────────────────────────────────────────────────┘
```

**Blocks available:**
- `{% block title %}` — page title (default: "Spendly")
- `{% block head %}` — extra `<link>` / `<style>` in `<head>`
- `{% block content %}` — main page content
- `{% block scripts %}` — extra `<script>` after `main.js`

### Template naming convention

Every template extends `base.html` and fills `{% block content %}`. Title block follows the pattern `Page Name — Spendly`.

```jinja2
{% extends "base.html" %}
{% block title %}Page Name — Spendly{% endblock %}
{% block content %}
  <!-- page content -->
{% endblock %}
```

### Established page patterns

| Page type | Wrapper class | Max-width | Centering | Example |
|-----------|--------------|-----------|-----------|---------|
| Marketing/hero | `.hero` | `--max-width` | centered text | `landing.html` |
| Auth (login/register) | `.auth-section` + `.auth-container` | `--auth-width` | flexbox centered | `login.html` |
| Legal (terms/privacy) | `.legal` | `760px` | left-aligned prose | `terms.html` |
| Dev utility | `.debug-wrap` | `960px` | left-aligned tables | `debug.html` |
| Profile/dashboard | `.profile-section` + `.profile-container` | `~900px` | left-aligned cards | *(to be built)* |

---

## Existing Component Classes (reuse these, don't reinvent)

### Buttons

| Class | Look | Use |
|-------|------|-----|
| `.btn-primary` | Dark bg (`--ink`), light text, hover → `--accent` | Primary actions |
| `.btn-dark` | Slightly lighter dark (`--ink-soft`), hover → `--ink` | Secondary CTA |
| `.btn-ghost` | Transparent bg, bordered, hover darkens | Tertiary actions |
| `.btn-submit` | Full-width dark, inside forms | Form submit buttons |
| `.nav-cta` | Small dark pill in navbar | Navigation CTA |

### Form elements

| Class | Element | Notes |
|-------|---------|-------|
| `.form-group` | `<div>` wrapper | `margin-bottom: 1.25rem` |
| `.form-group label` | `<label>` | `0.85rem`, weight 500, `--ink-soft` |
| `.form-input` | `<input>` | Full-width, `--paper` bg, border focus → `--accent` |

### Auth layout

| Class | Purpose |
|-------|---------|
| `.auth-section` | Full-height centered flex wrapper |
| `.auth-container` | Width-constrained inner box |
| `.auth-header` | Centered title + subtitle |
| `.auth-title` | `--font-display`, 2rem |
| `.auth-subtitle` | `--ink-muted`, 0.9rem |
| `.auth-card` | White card with border and padding |
| `.auth-error` | Red error banner |
| `.auth-switch` | "Already have account? Sign in" link row |

### Mock dashboard (landing page)

| Class | Purpose |
|-------|---------|
| `.mock-card` | White card with shadow, rounded `--radius-lg` |
| `.mock-stats` | 3-column grid of stat cards |
| `.mock-stat-card` | Individual stat: label, value, change |
| `.mock-categories` | Stacked category bar rows |
| `.mock-cat-row` | Grid: name + bar track |
| `.mock-cat-track` / `.mock-cat-bar` | Progress bar track and fill |

### Tables (debug page)

| Class | Purpose |
|-------|---------|
| `.debug-table` | Full-width collapsed table |
| `.debug-table th` | Uppercase, small, muted headers |
| `.debug-table td` | Normal ink text, bottom border |

---

## CSS Architecture Rules

1. **Single stylesheet:** All styles go in `static/css/style.css` in clearly commented sections
2. **Section comments:** Use the established format:
   ```css
   /* ------------------------------------------------------------------ */
   /* Section Name                                                        */
   /* ------------------------------------------------------------------ */
   ```
3. **Class naming:** Use `.component-element` BEM-lite pattern (e.g. `.profile-user-card`, `.profile-stat-label`, `.category-badge`)
4. **Page scoping:** Prefix all classes for a new page with the page name (e.g. `.profile-*`, `.dashboard-*`, `.expense-form-*`) so styles don't leak
5. **No `!important`** unless absolutely necessary (the navbar CTA is an existing exception)
6. **Responsive:** Add overrides inside the existing `@media` blocks at the bottom of `style.css`:
   - `@media (max-width: 900px)` — tablets, stack grids
   - `@media (max-width: 600px)` — phones, hide nav links, tighter padding

---

## JavaScript Patterns

- **No frameworks, no jQuery** — vanilla JS only
- **IIFE pattern** for page-specific scripts (see the video modal in `landing.html`):
  ```javascript
  (function () {
      // All page-specific logic here
  })();
  ```
- **DOM references** via `getElementById` / `querySelectorAll`
- **Event delegation** with `data-*` attributes for dynamic targets
- **Escape key** handling for modals
- **Cleanup on close** — clear iframe `src`, reset forms, etc.
- Place inline scripts inside `{% block scripts %}` or directly in the template after the HTML

---

## Icons & Decorative Elements

Spendly does **NOT** use an icon library. It uses:

- **Unicode glyphs:** `◈` (brand), `₹` (currency), `◎` / `◷` (features), `×` (close), `←` (back arrow)
- **CSS shapes:** coloured dots (`.dot-red`, `.dot-green`, `.dot-yellow`) for the mock window chrome
- **Emoji/text:** simple text labels work — no icon needed for every action

When you need a visual indicator, use a Unicode glyph or a CSS-only solution (background colour, border, shaped div). If a future step introduces an icon library, it will be declared in `CLAUDE.md`.

---

## Currency

All monetary values are shown in **Indian Rupees (₹)**. Format with commas: `₹1,450.75`.

In Jinja2:
```jinja2
₹{{ "{:,.2f}".format(amount) }}
```

---

## Output Structure

When fulfilling a design request, structure your response as:

### 1. Short UI plan (2–5 bullets)
Name the key sections, layout decisions, and any UX notes. Keep it tight — orientation, not a spec.

### 2. The code
- **CSS additions** to `static/css/style.css` — new section with the standard header comment. All colours via CSS variables.
- **Template file** — full Jinja2 extending `base.html`, filling `{% block content %}`. Use Jinja control flow (`{% for %}`, `{% if %}`) with clear variable names matching what the Flask route will pass.
- **JS** (only if needed) — vanilla, IIFE-wrapped, in `{% block scripts %}` or inline.

Each file in its own fenced code block with a clear path annotation.

### 3. Integration note (1–3 lines)
Which Flask route renders this, what template variables it expects, and any `style.css` additions needed. Call out anything the user must wire up in `app.py`.

---

## Authentication Pattern

Protected pages (like `/profile`) must check `session.get("user_id")`:

```python
@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    # ... render the page
```

The navbar automatically shows the logged-in state via Jinja in `base.html`:
```jinja2
{% if session.get('user_id') %}
    <span class="nav-greeting">Hello, {{ session.get('user_name', 'there') }}</span>
    <a href="{{ url_for('logout') }}">Log out</a>
{% else %}
    <a href="{{ url_for('login') }}">Sign in</a>
    <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
{% endif %}
```

---

## What to Avoid

- **Generic/dated looks** — no sharp-cornered bordered boxes, no browser-default type, no 2012-era bootstrap aesthetic
- **Off-palette colours** — never hardcode hex values; always use or extend the CSS variables
- **Inline styles** — never use `style=""` for colours or layout. Width percentages on progress bar fills are acceptable (they're dynamic layout, not styling)
- **Icon libraries** — Spendly doesn't use Lucide, FontAwesome, or any icon CDN
- **Framework output** — no `className=`, no `tw-`, no component imports
- **Inconsistent spacing** — if card padding is `2rem` in one place, match it everywhere
- **Over-styling** — if a solid colour works, don't use a gradient. If a border works, don't add a shadow. Restraint reads as quality.
- **Mobile afterthought** — use CSS that works at narrow widths. Stack grids vertically, make tables scrollable below ~768px

---

## Handling Ambiguity

If the request is under-specified ("design the dashboard"), make reasonable assumptions and **state them up front** in the UI plan. For example: "Assuming the dashboard shows: summary stats, recent transactions, and category breakdown."

Don't pepper the user with questions for things you can reasonably decide. Do ask when the answer genuinely changes the structure — e.g. "Is this a standalone page or a modal overlay?"

---

## Quick Reference: Adding a New Page

1. **Route in `app.py`** — add next to existing routes, follow the `render_template(...)` pattern
2. **Template in `templates/`** — extend `base.html`, fill `{% block content %}`
3. **CSS in `static/css/style.css`** — add a new section with comment header, prefix all classes with the page name
4. **Responsive** — add overrides to the existing `@media` blocks at the bottom
5. **Title** — `{% block title %}Page Name — Spendly{% endblock %}`
6. **Test** — add `tests/test_pagename.py` following the `test_login.py` pattern
