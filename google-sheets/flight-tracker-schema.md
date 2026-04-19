# Flight Tracker - Google Sheets Schema

## Tab 1: Sessions

Stores conversation state for each user.

| Column | Type | Description |
|--------|------|-------------|
| chat_id | String | Telegram or WhatsApp user ID (primary key) |
| platform | String | "telegram" or "whatsapp" |
| step | Number | Current step in onboarding (0-10) |
| temp_data | JSON String | Temporary storage for answers during onboarding |
| last_active | Timestamp | Last message received time |

### temp_data JSON structure:
```json
{
  "email_alerts": "YES" | "NO",
  "email_address": "user@gmail.com",
  "from_airport": "YYZ",
  "to_airport": "BOM",
  "travel_date": "2024-12-15",
  "return_date": "2024-12-22" | "ONEWAY",
  "passengers": "2",
  "check_nearby": "YES" | "NO",
  "alert_threshold_type": "1" | "2" | "3" | "4",
  "alert_threshold_value": "10" | "50"
}
```

---

## Tab 2: Tracker

Stores active flight price tracking configurations.

| Column | Type | Description |
|--------|------|-------------|
| tracker_id | String | UUID - unique identifier for this tracker |
| chat_id | String | User's Telegram/WhatsApp ID |
| platform | String | "telegram" or "whatsapp" |
| from_airport | String | Origin IATA code (e.g., YYZ) |
| to_airport | String | Destination IATA code (e.g., BOM) |
| travel_date | Date | Departure date (YYYY-MM-DD) |
| return_date | Date | Return date (YYYY-MM-DD) or "ONEWAY" |
| passengers | Number | Number of adult passengers |
| check_nearby | Boolean | TRUE = check nearby airports |
| initial_price | Number | Price when tracking started |
| last_price | Number | Most recent price fetched |
| lowest_price | Number | Lowest price seen since tracking started |
| last_checked | Timestamp | When price was last fetched |
| tracking_since | Date | When tracking was activated |
| alert_threshold_percent | Number | Percentage drop threshold (e.g., 10 for 10%) |
| alert_threshold_fixed | Number | Fixed dollar drop threshold (e.g., 50 for $50) |
| email_alerts | Boolean | TRUE = send email alerts |
| email_address | String | User's email for alerts |
| whatsapp_number | String | WhatsApp number with country code (e.g., +14161234567) |
| status | String | "active" or "stopped" |
| currency | String | Currency code (CAD, USD, INR, etc.) |

---

## Tab 3: PriceHistory

Stores historical price data for trend analysis.

| Column | Type | Description |
|--------|------|-------------|
| tracker_id | String | References Tracker tab |
| timestamp | Timestamp | When price was recorded |
| price | Number | Price at this moment |
| airline | String | Carrier name (e.g., "Air Canada") |
| flight_numbers | String | Comma-separated flight numbers (e.g., "AC872, AI101") |

---

## Setup Instructions

1. Create a new Google Sheet named "FlightTracker"
2. Rename Sheet1 to "Sessions"
3. Create "Tracker" sheet
4. Create "PriceHistory" sheet
5. Add all column headers to each sheet as shown above
6. Share the sheet with your Google Service Account email
7. Copy the Sheet ID from the URL for your config

---

## Example Data

### Sessions Tab:
| chat_id | platform | step | temp_data | last_active |
|---------|----------|------|-----------|-------------|
| 123456789 | telegram | 10 | {} | 2024-11-20 10:30:00 |

### Tracker Tab:
| tracker_id | chat_id | from_airport | to_airport | travel_date | status |
|------------|---------|--------------|------------|-------------|--------|
| abc123... | 123456789 | YYZ | BOM | 2024-12-15 | active |

### PriceHistory Tab:
| tracker_id | timestamp | price | airline | flight_numbers |
|------------|-----------|-------|--------|---------------|
| abc123... | 2024-11-20 10:30:00 | 850.00 | Air Canada | AC872 |