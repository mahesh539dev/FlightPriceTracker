# Plan 3: Telegram Bot State Machine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Telegram bot with a 10-step onboarding state machine that collects flight preferences, triggers a price scrape at step 9, and handles `/stop` and `/status` commands at step 10.

**Architecture:** FastAPI POST `/webhook` endpoint receives Telegram updates. `bot/handlers.py` reads the user's current step from SQLite Sessions table, routes to the correct handler function, saves the answer, and sends the next question. At step 9, calls `scraper.google_flights.scrape_flights_sync`, writes a Tracker row, and sends current prices.

**Tech Stack:** FastAPI, python-telegram-bot v20 (for sending messages via Bot API), SQLAlchemy, Playwright scraper (from Plan 2).

**Prerequisite:** Plans 1 and 2 complete.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `bot/__init__.py` | Create | Package marker |
| `bot/messages.py` | Create | All message template strings |
| `bot/handlers.py` | Create | Step router + per-step handler functions |
| `alerts/telegram.py` | Create | `send_message(chat_id, text)` helper |
| `main.py` | Modify | Add `/webhook` POST route |
| `tests/test_bot_handlers.py` | Create | Unit tests for state machine step logic |

---

### Task 1: Write message templates

**Files:**
- Create: `bot/__init__.py`
- Create: `bot/messages.py`

- [ ] **Step 1: Write bot/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write bot/messages.py**

```python
WELCOME = (
    "Welcome to FlightTracker Bot!\n"
    "I'll monitor flight prices for you and alert you when they drop.\n\n"
    "First — do you want to receive email alerts?\n"
    "Reply: YES or NO"
)

ASK_EMAIL = "Please enter your Gmail address:"

ASK_ORIGIN = "Enter your origin airport or city (e.g. YYZ or Toronto):"

ASK_DESTINATION = "Enter your destination airport or city (e.g. BOM or Mumbai):"

ASK_TRAVEL_DATE = "Enter your departure date (YYYY-MM-DD):"

ASK_RETURN_DATE = "Enter your return date (YYYY-MM-DD), or reply ONEWAY for a one-way trip:"

ASK_PASSENGERS = "How many adult passengers?"

ASK_NEARBY = "Should I also check nearby airports? Reply: YES or NO"

ASK_THRESHOLD = (
    "How much should the price drop before I alert you?\n"
    "1) 5%\n2) 10%\n3) 15%\n4) Custom (reply with a dollar amount, e.g. 50)"
)

CONFIRMATION = (
    "Got it! Here's your tracking setup:\n"
    "✈ {from_airport} → {to_airport}\n"
    "Depart: {travel_date} | Return: {return_date}\n"
    "{passengers} Adult(s)\n"
    "Alert when price drops by {threshold}\n"
    "Email alerts: {email_alerts} ({email_address})\n"
    "Nearby airports: {check_nearby}\n\n"
    "Searching for current prices..."
)

NO_FLIGHTS = "No flights found for this route/date. Try different dates."

CURRENT_PRICE = (
    "✈ {from_airport} → {to_airport}\n"
    "{travel_date}\n"
    "Current price: {currency} {price}\n"
    "Airline: {airline}\n\n"
    "I'll notify you when the price drops by your threshold. Send /stop to stop tracking."
)

STATUS = (
    "✈ {from_airport} → {to_airport}\n"
    "Tracking since: {tracking_since}\n"
    "Initial price: {currency} {initial_price}\n"
    "Current price: {currency} {last_price}\n"
    "Lowest ever: {currency} {lowest_price}\n"
    "Last checked: {last_checked}"
)

STOPPED = "Tracking stopped. Send a new message to start tracking a new route."

PRICE_DROP = (
    "Price Drop Alert!\n"
    "✈ {from_airport} → {to_airport}\n"
    "{travel_date}\n"
    "Was: {currency} {last_price}\n"
    "Now: {currency} {current_price} (down {percent_drop}%)\n"
    "Airline: {airline}\n"
    "Book quickly — prices can change!"
)

BEST_DEAL = (
    "BEST PRICE in {days} Days of Tracking!\n"
    "✈ {from_airport} → {to_airport}\n"
    "{travel_date}\n"
    "Lowest Ever: {currency} {lowest_price} (was {currency} {initial_price} when you started)\n"
    "That's a saving of {currency} {saving}! (down {percent_drop}%)\n"
    "This is the lowest we've seen — act fast!"
)

DAILY_DIGEST_HEADER = "Daily Flight Price Report – {date}\n──────────────────────────"

DAILY_DIGEST_ROUTE = (
    "✈ {from_airport} → {to_airport}\n"
    "Today: {currency} {price} | Yesterday: {currency} {yesterday_price}\n"
    "Lowest Ever: {currency} {lowest} | Tracking: {days} days\n"
    "──────────────────────────"
)
```

- [ ] **Step 3: Commit**

```bash
git add bot/
git commit -m "feat: add bot message templates"
```

---

### Task 2: Write Telegram send helper

**Files:**
- Create: `alerts/__init__.py`
- Create: `alerts/telegram.py`

- [ ] **Step 1: Write alerts/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write alerts/telegram.py**

```python
import httpx
from config import TELEGRAM_BOT_TOKEN

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id: str | int, text: str) -> None:
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": str(chat_id), "text": text, "parse_mode": "HTML"}
    with httpx.Client() as client:
        client.post(url, json=payload, timeout=10)
```

- [ ] **Step 3: Commit**

```bash
git add alerts/
git commit -m "feat: add Telegram send_message helper"
```

---

### Task 3: Write failing handler tests

**Files:**
- Create: `tests/test_bot_handlers.py`

- [ ] **Step 1: Write tests/test_bot_handlers.py**

```python
import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.models import Session as BotSession, Tracker

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    S = sessionmaker(bind=engine)
    session = S()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_step0_new_user_creates_session(db):
    from bot.handlers import handle_message
    sent = []
    handle_message(db=db, chat_id="u1", text="hello", send_fn=lambda cid, txt: sent.append(txt))
    session = db.query(BotSession).filter_by(chat_id="u1").first()
    assert session is not None
    assert session.step == 0
    assert any("Welcome" in m for m in sent)

def test_step0_yes_advances_to_step1(db):
    db.add(BotSession(chat_id="u2", step=0, temp_data="{}"))
    db.commit()
    sent = []
    from bot.handlers import handle_message
    handle_message(db=db, chat_id="u2", text="YES", send_fn=lambda cid, txt: sent.append(txt))
    session = db.query(BotSession).filter_by(chat_id="u2").first()
    assert session.step == 1

def test_step0_no_skips_email_to_step2(db):
    db.add(BotSession(chat_id="u3", step=0, temp_data="{}"))
    db.commit()
    sent = []
    from bot.handlers import handle_message
    handle_message(db=db, chat_id="u3", text="NO", send_fn=lambda cid, txt: sent.append(txt))
    session = db.query(BotSession).filter_by(chat_id="u3").first()
    assert session.step == 2

def test_step10_stop_command(db):
    import uuid
    tracker_id = str(uuid.uuid4())
    db.add(BotSession(chat_id="u4", step=10, temp_data=f'{{"tracker_id": "{tracker_id}"}}'))
    db.add(Tracker(tracker_id=tracker_id, chat_id="u4", from_airport="YYZ",
                   to_airport="BOM", travel_date="2026-06-01", status="active"))
    db.commit()
    sent = []
    from bot.handlers import handle_message
    handle_message(db=db, chat_id="u4", text="/stop", send_fn=lambda cid, txt: sent.append(txt))
    tracker = db.query(Tracker).filter_by(tracker_id=tracker_id).first()
    assert tracker.status == "stopped"
    assert any("stopped" in m.lower() for m in sent)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_bot_handlers.py -v
```

Expected: `ImportError` — `bot.handlers` doesn't exist yet.

---

### Task 4: Implement bot/handlers.py

**Files:**
- Create: `bot/handlers.py`

- [ ] **Step 1: Write bot/handlers.py**

```python
import json
import uuid
from datetime import datetime
from typing import Callable
from sqlalchemy.orm import Session as DBSession
from db.models import Session as BotSession, Tracker, PriceHistory
from bot import messages

THRESHOLD_MAP = {"1": 5.0, "2": 10.0, "3": 15.0}

def handle_message(
    db: DBSession,
    chat_id: str,
    text: str,
    send_fn: Callable[[str, str], None],
    scrape_fn: Callable | None = None,
) -> None:
    session = db.query(BotSession).filter_by(chat_id=chat_id).first()
    if session is None:
        session = BotSession(chat_id=chat_id, step=0, temp_data="{}")
        db.add(session)
        db.commit()
        send_fn(chat_id, messages.WELCOME)
        return

    step = session.step
    temp = json.loads(session.temp_data or "{}")

    if step == 0:
        _handle_step0(db, session, temp, chat_id, text.upper(), send_fn)
    elif step == 1:
        _handle_step1(db, session, temp, chat_id, text, send_fn)
    elif step == 2:
        _handle_step2(db, session, temp, chat_id, text.upper(), send_fn)
    elif step == 3:
        _handle_step3(db, session, temp, chat_id, text.upper(), send_fn)
    elif step == 4:
        _handle_step4(db, session, temp, chat_id, text, send_fn)
    elif step == 5:
        _handle_step5(db, session, temp, chat_id, text, send_fn)
    elif step == 6:
        _handle_step6(db, session, temp, chat_id, text, send_fn)
    elif step == 7:
        _handle_step7(db, session, temp, chat_id, text.upper(), send_fn)
    elif step == 8:
        _handle_step8(db, session, temp, chat_id, text, send_fn)
    elif step == 9:
        _handle_step9(db, session, temp, chat_id, send_fn, scrape_fn)
    elif step == 10:
        _handle_step10(db, session, temp, chat_id, text, send_fn, scrape_fn)

def _save(db, session, temp, step):
    session.temp_data = json.dumps(temp)
    session.step = step
    session.last_active = datetime.utcnow()
    db.commit()

def _handle_step0(db, session, temp, chat_id, text, send_fn):
    if text == "YES":
        temp["email_alerts"] = True
        _save(db, session, temp, 1)
        send_fn(chat_id, messages.ASK_EMAIL)
    else:
        temp["email_alerts"] = False
        temp["email_address"] = None
        _save(db, session, temp, 2)
        send_fn(chat_id, messages.ASK_ORIGIN)

def _handle_step1(db, session, temp, chat_id, text, send_fn):
    temp["email_address"] = text.strip()
    _save(db, session, temp, 2)
    send_fn(chat_id, messages.ASK_ORIGIN)

def _handle_step2(db, session, temp, chat_id, text, send_fn):
    temp["from_airport"] = text.strip()
    _save(db, session, temp, 3)
    send_fn(chat_id, messages.ASK_DESTINATION)

def _handle_step3(db, session, temp, chat_id, text, send_fn):
    temp["to_airport"] = text.strip()
    _save(db, session, temp, 4)
    send_fn(chat_id, messages.ASK_TRAVEL_DATE)

def _handle_step4(db, session, temp, chat_id, text, send_fn):
    temp["travel_date"] = text.strip()
    _save(db, session, temp, 5)
    send_fn(chat_id, messages.ASK_RETURN_DATE)

def _handle_step5(db, session, temp, chat_id, text, send_fn):
    temp["return_date"] = text.strip()
    _save(db, session, temp, 6)
    send_fn(chat_id, messages.ASK_PASSENGERS)

def _handle_step6(db, session, temp, chat_id, text, send_fn):
    temp["passengers"] = int(text.strip()) if text.strip().isdigit() else 1
    _save(db, session, temp, 7)
    send_fn(chat_id, messages.ASK_NEARBY)

def _handle_step7(db, session, temp, chat_id, text, send_fn):
    temp["check_nearby"] = text == "YES"
    _save(db, session, temp, 8)
    send_fn(chat_id, messages.ASK_THRESHOLD)

def _handle_step8(db, session, temp, chat_id, text, send_fn):
    t = text.strip()
    if t in THRESHOLD_MAP:
        temp["alert_threshold_percent"] = THRESHOLD_MAP[t]
        temp["alert_threshold_fixed"] = 0.0
    else:
        try:
            temp["alert_threshold_fixed"] = float(t.replace("$", ""))
            temp["alert_threshold_percent"] = 0.0
        except ValueError:
            temp["alert_threshold_percent"] = 10.0
            temp["alert_threshold_fixed"] = 0.0
    _save(db, session, temp, 9)
    confirm = messages.CONFIRMATION.format(
        from_airport=temp.get("from_airport", ""),
        to_airport=temp.get("to_airport", ""),
        travel_date=temp.get("travel_date", ""),
        return_date=temp.get("return_date", "ONEWAY"),
        passengers=temp.get("passengers", 1),
        threshold=f"{temp.get('alert_threshold_percent', 0)}% / ${temp.get('alert_threshold_fixed', 0)}",
        email_alerts="YES" if temp.get("email_alerts") else "NO",
        email_address=temp.get("email_address") or "N/A",
        check_nearby="YES" if temp.get("check_nearby") else "NO",
    )
    send_fn(chat_id, confirm)
    # Immediately trigger step 9
    handle_message(db=db, chat_id=chat_id, text="", send_fn=send_fn, scrape_fn=None)

def _handle_step9(db, session, temp, chat_id, send_fn, scrape_fn):
    result = None
    if scrape_fn:
        result = scrape_fn(
            temp.get("from_airport", ""),
            temp.get("to_airport", ""),
            temp.get("travel_date", ""),
            temp.get("return_date"),
            temp.get("passengers", 1),
        )
    if result is None:
        send_fn(chat_id, messages.NO_FLIGHTS)
        _save(db, session, temp, 0)
        return
    tracker_id = str(uuid.uuid4())
    tracker = Tracker(
        tracker_id=tracker_id,
        chat_id=chat_id,
        from_airport=temp.get("from_airport", ""),
        to_airport=temp.get("to_airport", ""),
        travel_date=temp.get("travel_date", ""),
        return_date=temp.get("return_date", "ONEWAY"),
        passengers=temp.get("passengers", 1),
        check_nearby=temp.get("check_nearby", False),
        initial_price=result["price"],
        last_price=result["price"],
        lowest_price=result["price"],
        last_checked=datetime.utcnow(),
        alert_threshold_percent=temp.get("alert_threshold_percent", 10.0),
        alert_threshold_fixed=temp.get("alert_threshold_fixed", 0.0),
        email_alerts=temp.get("email_alerts", False),
        email_address=temp.get("email_address"),
        status="active",
        currency=result.get("currency", "CAD"),
    )
    db.add(tracker)
    ph = PriceHistory(
        tracker_id=tracker_id,
        price=result["price"],
        airline=result.get("airline", ""),
        flight_numbers=result.get("flight_numbers", ""),
    )
    db.add(ph)
    temp["tracker_id"] = tracker_id
    _save(db, session, temp, 10)
    send_fn(chat_id, messages.CURRENT_PRICE.format(
        from_airport=tracker.from_airport,
        to_airport=tracker.to_airport,
        travel_date=tracker.travel_date,
        currency=tracker.currency,
        price=result["price"],
        airline=result.get("airline", ""),
    ))

def _handle_step10(db, session, temp, chat_id, text, send_fn, scrape_fn):
    if text.strip().lower() == "/stop":
        tracker_id = temp.get("tracker_id")
        if tracker_id:
            tracker = db.query(Tracker).filter_by(tracker_id=tracker_id).first()
            if tracker:
                tracker.status = "stopped"
                db.commit()
        send_fn(chat_id, messages.STOPPED)
    elif text.strip().lower() == "/status":
        tracker_id = temp.get("tracker_id")
        tracker = db.query(Tracker).filter_by(tracker_id=tracker_id).first() if tracker_id else None
        if not tracker:
            send_fn(chat_id, "No active tracker found.")
            return
        send_fn(chat_id, messages.STATUS.format(
            from_airport=tracker.from_airport,
            to_airport=tracker.to_airport,
            tracking_since=str(tracker.tracking_since)[:10],
            currency=tracker.currency,
            initial_price=tracker.initial_price,
            last_price=tracker.last_price,
            lowest_price=tracker.lowest_price,
            last_checked=str(tracker.last_checked)[:16] if tracker.last_checked else "Never",
        ))
```

- [ ] **Step 2: Run tests — expect PASS**

```bash
pytest tests/test_bot_handlers.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add bot/handlers.py
git commit -m "feat: implement Telegram bot state machine (steps 0-10)"
```

---

### Task 5: Add /webhook route to main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Update main.py to add webhook route**

```python
from fastapi import FastAPI, Request
from db.database import init_db, get_db
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(title="Flight Price Tracker")

@app.on_event("startup")
def on_startup():
    init_db()

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
        handle_message(
            db=db,
            chat_id=chat_id,
            text=text,
            send_fn=send_message,
            scrape_fn=scrape_flights_sync,
        )
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: Register Telegram webhook**

Start ngrok: `ngrok http 8000`

Copy the HTTPS URL (e.g. `https://abc123.ngrok.io`) and register it:

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook"
```

Expected response: `{"ok":true,"result":true,"description":"Webhook was set"}`

- [ ] **Step 3: End-to-end test**

Send a message to your Telegram bot. Bot should reply "Welcome to FlightTracker Bot!..." and begin the onboarding flow.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add Telegram webhook endpoint to FastAPI"
```
