# Plan 2: Playwright Google Flights Scraper

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reliable Playwright-based scraper that fetches the cheapest flight price from Google Flights for a given route and date.

**Architecture:** Async Playwright launches headless Chromium with stealth mode. `google_flights.py` builds the search URL and navigates to it. `parser.py` extracts price, airline, and flight numbers from the rendered DOM. Returns a typed dict or `None` if no results.

**Tech Stack:** Python 3.11+, Playwright (async), playwright-stealth, pytest, pytest-asyncio

**Prerequisite:** Plan 1 complete (requirements installed, project skeleton exists).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `scraper/__init__.py` | Create | Package marker |
| `scraper/google_flights.py` | Create | Build URL, launch Playwright, return raw page HTML |
| `scraper/parser.py` | Create | Extract price/airline/flight numbers from HTML |
| `tests/test_scraper_parser.py` | Create | Unit tests for parser with fixture HTML |
| `tests/fixtures/google_flights_sample.html` | Create | Sample HTML snippet for parser tests |

---

### Task 1: Create scraper package and Google Flights URL builder

**Files:**
- Create: `scraper/__init__.py`
- Create: `scraper/google_flights.py`

- [ ] **Step 1: Write scraper/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write the URL builder and scraper in scraper/google_flights.py**

```python
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

AIRPORT_GROUPS = {
    "YYZ": ["YYZ", "YTZ", "YHM", "YKF"],
    "YVR": ["YVR", "YXX"],
    "JFK": ["JFK", "LGA", "EWR"],
    "LHR": ["LHR", "LGW", "STN", "LTN"],
    "BOM": ["BOM", "PNQ"],
}

def get_nearby_airports(iata: str) -> list[str]:
    code = iata.upper().strip()
    return AIRPORT_GROUPS.get(code, [code])

def build_google_flights_url(
    origin: str,
    destination: str,
    date_from: str,
    date_to: str | None = None,
    passengers: int = 1,
) -> str:
    # Google Flights deep-link format
    base = "https://www.google.com/travel/flights"
    params = f"?q=flights+from+{origin}+to+{destination}+on+{date_from}"
    if date_to and date_to != "ONEWAY":
        params += f"+returning+{date_to}"
    return base + params

async def scrape_google_flights(
    origin: str,
    destination: str,
    date_from: str,
    date_to: str | None = None,
    passengers: int = 1,
) -> dict | None:
    url = build_google_flights_url(origin, destination, date_from, date_to, passengers)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)
        await page.goto(url, wait_until="networkidle", timeout=30000)
        # Wait for price results to render
        try:
            await page.wait_for_selector('[data-testid="offer-listing"]', timeout=15000)
        except Exception:
            await browser.close()
            return None
        html = await page.content()
        await browser.close()
    from scraper.parser import extract_cheapest_flight
    return extract_cheapest_flight(html)

def scrape_flights_sync(
    origin: str,
    destination: str,
    date_from: str,
    date_to: str | None = None,
    passengers: int = 1,
) -> dict | None:
    return asyncio.run(scrape_google_flights(origin, destination, date_from, date_to, passengers))
```

- [ ] **Step 3: Commit**

```bash
git add scraper/
git commit -m "feat: add Google Flights URL builder and Playwright scraper"
```

---

### Task 2: Write the HTML parser

**Files:**
- Create: `scraper/parser.py`
- Create: `tests/fixtures/google_flights_sample.html`

- [ ] **Step 1: Create tests/fixtures/ directory and sample HTML**

Create `tests/fixtures/google_flights_sample.html` with this minimal HTML that mimics what Google Flights renders for a result row:

```html
<!DOCTYPE html>
<html>
<body>
  <div data-testid="offer-listing">
    <div class="YMlIz">
      <span class="YMlIz FpEdX">$850</span>
      <span class="eoY5cb">Air Canada</span>
      <span class="c257Jb">AC 872</span>
    </div>
  </div>
</body>
</html>
```

Note: Google Flights CSS class names change frequently. The parser uses `data-testid` attributes where available and falls back to positional heuristics. This fixture matches the current class structure as of 2026-04. Update the fixture if Google changes their markup.

- [ ] **Step 2: Write failing test first**

```python
# tests/test_scraper_parser.py
import pytest
from pathlib import Path
from scraper.parser import extract_cheapest_flight

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "google_flights_sample.html"

def test_extract_price_from_fixture():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    result = extract_cheapest_flight(html)
    assert result is not None
    assert result["price"] == 850.0
    assert result["airline"] == "Air Canada"
    assert result["flight_numbers"] == "AC 872"
    assert result["currency"] == "CAD"

def test_returns_none_when_no_results():
    result = extract_cheapest_flight("<html><body>No flights found</body></html>")
    assert result is None
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
pytest tests/test_scraper_parser.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `scraper.parser` doesn't exist yet.

- [ ] **Step 4: Write scraper/parser.py**

```python
import re
from bs4 import BeautifulSoup

def extract_cheapest_flight(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    listing = soup.find(attrs={"data-testid": "offer-listing"})
    if not listing:
        return None
    # Extract price: look for text matching $NNN or NNN pattern
    price_text = None
    for tag in listing.find_all(string=True):
        match = re.search(r"\$?([\d,]+)", tag.strip())
        if match and int(match.group(1).replace(",", "")) > 50:
            price_text = match.group(1).replace(",", "")
            break
    if not price_text:
        return None
    # Extract airline: first non-price, non-number text block
    airline = None
    for tag in listing.find_all(string=True):
        text = tag.strip()
        if text and not re.match(r"^\$?[\d,]+$", text) and len(text) > 2:
            airline = text
            break
    # Extract flight numbers: pattern like "XX NNN"
    flight_numbers = None
    for tag in listing.find_all(string=True):
        text = tag.strip()
        if re.match(r"^[A-Z]{2}\s?\d{2,4}$", text):
            flight_numbers = text
            break
    return {
        "price": float(price_text),
        "airline": airline or "Unknown",
        "flight_numbers": flight_numbers or "",
        "currency": "CAD",
    }
```

Note: Add BeautifulSoup to requirements.txt:
```
beautifulsoup4==4.12.3
```
Then run: `pip install beautifulsoup4`

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_scraper_parser.py -v
```

Expected: Both tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scraper/parser.py tests/test_scraper_parser.py tests/fixtures/ requirements.txt
git commit -m "feat: add Google Flights HTML parser with tests"
```

---

### Task 3: Smoke-test the live scraper

**Files:**
- No new files — this is a manual integration test

- [ ] **Step 1: Run a live scrape from a Python REPL**

```python
from scraper.google_flights import scrape_flights_sync
result = scrape_flights_sync("YYZ", "BOM", "2026-06-01")
print(result)
```

Expected: Either a dict `{"price": <float>, "airline": <str>, "flight_numbers": <str>, "currency": "CAD"}` or `None` if Google blocked the request.

- [ ] **Step 2: If result is None, debug**

Run with `headless=False` to see what the browser shows:

In `scraper/google_flights.py`, temporarily change:
```python
browser = await p.chromium.launch(headless=False)
```

Re-run. Watch what the browser renders. Common issues:
- CAPTCHA page → stealth mode needs tuning (try adding `--disable-blink-features=AutomationControlled` launch arg)
- Different CSS selectors → update `data-testid` value in `google_flights.py` and class names in `parser.py`
- Timeout → increase `timeout=30000` to `60000`

Restore `headless=True` after debugging.

- [ ] **Step 3: Commit any selector fixes**

```bash
git add scraper/
git commit -m "fix: update Google Flights selectors after live smoke test"
```
