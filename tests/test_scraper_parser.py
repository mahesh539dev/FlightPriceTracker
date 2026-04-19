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
