# Agent Prompt: Web Dashboard

You are working on the `web/` module of a Python flight price tracker.

## Your scope
- `web/dashboard.py` — FastAPI router with two routes
- `main.py` — includes the dashboard router via `app.include_router(dashboard_router)`

## What this module does
- `GET /` — HTML table of all Tracker rows: route, date, last price, status, last checked, link to history
- `GET /tracker/{tracker_id}` — HTML page with Chart.js line chart of PriceHistory for one tracker

## Key rules
- No external template engine — all HTML is inline Python f-strings.
- Chart.js is loaded from CDN (no Python dependency).
- No authentication — this dashboard is local-only, never exposed publicly.
- Return FastAPI HTMLResponse objects (not dict/JSON).
- The dashboard router is mounted at root prefix — routes are `/` and `/tracker/{id}`, not `/dashboard/`.

## How to test
1. Start the app: `python main.py`
2. Visit `http://localhost:8000/` — should show tracker table (empty if no trackers yet)
3. Add a tracker row directly to SQLite and refresh
4. Visit `http://localhost:8000/tracker/<uuid>` — should show Chart.js chart
