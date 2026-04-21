# Plan 4: Scheduler, Alerts, Web Dashboard, CLAUDE.md + Agent Prompts + Git Branch

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the application with hourly price monitoring, daily digest, Gmail/WhatsApp alerts, a local web dashboard, updated CLAUDE.md, agent prompts for all sub-components, and commit everything to a new git branch.

**Architecture:** APScheduler runs two jobs in-process (hourly price monitor, 9AM digest). Alert modules are thin wrappers over Telegram API, Gmail SMTP, and Twilio REST. Dashboard is a FastAPI router with two routes and inline Chart.js HTML.

**Tech Stack:** APScheduler 3.x, smtplib (stdlib), twilio SDK, FastAPI (Jinja2-free, inline HTML), Jinja2 (optional for templates).

**Prerequisite:** Plans 1, 2, and 3 complete.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `alerts/gmail.py` | Create | Send email via Gmail SMTP |
| `alerts/whatsapp.py` | Create | Send WhatsApp via Twilio REST |
| `scheduler/__init__.py` | Create | Package marker |
| `scheduler/price_monitor.py` | Create | Hourly: check all active trackers, fire alerts |
| `scheduler/daily_digest.py` | Create | 9AM: send per-user digest |
| `web/__init__.py` | Create | Package marker |
| `web/dashboard.py` | Create | FastAPI router: `/` and `/tracker/{id}` |
| `main.py` | Modify | Add APScheduler startup, include dashboard router |
| `CLAUDE.md` | Rewrite | Updated for Python project |
| `prompts/agent-scraper.md` | Create | Prompt for scraper agent |
| `prompts/agent-bot.md` | Create | Prompt for bot agent |
| `prompts/agent-scheduler.md` | Create | Prompt for scheduler/alerts agent |
| `prompts/agent-dashboard.md` | Create | Prompt for dashboard agent |
| `tests/test_price_logic.py` | Create | Unit tests for price drop logic |
| `tests/test_alerts.py` | Create | Unit tests for alert formatting |

---

### Task 1: Write Gmail and WhatsApp alert modules

**Files:**
- Create: `alerts/gmail.py`
- Create: `alerts/whatsapp.py`

- [ ] **Step 1: Write alerts/gmail.py**

```python
import smtplib
from email.mime.text import MIMEText
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD

def send_email(to_address: str, subject: str, body: str) -> None:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_address
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())
```

- [ ] **Step 2: Write alerts/whatsapp.py**

```python
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM

def send_whatsapp(to_number: str, body: str) -> None:
    if not TWILIO_ACCOUNT_SID or not to_number:
        return
    from twilio.rest import Client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=body,
        from_=TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{to_number}",
    )
```

- [ ] **Step 3: Commit**

```bash
git add alerts/gmail.py alerts/whatsapp.py
git commit -m "feat: add Gmail SMTP and Twilio WhatsApp alert modules"
```

---

### Task 2: Write price drop logic and tests

**Files:**
- Create: `tests/test_price_logic.py`
- Create: `scheduler/price_monitor.py` (partial — logic functions only)

- [ ] **Step 1: Write failing tests for price logic**

```python
# tests/test_price_logic.py
import pytest
from scheduler.price_monitor import compute_price_drop

def test_percent_drop_triggers_alert():
    result = compute_price_drop(
        last_price=1000.0, current_price=880.0,
        threshold_percent=10.0, threshold_fixed=0.0,
        lowest_price=1000.0, days_tracked=1
    )
    assert result["is_significant"] is True
    assert abs(result["percent_drop"] - 12.0) < 0.1
    assert result["is_new_lowest"] is True
    assert result["is_mature_deal"] is False

def test_fixed_drop_triggers_alert():
    result = compute_price_drop(
        last_price=1000.0, current_price=940.0,
        threshold_percent=10.0, threshold_fixed=50.0,
        lowest_price=1000.0, days_tracked=1
    )
    assert result["is_significant"] is True

def test_no_drop_no_alert():
    result = compute_price_drop(
        last_price=1000.0, current_price=995.0,
        threshold_percent=10.0, threshold_fixed=0.0,
        lowest_price=1000.0, days_tracked=1
    )
    assert result["is_significant"] is False

def test_mature_deal_requires_3_days_and_new_lowest():
    result = compute_price_drop(
        last_price=1000.0, current_price=800.0,
        threshold_percent=10.0, threshold_fixed=0.0,
        lowest_price=900.0, days_tracked=4
    )
    assert result["is_mature_deal"] is True

def test_mature_deal_false_if_not_new_lowest():
    result = compute_price_drop(
        last_price=1000.0, current_price=950.0,
        threshold_percent=10.0, threshold_fixed=0.0,
        lowest_price=900.0, days_tracked=4
    )
    assert result["is_mature_deal"] is False
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_price_logic.py -v
```

Expected: `ImportError` — `scheduler.price_monitor` doesn't exist.

- [ ] **Step 3: Write scheduler/__init__.py**

```python
```
(empty file)

---

### Task 3: Implement full price monitor

**Files:**
- Create: `scheduler/price_monitor.py`

- [ ] **Step 1: Write scheduler/price_monitor.py**

```python
from datetime import datetime
from db.database import SessionLocal
from db.models import Tracker, PriceHistory
from alerts.telegram import send_message
from alerts.gmail import send_email
from alerts.whatsapp import send_whatsapp
from bot.messages import PRICE_DROP, BEST_DEAL
from scraper.google_flights import scrape_flights_sync

def compute_price_drop(
    last_price: float,
    current_price: float,
    threshold_percent: float,
    threshold_fixed: float,
    lowest_price: float,
    days_tracked: int,
) -> dict:
    percent_drop = (last_price - current_price) / last_price * 100
    is_significant = (
        percent_drop >= threshold_percent
        or (threshold_fixed > 0 and current_price <= last_price - threshold_fixed)
    )
    is_new_lowest = current_price < lowest_price
    is_mature_deal = days_tracked >= 3 and is_new_lowest
    return {
        "percent_drop": round(percent_drop, 2),
        "is_significant": is_significant,
        "is_new_lowest": is_new_lowest,
        "is_mature_deal": is_mature_deal,
    }

def run_price_monitor():
    db = SessionLocal()
    try:
        trackers = db.query(Tracker).filter_by(status="active").all()
        for tracker in trackers:
            result = scrape_flights_sync(
                tracker.from_airport,
                tracker.to_airport,
                tracker.travel_date,
                tracker.return_date,
                tracker.passengers,
            )
            if result is None:
                continue
            current_price = result["price"]
            days_tracked = (datetime.utcnow() - tracker.tracking_since).days
            drop = compute_price_drop(
                last_price=tracker.last_price or current_price,
                current_price=current_price,
                threshold_percent=tracker.alert_threshold_percent,
                threshold_fixed=tracker.alert_threshold_fixed,
                lowest_price=tracker.lowest_price or current_price,
                days_tracked=days_tracked,
            )
            ph = PriceHistory(
                tracker_id=tracker.tracker_id,
                price=current_price,
                airline=result.get("airline", ""),
                flight_numbers=result.get("flight_numbers", ""),
            )
            db.add(ph)
            tracker.last_checked = datetime.utcnow()
            if drop["is_significant"]:
                saving = (tracker.initial_price or current_price) - current_price
                if drop["is_mature_deal"]:
                    msg = BEST_DEAL.format(
                        days=days_tracked,
                        from_airport=tracker.from_airport,
                        to_airport=tracker.to_airport,
                        travel_date=tracker.travel_date,
                        currency=tracker.currency,
                        lowest_price=current_price,
                        initial_price=tracker.initial_price,
                        saving=round(saving, 2),
                        percent_drop=drop["percent_drop"],
                    )
                else:
                    msg = PRICE_DROP.format(
                        from_airport=tracker.from_airport,
                        to_airport=tracker.to_airport,
                        travel_date=tracker.travel_date,
                        currency=tracker.currency,
                        last_price=tracker.last_price,
                        current_price=current_price,
                        percent_drop=drop["percent_drop"],
                        airline=result.get("airline", ""),
                    )
                send_message(tracker.chat_id, msg)
                if tracker.email_alerts and tracker.email_address:
                    send_email(tracker.email_address, "Flight Price Drop Alert", msg)
                if tracker.whatsapp_number:
                    send_whatsapp(tracker.whatsapp_number, msg)
                tracker.last_price = current_price
                if drop["is_new_lowest"]:
                    tracker.lowest_price = current_price
            db.commit()
    finally:
        db.close()
```

- [ ] **Step 2: Run price logic tests — expect PASS**

```bash
pytest tests/test_price_logic.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scheduler/ tests/test_price_logic.py
git commit -m "feat: implement hourly price monitor with price drop logic"
```

---

### Task 4: Implement daily digest

**Files:**
- Create: `scheduler/daily_digest.py`

- [ ] **Step 1: Write scheduler/daily_digest.py**

```python
from datetime import datetime, timedelta
from collections import defaultdict
from db.database import SessionLocal
from db.models import Tracker, PriceHistory
from alerts.telegram import send_message
from alerts.gmail import send_email
from alerts.whatsapp import send_whatsapp
from bot.messages import DAILY_DIGEST_HEADER, DAILY_DIGEST_ROUTE
from scraper.google_flights import scrape_flights_sync

def run_daily_digest():
    db = SessionLocal()
    try:
        trackers = db.query(Tracker).filter_by(status="active").all()
        by_user: dict[str, list[Tracker]] = defaultdict(list)
        for t in trackers:
            by_user[t.chat_id].append(t)
        today = datetime.utcnow().date()
        for chat_id, user_trackers in by_user.items():
            lines = [DAILY_DIGEST_HEADER.format(date=str(today))]
            for tracker in user_trackers:
                result = scrape_flights_sync(
                    tracker.from_airport, tracker.to_airport,
                    tracker.travel_date, tracker.return_date, tracker.passengers,
                )
                if result is None:
                    continue
                yesterday = datetime.utcnow() - timedelta(days=1)
                yesterday_entry = (
                    db.query(PriceHistory)
                    .filter(
                        PriceHistory.tracker_id == tracker.tracker_id,
                        PriceHistory.timestamp >= yesterday,
                    )
                    .order_by(PriceHistory.timestamp.asc())
                    .first()
                )
                yesterday_price = yesterday_entry.price if yesterday_entry else result["price"]
                days = (datetime.utcnow() - tracker.tracking_since).days
                lines.append(DAILY_DIGEST_ROUTE.format(
                    from_airport=tracker.from_airport,
                    to_airport=tracker.to_airport,
                    currency=tracker.currency,
                    price=result["price"],
                    yesterday_price=yesterday_price,
                    lowest=tracker.lowest_price or result["price"],
                    days=days,
                ))
            if len(lines) <= 1:
                continue
            msg = "\n".join(lines)
            send_message(chat_id, msg)
            first_tracker = user_trackers[0]
            if first_tracker.email_alerts and first_tracker.email_address:
                send_email(first_tracker.email_address, f"Daily Flight Digest – {today}", msg)
            if first_tracker.whatsapp_number:
                send_whatsapp(first_tracker.whatsapp_number, msg)
    finally:
        db.close()
```

- [ ] **Step 2: Commit**

```bash
git add scheduler/daily_digest.py
git commit -m "feat: implement daily digest scheduler job"
```

---

### Task 5: Build web dashboard

**Files:**
- Create: `web/__init__.py`
- Create: `web/dashboard.py`

- [ ] **Step 1: Write web/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write web/dashboard.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Tracker, PriceHistory

router = APIRouter()

@router.get("/", response_class=None)
def dashboard(db: Session = Depends(get_db)):
    from fastapi.responses import HTMLResponse
    trackers = db.query(Tracker).all()
    rows = ""
    for t in trackers:
        rows += (
            f"<tr>"
            f"<td>{t.from_airport} → {t.to_airport}</td>"
            f"<td>{t.travel_date}</td>"
            f"<td>{t.currency} {t.last_price}</td>"
            f"<td>{t.status}</td>"
            f"<td>{str(t.last_checked)[:16] if t.last_checked else 'Never'}</td>"
            f"<td><a href='/tracker/{t.tracker_id}'>History</a></td>"
            f"</tr>"
        )
    html = f"""<!DOCTYPE html><html><head><title>Flight Tracker</title>
    <style>body{{font-family:sans-serif;padding:20px}}table{{border-collapse:collapse;width:100%}}
    th,td{{border:1px solid #ddd;padding:8px}}th{{background:#f2f2f2}}</style></head>
    <body><h1>Flight Price Tracker</h1>
    <table><tr><th>Route</th><th>Date</th><th>Last Price</th><th>Status</th><th>Last Checked</th><th></th></tr>
    {rows}</table></body></html>"""
    return HTMLResponse(html)

@router.get("/tracker/{tracker_id}", response_class=None)
def tracker_detail(tracker_id: str, db: Session = Depends(get_db)):
    from fastapi.responses import HTMLResponse
    tracker = db.query(Tracker).filter_by(tracker_id=tracker_id).first()
    if not tracker:
        return HTMLResponse("<h1>Not found</h1>", status_code=404)
    history = db.query(PriceHistory).filter_by(tracker_id=tracker_id).order_by(PriceHistory.timestamp).all()
    labels = [str(h.timestamp)[:16] for h in history]
    prices = [h.price for h in history]
    html = f"""<!DOCTYPE html><html><head><title>{tracker.from_airport} → {tracker.to_airport}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script></head>
    <body style="font-family:sans-serif;padding:20px">
    <h1>✈ {tracker.from_airport} → {tracker.to_airport}</h1>
    <p>Travel date: {tracker.travel_date} | Status: {tracker.status} | Lowest: {tracker.currency} {tracker.lowest_price}</p>
    <canvas id="chart" width="800" height="400"></canvas>
    <script>
    new Chart(document.getElementById('chart'), {{
      type: 'line',
      data: {{
        labels: {labels},
        datasets: [{{label: 'Price ({tracker.currency})', data: {prices}, borderColor: '#4a90e2', tension: 0.1}}]
      }},
      options: {{responsive: false}}
    }});
    </script>
    <p><a href="/">← Back</a></p></body></html>"""
    return HTMLResponse(html)
```

- [ ] **Step 3: Commit**

```bash
git add web/
git commit -m "feat: add web dashboard with route list and price history chart"
```

---

### Task 6: Wire APScheduler into main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace main.py with full version**

```python
from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from db.database import init_db, get_db
from web.dashboard import router as dashboard_router

app = FastAPI(title="Flight Price Tracker")
scheduler = BackgroundScheduler()

@app.on_event("startup")
def on_startup():
    init_db()
    from scheduler.price_monitor import run_price_monitor
    from scheduler.daily_digest import run_daily_digest
    scheduler.add_job(run_price_monitor, "cron", minute=0)
    scheduler.add_job(run_daily_digest, "cron", hour=9, minute=0)
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()

app.include_router(dashboard_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    from bot.handlers import handle_message
    from alerts.telegram import send_message
    from scraper.google_flights import scrape_flights_sync
    data = await request.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")
    if chat_id and text:
        handle_message(db=db, chat_id=chat_id, text=text,
                       send_fn=send_message, scrape_fn=scrape_flights_sync)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
```

Note: Use `reload=False` — APScheduler conflicts with uvicorn's reload mode.

- [ ] **Step 2: Start the app and verify**

```bash
python main.py
```

Expected:
- Server starts on port 8000
- APScheduler logs two jobs registered (hourly price monitor, 9AM digest)
- `GET http://localhost:8000/` shows dashboard table
- `GET http://localhost:8000/health` returns `{"status": "ok"}`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: wire APScheduler hourly monitor and daily digest into FastAPI startup"
```

---

### Task 7: Rewrite CLAUDE.md for the Python project

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite CLAUDE.md**

```markdown
# Flight Price Tracker — Claude Code Instructions

## Project Overview

A Python-based automated flight price tracking system that uses web scraping instead of paid APIs.
Monitors prices from Google Flights via Playwright, stores data in SQLite, and alerts users via Telegram, Gmail, and WhatsApp.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI + Uvicorn |
| Bot interface | Telegram Bot API (webhook via python-telegram-bot) |
| Flight data | Playwright scraping Google Flights (headless Chromium) |
| Database | SQLite via SQLAlchemy 2.x ORM |
| Scheduling | APScheduler (in-process background jobs) |
| Email | Gmail SMTP with app password (smtplib) |
| WhatsApp | Twilio REST API |
| HTML parsing | BeautifulSoup4 |
| Config | python-dotenv (.env file) |

---

## Directory Structure

```
flight-price-tracker/
├── main.py                    # Entry point: FastAPI app + APScheduler
├── config.py                  # Environment variable loading
├── requirements.txt
├── .env                       # Local credentials (not committed)
├── CLAUDE.md
├── bot/
│   ├── handlers.py            # Telegram state machine (steps 0-10)
│   └── messages.py            # All message templates
├── scraper/
│   ├── google_flights.py      # Playwright scraper + URL builder
│   └── parser.py              # BeautifulSoup HTML parser
├── scheduler/
│   ├── price_monitor.py       # Hourly: check active trackers, fire alerts
│   └── daily_digest.py        # 9AM: per-user digest
├── db/
│   ├── models.py              # SQLAlchemy: Session, Tracker, PriceHistory
│   └── database.py            # Engine, SessionLocal, init_db()
├── web/
│   └── dashboard.py           # FastAPI router: / and /tracker/{id}
├── alerts/
│   ├── telegram.py            # send_message(chat_id, text)
│   ├── gmail.py               # send_email(to, subject, body)
│   └── whatsapp.py            # send_whatsapp(to_number, body)
├── prompts/
│   ├── agent-scraper.md
│   ├── agent-bot.md
│   ├── agent-scheduler.md
│   └── agent-dashboard.md
└── tests/
    ├── conftest.py
    ├── test_db_models.py
    ├── test_scraper_parser.py
    ├── test_bot_handlers.py
    └── test_price_logic.py
```

---

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Copy and fill env vars
cp .env.example .env

# Start
python main.py
```

Server runs on `http://localhost:8000`
Dashboard at `http://localhost:8000/`

---

## Telegram Webhook Setup

```bash
# Start ngrok
ngrok http 8000

# Register webhook
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<ngrok-url>/webhook"
```

---

## Key Implementation Rules

1. **Scraper selectors change** — if Google Flights updates their DOM, update `data-testid` in `scraper/google_flights.py` and class selectors in `scraper/parser.py`.
2. **Batch size = 1** — price monitor processes one tracker at a time to avoid overwhelming Playwright.
3. **APScheduler + uvicorn** — always run with `reload=False`; reload mode conflicts with BackgroundScheduler.
4. **SQLite concurrency** — `check_same_thread=False` is set; APScheduler jobs use their own `SessionLocal()` instances, not the FastAPI request session.
5. **Gmail app password** — use a Google App Password (not your account password). Enable 2FA first, then generate at myaccount.google.com/apppasswords.
6. **WhatsApp optional** — alerts only fire if `whatsapp_number` is set on the Tracker row.
7. **No flights found** — if Playwright returns None, bot replies with the NO_FLIGHTS message and resets to step 0.
8. **Price history** — every scrape result is appended to PriceHistory, not just drops.

---

## Running Tests

```bash
pytest tests/ -v
```

All tests use an in-memory SQLite database (defined in `tests/conftest.py`). No network calls in unit tests.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: rewrite CLAUDE.md for Python architecture"
```

---

### Task 8: Write agent prompts

**Files:**
- Create: `prompts/agent-scraper.md`
- Create: `prompts/agent-bot.md`
- Create: `prompts/agent-scheduler.md`
- Create: `prompts/agent-dashboard.md`

- [ ] **Step 1: Write prompts/agent-scraper.md**

```markdown
# Agent Prompt: Scraper

You are working on the `scraper/` module of a Python flight price tracker.

## Your scope
- `scraper/google_flights.py` — Playwright async scraper and URL builder
- `scraper/parser.py` — BeautifulSoup HTML parser
- `tests/test_scraper_parser.py` — parser unit tests
- `tests/fixtures/google_flights_sample.html` — fixture HTML for tests

## What this module does
Launches a headless Chromium browser via Playwright, navigates to Google Flights with a search URL, waits for prices to render, extracts the cheapest flight's price/airline/flight numbers, and returns a dict or None.

## Key rules
- Google Flights CSS class names change frequently. If selectors break, inspect the live page with `headless=False` and update `data-testid` values in `google_flights.py` and class names in `parser.py`.
- Always use `playwright-stealth` to reduce bot detection.
- Return `None` (not raise) when no results are found.
- Parser tests must use the HTML fixture file, not live network calls.
- The return type is always: `{"price": float, "airline": str, "flight_numbers": str, "currency": str}` or `None`.

## How to test
```bash
pytest tests/test_scraper_parser.py -v
```

For live smoke test:
```python
from scraper.google_flights import scrape_flights_sync
print(scrape_flights_sync("YYZ", "BOM", "2026-06-01"))
```
```

- [ ] **Step 2: Write prompts/agent-bot.md**

```markdown
# Agent Prompt: Telegram Bot

You are working on the `bot/` module of a Python flight price tracker.

## Your scope
- `bot/handlers.py` — 10-step state machine: handle_message() is the entry point
- `bot/messages.py` — all message template strings
- `alerts/telegram.py` — send_message(chat_id, text) helper
- `tests/test_bot_handlers.py` — state machine unit tests
- `main.py` — POST /webhook route (reads Telegram update, calls handle_message)

## What this module does
Receives Telegram webhook POST → extracts chat_id and text → reads BotSession from SQLite → routes to the handler for the current step → saves answer to temp_data JSON → advances step → sends next question.

At step 9: calls scrape_fn, writes Tracker + PriceHistory rows, sends current price.
At step 10: handles /stop (marks tracker stopped) and /status (sends tracker summary).

## Key rules
- handle_message() signature: `(db, chat_id, text, send_fn, scrape_fn=None)` — always pass send_fn and scrape_fn as callables so they can be mocked in tests.
- Never import send_message or scrape_flights_sync at module level in handlers.py — they are injected.
- temp_data is always a JSON string stored in BotSession.temp_data column.
- Step 9 is triggered automatically after step 8 saves — handle_message calls itself recursively for step 9.
- If scrape_fn is None (in tests), step 9 falls back to sending NO_FLIGHTS.

## How to test
```bash
pytest tests/test_bot_handlers.py -v
```
```

- [ ] **Step 3: Write prompts/agent-scheduler.md**

```markdown
# Agent Prompt: Scheduler and Alerts

You are working on the `scheduler/` and `alerts/` modules of a Python flight price tracker.

## Your scope
- `scheduler/price_monitor.py` — hourly job: scrape all active trackers, compute price drops, fire alerts
- `scheduler/daily_digest.py` — 9AM job: group trackers by user, send digest
- `alerts/telegram.py` — send_message(chat_id, text)
- `alerts/gmail.py` — send_email(to, subject, body)
- `alerts/whatsapp.py` — send_whatsapp(to_number, body)
- `tests/test_price_logic.py` — unit tests for compute_price_drop()

## Key rules
- Each scheduler job creates its own `SessionLocal()` — do NOT reuse the FastAPI request session.
- WhatsApp alerts only fire if tracker.whatsapp_number is set (non-empty).
- Gmail alerts only fire if tracker.email_alerts is True AND tracker.email_address is set.
- Every scrape result is appended to PriceHistory, even when no alert fires.
- compute_price_drop() is a pure function — no DB or network calls — keep it testable.
- Alert modules silently no-op if credentials are missing (check config values before calling external APIs).

## Price drop logic
```python
percent_drop = (last_price - current_price) / last_price * 100
is_significant = percent_drop >= threshold_percent OR current_price <= last_price - threshold_fixed
is_new_lowest = current_price < lowest_price
is_mature_deal = days_tracked >= 3 AND is_new_lowest
```

## How to test
```bash
pytest tests/test_price_logic.py -v
```

To manually trigger the hourly job:
```python
from scheduler.price_monitor import run_price_monitor
run_price_monitor()
```
```

- [ ] **Step 4: Write prompts/agent-dashboard.md**

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add prompts/
git commit -m "docs: add agent prompts for scraper, bot, scheduler, and dashboard"
```

---

### Task 9: Create git branch and push all work

- [ ] **Step 1: Create and switch to new branch**

```bash
git checkout -b python-rewrite
```

- [ ] **Step 2: Verify all tests pass**

```bash
pytest tests/ -v
```

Expected: All tests PASS (db models, parser, bot handlers, price logic).

- [ ] **Step 3: Check git log**

```bash
git log --oneline
```

Confirm all commits from Plans 1-4 are present on the branch.

- [ ] **Step 4: Done**

The `python-rewrite` branch now contains the complete Python implementation. To start the app:

```bash
python main.py
```

To run tests:
```bash
pytest tests/ -v
```
