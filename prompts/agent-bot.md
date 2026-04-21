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
