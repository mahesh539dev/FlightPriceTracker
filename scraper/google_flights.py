import asyncio
import re
import json
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

def parse_google_flights_api_response(response_text: str) -> dict | None:
    """
    Parse the Google Flights API response to extract flight prices and airlines.

    The response format:
    )]'
    [length_indicator]
    [["wrb.fr", null, "[flight_data_as_string]", ...], ...]

    The flight_data_as_string contains the actual flight offers with prices.
    """
    try:
        # Google Flights API responses start with )]}'
        if not response_text.startswith(")]}'"):
            return None

        # Remove the security prefix
        response_text = response_text[4:].strip()

        # Split by newlines to get the length and JSON
        lines = response_text.split('\n', 1)
        if len(lines) < 2:
            return None

        # The first line is the JSON length indicator, second line is the JSON
        json_str = lines[1]

        # Parse the first JSON object (before any newline separators)
        # Split on newline to handle multiple JSON objects
        first_json = json_str.split('\n')[0]
        data = json.loads(first_json)

        # Navigate the nested structure to find flight data
        if not isinstance(data, list) or len(data) < 1:
            return None

        wrapper = data[0]
        if not isinstance(wrapper, list) or len(wrapper) < 3:
            return None

        # The third element (index 2) contains the flight data as a string
        flight_data_str = wrapper[2]
        if not isinstance(flight_data_str, str):
            return None

        # Extract prices from the flight data
        # Pattern: prices appear as 4-digit numbers followed by ",digit,null,false"
        # Example: ,1065,2,null,false or ,1550,2,null,false
        price_matches = re.findall(r',(\d{4}),\d,null,false', flight_data_str)

        if not price_matches:
            # Fallback: look for 4-digit numbers in reasonable price ranges
            all_numbers = re.findall(r',(\d{3,5}),', flight_data_str)
            # Filter for prices (typically 900-5000 for international flights)
            price_matches = [n for n in all_numbers if 900 <= int(n) <= 5000]

        if not price_matches:
            return None

        # Get the cheapest price
        prices = sorted(list(set(map(int, price_matches))))
        cheapest_price = prices[0]

        # Extract airline codes
        # Pattern: "AIRLINECODE",[flight info...]
        airline_matches = re.findall(r'"([A-Z]{2})"\s*,\s*\[', flight_data_str)
        airline = airline_matches[0] if airline_matches else "Unknown"

        # Try to find airline name (often follows the code)
        airline_name_pattern = rf'"{airline}"\s*,\s*\["([^"]+)"'
        airline_name_match = re.search(airline_name_pattern, flight_data_str)
        airline_name = airline_name_match.group(1) if airline_name_match else airline

        return {
            "price": float(cheapest_price),
            "airline": airline_name,
            "flight_numbers": "",  # Flight numbers are harder to extract from this format
            "currency": "CAD",
        }

    except (json.JSONDecodeError, IndexError, TypeError, KeyError, AttributeError):
        return None
    except Exception:
        return None

async def scrape_google_flights(
    origin: str,
    destination: str,
    date_from: str,
    date_to: str | None = None,
    passengers: int = 1,
) -> dict | None:
    """
    Scrape flight prices from Google Flights using API response interception.

    Uses Playwright to load the page and intercept the FlightsFrontendService API
    response, then parses it to extract price and airline information.

    Falls back to DOM parsing if API parsing fails.
    """
    url = build_google_flights_url(origin, destination, date_from, date_to, passengers)

    captured_response = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # Intercept API responses to extract flight data
        async def capture_response(response):
            nonlocal captured_response
            if "FlightsFrontendService" in response.url and captured_response is None:
                try:
                    captured_response = await response.text()
                except:
                    pass

        page.on("response", capture_response)

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except:
            await browser.close()
            return None

        # Wait for price results to render (DOM parsing fallback)
        try:
            await page.wait_for_selector('[data-testid="offer-listing"]', timeout=10000)
        except:
            pass  # Results might have loaded via API even if DOM selector times out

        # Try to parse API response first
        if captured_response:
            result = parse_google_flights_api_response(captured_response)
            if result:
                await browser.close()
                return result

        # Fallback to DOM parsing if API parsing fails
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
    """
    Synchronous wrapper for scraping Google Flights.

    Args:
        origin: Airport IATA code (e.g., 'YYZ')
        destination: Airport IATA code (e.g., 'BOM')
        date_from: Travel date in YYYY-MM-DD format
        date_to: Return date in YYYY-MM-DD format or 'ONEWAY' for one-way flights
        passengers: Number of adult passengers (default 1)

    Returns:
        dict with keys: price (float), airline (str), flight_numbers (str), currency (str)
        or None if no flights found
    """
    return asyncio.run(scrape_google_flights(origin, destination, date_from, date_to, passengers))
