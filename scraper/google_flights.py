import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

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
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
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
