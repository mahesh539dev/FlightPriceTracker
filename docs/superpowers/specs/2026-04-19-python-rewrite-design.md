# Flight Price Tracker — Python Rewrite Design Spec
Date: 2026-04-19

## Context

The original architecture used n8n (a no-code automation engine) with the Kiwi.com Tequila API for flight pricing. The Kiwi API proved unavailable or too costly. Rather than finding another paid flight API, the decision is to rewrite the entire application in Python using web scraping (Playwright on Google Flights) as the pricing data source. This eliminates API costs entirely and gives full control over the stack.

## Goals

- Replace n8n workflows with a single Python application
- Replace flight pricing API with Playwright-based Google Flights scraper
- Replace Google Sheets with SQLite (local, zero-cost, no API quota)
- Retain Telegram bot as the primary user interface
- Add a simple local web dashboard for monitoring
- Retain Gmail and Twilio WhatsApp as optional alert channels

## Architecture

### Entry Point

`main.py` starts two things concurrently:
1. FastAPI server (Uvicorn) — handles Telegram webhook + web dashboard routes
2. APScheduler — runs hourly price monitor and 9AM daily digest jobs in-process

### Components

#### `bot/` — Telegram State Machine
- `handlers.py`: receives webhook POST from Telegram, reads current step from SQLite Sessions table, routes to the correct handler, saves answer, advances step
- `messages.py`: all message templates (welcome, questions, confirmations, alerts, digest format)
- Steps 0–9: onboarding flow (email, origin, destination, dates, passengers, nearby airports, threshold)
- Step 9: triggers first scrape, writes Tracker row, sends confirmation
- Step 10: listens for `/stop` and `/status` commands

#### `scraper/` — Google Flights Playwright Scraper
- `google_flights.py`: launches Playwright browser (headless Chromium), navigates to Google Flights search URL with query params (origin, destination, date, passengers), waits for price results to render
- `parser.py`: extracts cheapest price, airline name, and flight numbers from the rendered DOM
- Stealth mode via `playwright-stealth` to reduce bot detection
- Returns: `{price: float, airline: str, flight_numbers: str, currency: str}`
- On no results: returns `None` — callers send "No flights found" message

#### `scheduler/` — Background Jobs
- `price_monitor.py`: hourly APScheduler job — reads all `status="active"` Tracker rows, scrapes each route, computes price drop (percent and fixed), fires alerts if threshold exceeded, appends to PriceHistory, updates Tracker
- `daily_digest.py`: 9AM APScheduler job — groups active Tracker rows by `chat_id`, scrapes fresh prices, formats multi-route digest, sends via all configured channels

#### `db/` — SQLite Persistence
- `models.py`: SQLAlchemy ORM models for Sessions, Tracker, PriceHistory (same schema as current Google Sheets design)
- `database.py`: engine creation, session factory, `init_db()` called at startup

**Sessions table:** `chat_id`, `platform`, `step`, `temp_data` (JSON string), `last_active`

**Tracker table:** `tracker_id` (UUID), `chat_id`, `platform`, `from_airport`, `to_airport`, `travel_date`, `return_date`, `passengers`, `check_nearby`, `initial_price`, `last_price`, `lowest_price`, `last_checked`, `tracking_since`, `alert_threshold_percent`, `alert_threshold_fixed`, `email_alerts`, `email_address`, `whatsapp_number`, `status`, `currency`

**PriceHistory table:** `tracker_id` (FK), `timestamp`, `price`, `airline`, `flight_numbers`

#### `web/` — Local Dashboard
- `dashboard.py`: FastAPI routes
  - `GET /` — table of all tracked routes with current price, status, last checked
  - `GET /tracker/{id}` — price history as a simple HTML chart (Chart.js via CDN)
- No authentication (local machine only, not exposed publicly)

#### `alerts/` — Notification Channels
- `telegram.py`: sends messages via Bot API (HTTP POST)
- `gmail.py`: sends via Gmail SMTP with app password (no OAuth complexity)
- `whatsapp.py`: sends via Twilio REST API (only if `whatsapp_number` set)

#### `config.py`
Reads from `.env`:
```
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_URL
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
GMAIL_ADDRESS
GMAIL_APP_PASSWORD
```

### Nearby Airport Logic
Same as current design: a hardcoded dict maps major airports to nearby codes. If `check_nearby=True`, run one Playwright scrape per airport code, merge results, sort by price, take cheapest.

### Price Drop Logic
```python
percent_drop = (last_price - current_price) / last_price * 100
is_significant = percent_drop >= threshold_percent or (current_price <= last_price - threshold_fixed)
is_new_lowest = current_price < lowest_price
is_mature_deal = days_tracked >= 3 and is_new_lowest
```

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Bot SDK | python-telegram-bot v20 |
| Scraping | Playwright (async) + playwright-stealth |
| Scheduling | APScheduler 3.x |
| Database | SQLite + SQLAlchemy 2.x |
| Email | smtplib (stdlib) |
| WhatsApp | twilio SDK |
| Dashboard charts | Chart.js via CDN (no Python dep) |
| Config | python-dotenv |

## File Structure

```
flight-price-tracker/
├── main.py
├── config.py
├── requirements.txt
├── .env                        # not committed
├── CLAUDE.md                   # updated for Python project
├── bot/
│   ├── __init__.py
│   ├── handlers.py
│   └── messages.py
├── scraper/
│   ├── __init__.py
│   ├── google_flights.py
│   └── parser.py
├── scheduler/
│   ├── __init__.py
│   ├── price_monitor.py
│   └── daily_digest.py
├── db/
│   ├── __init__.py
│   ├── models.py
│   └── database.py
├── web/
│   ├── __init__.py
│   └── dashboard.py
└── alerts/
    ├── __init__.py
    ├── telegram.py
    ├── gmail.py
    └── whatsapp.py
```

## Verification

1. `python main.py` — server starts, APScheduler logs jobs registered
2. Set Telegram webhook: `curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>/webhook`
3. Message the bot — state machine advances step by step through onboarding
4. At step 9 — Playwright launches, scrapes Google Flights, returns price, bot confirms
5. Manually trigger `price_monitor.py` job — price compared, alert fires if threshold met
6. Visit `http://localhost:8000/` — dashboard shows tracked routes
7. Visit `http://localhost:8000/tracker/<id>` — price history chart renders
