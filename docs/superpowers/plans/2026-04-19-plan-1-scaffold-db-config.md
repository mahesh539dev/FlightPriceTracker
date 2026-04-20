# Plan 1: Project Scaffold, DB Models, Config

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the Python project skeleton with SQLite database models, config loading, and a passing test suite baseline.

**Architecture:** FastAPI app with SQLAlchemy 2.x ORM on SQLite. Config loaded from `.env` via python-dotenv. All models defined in `db/models.py` with a shared session factory in `db/database.py`.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, SQLite, python-dotenv, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Create | All Python dependencies |
| `.env.example` | Create | Template for required env vars |
| `config.py` | Create | Load and expose env vars |
| `db/__init__.py` | Create | Package marker |
| `db/database.py` | Create | Engine, session factory, `init_db()` |
| `db/models.py` | Create | SQLAlchemy ORM models: Session, Tracker, PriceHistory |
| `main.py` | Create | FastAPI app entry point, calls `init_db()` on startup |
| `tests/__init__.py` | Create | Package marker |
| `tests/conftest.py` | Create | Pytest fixtures: in-memory SQLite DB, test client |
| `tests/test_db_models.py` | Create | Tests for model creation and relationships |

---

### Task 1: Create requirements.txt and install dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
python-dotenv==1.0.1
python-telegram-bot==20.8
playwright==1.44.0
playwright-stealth==1.0.6
apscheduler==3.10.4
twilio==9.0.5
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.26.0
beautifulsoup4==4.12.3
```

- [ ] **Step 2: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: All packages install without errors. `playwright install chromium` downloads Chromium browser.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add requirements.txt"
```

---

### Task 2: Create config.py and .env.example

**Files:**
- Create: `config.py`
- Create: `.env.example`

- [ ] **Step 1: Write .env.example**

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_URL=https://your-ngrok-url/webhook
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

- [ ] **Step 2: Write config.py**

```python
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DATABASE_URL = "sqlite:///./flight_tracker.db"
```

- [ ] **Step 3: Copy .env.example to .env and fill in real values**

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

- [ ] **Step 4: Commit**

```bash
git add config.py .env.example
git commit -m "feat: add config and env template"
```

---

### Task 3: Create DB models

**Files:**
- Create: `db/__init__.py`
- Create: `db/database.py`
- Create: `db/models.py`

- [ ] **Step 1: Write db/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write db/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from db.models import Session, Tracker, PriceHistory  # noqa: F401
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Write db/models.py**

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add db/
git commit -m "feat: add SQLAlchemy models for Session, Tracker, PriceHistory"
```

---

### Task 4: Write and run DB model tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db_models.py`

- [ ] **Step 1: Write tests/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write tests/conftest.py**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
```

- [ ] **Step 3: Write failing tests**

```python
# tests/test_db_models.py
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
```

- [ ] **Step 4: Run tests — expect FAIL (models not imported yet)**

```bash
pytest tests/test_db_models.py -v
```

Expected: 3 tests pass (models already written in Task 3 — verify all 3 PASS)

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: add DB model tests"
```

---

### Task 5: Create main.py entry point

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write main.py**

```python
from fastapi import FastAPI
from db.database import init_db

app = FastAPI(title="Flight Price Tracker")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: Run the server**

```bash
python main.py
```

Expected: Server starts on port 8000. `GET http://localhost:8000/health` returns `{"status": "ok"}`. SQLite file `flight_tracker.db` is created.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add FastAPI entry point with DB init on startup"
```
