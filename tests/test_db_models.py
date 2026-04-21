import pytest
from datetime import datetime
from db.models import Session, Tracker, PriceHistory


def test_create_session(db):
    s = Session(chat_id="123", platform="telegram", step=0, temp_data="{}")
    db.add(s)
    db.commit()
    result = db.query(Session).filter_by(chat_id="123").first()
    assert result.step == 0
    assert result.platform == "telegram"


def test_create_tracker(db):
    t = Tracker(
        tracker_id="abc-123",
        chat_id="123",
        from_airport="YYZ",
        to_airport="BOM",
        travel_date="2026-06-01",
    )
    db.add(t)
    db.commit()
    result = db.query(Tracker).filter_by(tracker_id="abc-123").first()
    assert result.from_airport == "YYZ"
    assert result.status == "active"
    assert result.currency == "CAD"


def test_create_price_history(db):
    t = Tracker(
        tracker_id="abc-456",
        chat_id="123",
        from_airport="YYZ",
        to_airport="BOM",
        travel_date="2026-06-01",
    )
    db.add(t)
    db.commit()
    ph = PriceHistory(
        tracker_id="abc-456",
        price=850.0,
        airline="Air Canada",
        flight_numbers="AC872",
    )
    db.add(ph)
    db.commit()
    result = db.query(PriceHistory).filter_by(tracker_id="abc-456").first()
    assert result.price == 850.0
    assert result.airline == "Air Canada"
    assert len(t.price_history) == 1
