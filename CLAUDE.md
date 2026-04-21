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
