# Flight Price Tracker Bot — Claude Code Instructions

## Project Overview

A fully automated flight price tracking system built on **n8n** that includes:
- Telegram/WhatsApp conversational bot (onboarding + commands)
- Hourly price monitoring via Amadeus Flight Offers API
- Daily digest summaries
- Multi-channel alerts: Telegram, WhatsApp (Twilio), Gmail

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Automation Engine | n8n (self-hosted recommended) |
| Conversational Bot | Telegram Bot API (webhook-based) |
| WhatsApp | Twilio WhatsApp API |
| Flight Prices | Amadeus Flight Offers Search API v2 |
| Database | Google Sheets (3 tabs: Sessions, Tracker, PriceHistory) |
| Email | Gmail OAuth2 via n8n |

---

## Directory Structure

```
flight-price-tracker/
├── n8n-workflows/
│   ├── workflow-1-conversation-bot.json
│   ├── workflow-2-hourly-price-monitor.json
│   └── workflow-3-daily-digest.json
├── google-sheets/
│   └── flight-tracker-schema.md
├── config/
│   └── env-variables.md
├── prompts/
│   └── bot-conversation-messages.md
└── README.md
```

---

## Architecture: 3 n8n Workflows

### Workflow 1 — Conversational Bot (Telegram + WhatsApp)

**Trigger:** Telegram Trigger node (webhook on every message)

**State Machine** stored in Google Sheets `Sessions` tab:
- `step_0` → Welcome + ask email alerts (YES/NO)
- `step_1` → If YES: collect Gmail address
- `step_2` → Ask origin airport/city (e.g. YYZ or Toronto)
- `step_3` → Ask destination airport/city (e.g. BOM or Mumbai)
- `step_4` → Ask travel date (YYYY-MM-DD)
- `step_5` → Ask return date (YYYY-MM-DD or ONEWAY)
- `step_6` → Ask number of adult passengers
- `step_7` → Ask nearby airports (YES/NO)
- `step_8` → Ask alert threshold: 1) 5%  2) 10%  3) 15%  4) Custom ($amount)
- `step_9` → Confirm details + trigger first Amadeus price search + write to Tracker
- `step_10` → ACTIVE: listen for `/stop` or `/status` commands

**Node Flow:**
```
[Telegram Trigger]
  → [Google Sheets - Read Session by chat_id]
  → [Switch Node - current step?]
      step_0..8 → [Set Node: save answer] → [Update Google Sheets] → [IF step_9?]
                    YES → [Amadeus OAuth] → [Amadeus Flight Search] → [Format Results]
                          → [Google Sheets: Write Tracker row] → [Telegram: Send prices]
                          → [IF email=YES → Gmail: confirmation] → [Update step to 10]
                    NO  → [Telegram: Send next question]
      step_10 → [Switch: /stop → Mark inactive | /status → Fetch & reply]
```

**Amadeus API Call (step 9):**
- Endpoint: `GET https://test.api.amadeus.com/v2/shopping/flight-offers`
- Params: `originLocationCode`, `destinationLocationCode`, `departureDate`, `returnDate` (omit if ONEWAY), `adults`, `max=5`, `currencyCode=CAD`
- Auth: OAuth2 via `POST https://test.api.amadeus.com/v1/security/oauth2/token` with `grant_type=client_credentials`

**Nearby Airport Logic (JavaScript Code Node):**
```javascript
const airportGroups = {
  "YYZ": ["YYZ", "YTZ", "YHM", "YKF"],
  "YVR": ["YVR", "YXX"],
  "JFK": ["JFK", "LGA", "EWR"],
  "LHR": ["LHR", "LGW", "STN", "LTN"],
  "BOM": ["BOM", "PNQ"],
};
const userInput = $json.from_airport.toUpperCase();
const matchedCode = Object.keys(airportGroups).find(k =>
  userInput.includes(k) || userInput.includes("TORONTO") // extend city matching
);
return airportGroups[matchedCode] || [userInput];
// Run separate Amadeus calls per code, merge/sort by price
```

---

### Workflow 2 — Hourly Price Monitor

**Trigger:** Schedule Trigger — every 1 hour (`cron: 0 * * * *`)

**Node Flow:**
```
[Schedule Trigger - 1hr]
  → [Google Sheets: Read Tracker tab, filter status="active"]
  → [Split In Batches: batch size 1]
  → [Amadeus OAuth] → [Amadeus Flight Search per row]
  → [Code Node: Extract cheapest price]
  → [IF: current_price < last_price * (1 - threshold/100)]
      YES → [IF: tracking_days >= 3 AND current_price < lowest_ever]
              YES → [Telegram: BEST DEAL ALERT]
              NO  → [Telegram: Price Drop Alert]
            [IF email=YES → Gmail alert]
            [IF whatsapp set → Twilio WhatsApp alert]
            [Google Sheets: Update last_price, lowest_price, last_checked, append PriceHistory]
      NO  → [Google Sheets: Update last_checked only]
  → [Continue to next row]
```

**Price Drop Logic (JavaScript Code Node):**
```javascript
const lastPrice = parseFloat($json.last_price);
const currentPrice = parseFloat($json.current_price);
const thresholdPercent = parseFloat($json.alert_threshold_percent);
const thresholdFixed = parseFloat($json.alert_threshold_fixed || 0);
const lowestPrice = parseFloat($json.lowest_price);
const trackingSince = new Date($json.tracking_since);
const now = new Date();
const daysDiff = Math.floor((now - trackingSince) / (1000 * 60 * 60 * 24));
const percentDrop = ((lastPrice - currentPrice) / lastPrice) * 100;
const isSignificantDrop = percentDrop >= thresholdPercent || (currentPrice <= lastPrice - thresholdFixed);
const isNewLowest = currentPrice < lowestPrice;
const isMatureDeal = daysDiff >= 3 && isNewLowest;
return { currentPrice, percentDrop: percentDrop.toFixed(2), isSignificantDrop, isNewLowest, isMatureDeal, daysDiff };
```

---

### Workflow 3 — Daily Summary Digest

**Trigger:** Schedule Trigger — daily at 9:00 AM (`cron: 0 9 * * *`)

**Node Flow:**
```
[Schedule Trigger - 9AM]
  → [Google Sheets: Read Tracker tab, filter status="active"]
  → [Code Node: Group rows by chat_id]
  → [Loop over each unique user]
      → [Amadeus search for each route of this user]
      → [Code Node: Format multi-route digest message]
      → [Telegram: Send digest]
      → [IF email=YES → Gmail: daily email]
      → [IF whatsapp=YES → Twilio WhatsApp: digest]
```

**Digest Format:**
```
Daily Flight Price Report – {date}
──────────────────────────
✈ {from} → {to}
Today: {currency} {price} | Yesterday: {currency} {yesterday_price}
Lowest Ever: {currency} {lowest} | Tracking: {days} days
──────────────────────────
```

---

## Google Sheets Schema

### Tab 1: Sessions
| Column | Type | Description |
|--------|------|-------------|
| chat_id | String | Telegram or WhatsApp user ID |
| platform | String | "telegram" or "whatsapp" |
| step | Number | Current step 0-10 |
| temp_data | JSON String | Partial answers during onboarding |
| last_active | Timestamp | Last message time |

### Tab 2: Tracker
| Column | Type | Description |
|--------|------|-------------|
| tracker_id | String | UUID (auto-generated) |
| chat_id | String | User's Telegram/WhatsApp ID |
| platform | String | "telegram" or "whatsapp" |
| from_airport | String | IATA code e.g. YYZ |
| to_airport | String | IATA code e.g. BOM |
| travel_date | Date | YYYY-MM-DD |
| return_date | Date | YYYY-MM-DD or "ONEWAY" |
| passengers | Number | Adult count |
| check_nearby | Boolean | TRUE/FALSE |
| initial_price | Number | Price at first search |
| last_price | Number | Most recently fetched price |
| lowest_price | Number | Lowest price seen so far |
| last_checked | Timestamp | Last Amadeus fetch time |
| tracking_since | Date | When tracking started |
| alert_threshold_percent | Number | e.g. 10 for 10% |
| alert_threshold_fixed | Number | e.g. 50 for $50 drop |
| email_alerts | Boolean | TRUE/FALSE |
| email_address | String | user@gmail.com |
| whatsapp_number | String | +14161234567 |
| status | String | "active" or "stopped" |
| currency | String | CAD, USD, INR, etc. |

### Tab 3: PriceHistory
| Column | Type | Description |
|--------|------|-------------|
| tracker_id | String | References Tracker tab |
| timestamp | Timestamp | When price was fetched |
| price | Number | Price at this moment |
| airline | String | Carrier name |
| flight_numbers | String | e.g. "AC872, AI101" |

---

## Environment Variables (n8n Credentials)

```
AMADEUS_API_KEY           = your-amadeus-api-key
AMADEUS_API_SECRET        = your-amadeus-api-secret
AMADEUS_BASE_URL          = https://test.api.amadeus.com

TELEGRAM_BOT_TOKEN        = your-telegram-bot-token
TELEGRAM_WEBHOOK_URL      = https://your-n8n-instance.com/webhook/telegram

TWILIO_ACCOUNT_SID        = your-twilio-sid
TWILIO_AUTH_TOKEN         = your-twilio-auth-token
TWILIO_WHATSAPP_FROM      = whatsapp:+14155238886

GMAIL_OAUTH_CLIENT_ID     = your-gmail-oauth-id
GMAIL_OAUTH_CLIENT_SECRET = your-gmail-oauth-secret

GOOGLE_SHEETS_ID          = your-google-sheet-id
GOOGLE_SHEETS_CREDENTIALS = your-service-account-json
```

---

## Message Templates

### Welcome (step_0)
```
Welcome to FlightTracker Bot!
I'll monitor flight prices for you and alert you when they drop.

First — do you want to receive email alerts?
Reply: YES or NO
```

### Confirmation (step_9)
```
Got it! Here's your tracking setup:
✈ {from} → {to}
Depart: {travel_date} | Return: {return_date}
{passengers} Adult(s)
Alert when price drops by {threshold}
Email alerts: {email_alerts} ({email_address})
Nearby airports: {check_nearby}

Searching for current prices...
```

### Price Drop Alert
```
Price Drop Alert!
✈ {from} → {to}
{travel_date}
Was: {currency} {last_price}
Now: {currency} {current_price} (down {percent_drop}%)
Airline: {airline}
Book quickly — prices can change!
```

### Best Deal Alert (3+ days tracking)
```
BEST PRICE in {days} Days of Tracking!
✈ {from} → {to}
{travel_date}
Lowest Ever: {currency} {lowest_price} (was {currency} {initial_price} when you started)
That's a saving of {currency} {saving}! (down {percent_drop}%)
This is the lowest we've seen — act fast!
```

---

## Implementation Phases

| Phase | Task | Duration |
|-------|------|----------|
| Phase 1 | Setup credentials (Telegram, Amadeus, Google Sheets, Twilio, Gmail OAuth) | Day 1 |
| Phase 2 | Build Workflow 1: Conversation Bot | Days 2-3 |
| Phase 3 | Build Workflow 2: Hourly Price Monitor | Day 4 |
| Phase 4 | Build Workflow 3: Daily Digest | Day 5 |
| Phase 5 | Testing | Day 6 |
| Phase 6 | Deployment (switch Amadeus to production, deploy n8n to VPS) | Day 7 |

---

## Key Implementation Rules

1. **Always get Amadeus OAuth token first** before any flight search call — tokens expire and must be fetched fresh per workflow execution.
2. **Batch size must be 1** in Workflow 2's Split In Batches node to avoid API rate limit issues.
3. **Nearby airports**: Run separate Amadeus calls for each airport code, then merge and sort all results by price before presenting.
4. **State machine**: Always read the Sessions tab first to determine current step. Never assume step — always look it up.
5. **Price history**: Append every price fetch to PriceHistory tab (not just on drops) to enable trend analysis.
6. **Currency**: Default to CAD; allow user to specify during onboarding or default from their locale.
7. **Error handling**: If Amadeus returns no results, reply to user: "No flights found for this route/date. Try different dates."
8. **WhatsApp**: Treat as optional — only send if `whatsapp_number` is set in the Tracker row.
9. **n8n self-hosted**: Recommend Railway or Render for zero-cost VPS hosting during development.
10. **Test first**: Always use `test.api.amadeus.com` during development. Switch to `api.amadeus.com` only after full testing.

---

## Cost Estimates

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| Amadeus API (Test) | Unlimited | $0 |
| Amadeus API (Production) | 500 calls/month | $0–$10 |
| Telegram Bot API | Unlimited | $0 |
| Twilio WhatsApp | $0 incoming | ~$1–$5 per 100 alerts |
| Gmail via n8n | Free | $0 |
| Google Sheets API | Free | $0 |
| n8n Cloud Starter | 5,000 executions | $20/month |
| n8n Self-hosted (VPS) | — | ~$5–$10/month |

**Total: ~$5–$30/month** depending on volume and hosting choice.
