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
