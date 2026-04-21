from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Session(Base):
    __tablename__ = "sessions"
    chat_id = Column(String, primary_key=True)
    platform = Column(String, default="telegram")
    step = Column(Integer, default=0)
    temp_data = Column(Text, default="{}")
    last_active = Column(DateTime, default=datetime.utcnow)

class Tracker(Base):
    __tablename__ = "trackers"
    tracker_id = Column(String, primary_key=True)
    chat_id = Column(String, nullable=False)
    platform = Column(String, default="telegram")
    from_airport = Column(String, nullable=False)
    to_airport = Column(String, nullable=False)
    travel_date = Column(String, nullable=False)
    return_date = Column(String, default="ONEWAY")
    passengers = Column(Integer, default=1)
    check_nearby = Column(Boolean, default=False)
    initial_price = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    lowest_price = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    tracking_since = Column(DateTime, default=datetime.utcnow)
    alert_threshold_percent = Column(Float, default=10.0)
    alert_threshold_fixed = Column(Float, default=0.0)
    email_alerts = Column(Boolean, default=False)
    email_address = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    status = Column(String, default="active")
    currency = Column(String, default="CAD")
    price_history = relationship("PriceHistory", back_populates="tracker")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tracker_id = Column(String, ForeignKey("trackers.tracker_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    airline = Column(String, nullable=True)
    flight_numbers = Column(String, nullable=True)
    tracker = relationship("Tracker", back_populates="price_history")
