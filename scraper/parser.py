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
