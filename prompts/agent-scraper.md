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
