# Flight Price Tracker Bot — Build TODO

Agent instructions: Complete tasks in order. Each phase depends on the previous.
Mark tasks [x] as you complete them. Do NOT skip phases.

---

## PHASE 1 — Project Setup & Credentials (Day 1)

### 1.1 Create directory structure
- [ ] Create `n8n-workflows/` directory
- [ ] Create `google-sheets/` directory
- [ ] Create `config/` directory
- [ ] Create `prompts/` directory

### 1.2 Create config documentation files
- [ ] Create `config/env-variables.md` — list all required API keys with placeholder values and instructions to fill them in
- [ ] Create `google-sheets/flight-tracker-schema.md` — full column definitions for Sessions, Tracker, PriceHistory tabs
- [ ] Create `prompts/bot-conversation-messages.md` — all bot message templates (welcome, confirmation, price drop, best deal, daily digest)

### 1.3 External service setup (manual steps — document in README)
- [ ] Create `README.md` with step-by-step instructions for:
  - Creating a Telegram bot via @BotFather and setting the webhook URL
  - Registering on developers.amadeus.com and creating an app
  - Creating Google Sheet with 3 tabs (Sessions, Tracker, PriceHistory) and all columns
  - Enabling Google Sheets API + creating Service Account in Google Cloud Console
  - Setting up Twilio WhatsApp Sandbox (optional)
  - Configuring Gmail OAuth2 in n8n

---

## PHASE 2 — Workflow 1: Conversation Bot (Days 2-3)

### 2.1 Build workflow-1-conversation-bot.json
- [ ] **Node 1:** Telegram Trigger — webhook-based, fires on every message
- [ ] **Node 2:** Google Sheets Read — lookup chat_id in Sessions tab; if not found, create new row at step_0
- [ ] **Node 3:** Switch Node — 11 cases: step_0 through step_10

### 2.2 Implement each step branch
- [ ] **step_0:** Send welcome message; ask for email alerts (YES/NO)
- [ ] **step_1:** If YES → ask for Gmail address; if NO → skip to step_2
- [ ] **step_2:** Ask for origin airport/city
- [ ] **step_3:** Ask for destination airport/city
- [ ] **step_4:** Ask for travel date (YYYY-MM-DD)
- [ ] **step_5:** Ask for return date (YYYY-MM-DD or ONEWAY)
- [ ] **step_6:** Ask for number of adult passengers
- [ ] **step_7:** Ask if check nearby airports (YES/NO)
- [ ] **step_8:** Ask for alert threshold (1=5%, 2=10%, 3=15%, 4=Custom $amount)
- [ ] **step_9:** Confirm all details → trigger Amadeus search → write Tracker row → send prices → update to step_10

For each step (0-8):
- [ ] Set Node: extract and save answer to temp_data JSON
- [ ] Google Sheets Update: write answer to Sessions row
- [ ] Telegram Send: send next question message

### 2.3 Build Amadeus call at step_9
- [ ] HTTP Request Node 1: POST to Amadeus OAuth token endpoint; capture `access_token`
- [ ] Code Node: Build nearby airport array if check_nearby=YES (use airportGroups map from CLAUDE.md)
- [ ] HTTP Request Node 2: GET Amadeus Flight Offers Search with dynamic params (from/to/date/adults/max=5/currency)
- [ ] If nearby=YES: loop over airport codes, run separate calls, merge and sort results by price
- [ ] Code Node: Extract top 5 cheapest offers; format price list message
- [ ] Google Sheets Append: write full row to Tracker tab (generate UUID for tracker_id, set status="active", tracking_since=today)
- [ ] Google Sheets Append: write first price entry to PriceHistory tab
- [ ] Telegram Send: send formatted current prices + "Tracking active!" message
- [ ] IF Node: if email_alerts=YES → Gmail Send: confirmation email with current prices
- [ ] Google Sheets Update: set step=10 in Sessions tab

### 2.4 Build step_10 command handlers
- [ ] Switch Node: detect `/stop` or `/status` in message text
- [ ] `/stop` branch: Google Sheets Update — set status="stopped" in Tracker; Telegram Send: "Tracking stopped."
- [ ] `/status` branch: Google Sheets Read Tracker row → Amadeus fresh price fetch → Telegram Send: current price summary
- [ ] Default (unrecognized message): Telegram Send: "Tracking is active. Send /stop to stop or /status for latest prices."

### 2.5 Export and validate
- [ ] Export workflow as JSON to `n8n-workflows/workflow-1-conversation-bot.json`
- [ ] Test full conversation flow end-to-end in Telegram (all 10 steps)
- [ ] Test `/stop` command
- [ ] Test `/status` command

---

## PHASE 3 — Workflow 2: Hourly Price Monitor (Day 4)

### 3.1 Build workflow-2-hourly-price-monitor.json
- [ ] **Node 1:** Schedule Trigger — cron `0 * * * *` (every hour)
- [ ] **Node 2:** Google Sheets Read — all rows from Tracker tab where status="active"
- [ ] **Node 3:** IF Node — skip if no active rows (avoid empty loop errors)
- [ ] **Node 4:** Split In Batches — batch size: 1

### 3.2 Per-row price check loop
- [ ] HTTP Request: Amadeus OAuth token
- [ ] HTTP Request: Amadeus Flight Offers Search using stored from/to/date from current row
- [ ] Code Node: Extract cheapest price from response
- [ ] Code Node: Price drop logic (from CLAUDE.md) — calculate percentDrop, isSignificantDrop, isNewLowest, isMatureDeal, daysDiff

### 3.3 Alert branching
- [ ] IF Node: isSignificantDrop=true?
  - YES branch:
    - [ ] IF Node: isMatureDeal=true?
      - YES: Telegram Send — BEST DEAL ALERT message
      - NO: Telegram Send — standard Price Drop Alert message
    - [ ] IF Node: email_alerts=YES → Gmail Send: price drop email
    - [ ] IF Node: whatsapp_number is set → Twilio HTTP Request: WhatsApp message
    - [ ] Google Sheets Update: last_price, lowest_price (if new lowest), last_checked
    - [ ] Google Sheets Append: PriceHistory row with timestamp, price, airline, flight_numbers
  - NO branch:
    - [ ] Google Sheets Update: last_checked only

### 3.4 Export and validate
- [ ] Export workflow as JSON to `n8n-workflows/workflow-2-hourly-price-monitor.json`
- [ ] Test: manually trigger workflow with at least 1 active Tracker row
- [ ] Test price drop simulation: manually set last_price in sheet to a higher value → verify alert fires
- [ ] Test 3+ day best deal: set tracking_since to 4 days ago + lower current price → verify BEST DEAL message

---

## PHASE 4 — Workflow 3: Daily Digest (Day 5)

### 4.1 Build workflow-3-daily-digest.json
- [ ] **Node 1:** Schedule Trigger — cron `0 9 * * *` (9 AM daily)
- [ ] **Node 2:** Google Sheets Read — Tracker tab, filter status="active"
- [ ] **Node 3:** IF Node — skip if no active rows

### 4.2 Group and loop
- [ ] Code Node: Group all Tracker rows by chat_id into a map `{ chat_id: [rows] }`
- [ ] Loop Node: iterate over each unique user

### 4.3 Per-user digest
- [ ] For each route belonging to this user:
  - [ ] HTTP Request: Amadeus OAuth
  - [ ] HTTP Request: Amadeus Flight Search (fresh price)
  - [ ] Extract cheapest current price
- [ ] Code Node: Build multi-route digest message string (see template in CLAUDE.md)
- [ ] Telegram Send: digest to user's chat_id
- [ ] IF Node: email=YES → Gmail Send: daily digest email (HTML formatted)
- [ ] IF Node: whatsapp=YES → Twilio WhatsApp: digest message

### 4.4 Export and validate
- [ ] Export workflow as JSON to `n8n-workflows/workflow-3-daily-digest.json`
- [ ] Test: manually trigger workflow → verify multi-route digest message formatting
- [ ] Test: user with 2 routes → verify both appear in one digest message
- [ ] Test email and WhatsApp delivery

---

## PHASE 5 — Testing (Day 6)

- [ ] **End-to-end bot test:** Start fresh conversation → complete all 10 steps → verify Tracker row created
- [ ] **Price data accuracy:** Compare Amadeus response prices against amadeus.com website
- [ ] **Alert trigger test:** Simulate price drop in Tracker sheet → manually run Workflow 2 → confirm Telegram, WhatsApp, Gmail all receive alert
- [ ] **Stop command test:** Send `/stop` → confirm status changes to "stopped" → confirm Workflow 2 skips this row
- [ ] **Status command test:** Send `/status` → confirm fresh price fetched and returned
- [ ] **Daily digest test:** Manually trigger Workflow 3 → confirm digest format and delivery
- [ ] **Multi-user test:** Create 2 different Telegram accounts → both set up tracking → verify both get independent alerts
- [ ] **Nearby airports test:** Set check_nearby=YES for YYZ → confirm multiple airport codes searched
- [ ] **No flights found test:** Enter a nonsense route → verify graceful error message
- [ ] **ONEWAY trip test:** Enter ONEWAY for return date → verify Amadeus call omits returnDate param

---

## PHASE 6 — Deployment (Day 7)

- [ ] Switch Amadeus base URL from `test.api.amadeus.com` to `api.amadeus.com` in all workflows
- [ ] Set up n8n on VPS (Railway, Render, or DigitalOcean) OR use n8n Cloud
- [ ] Configure all n8n credentials with production API keys
- [ ] Set Telegram webhook to production n8n URL:
  `https://api.telegram.org/bot{TOKEN}/setWebhook?url={PROD_N8N_URL}/webhook/telegram`
- [ ] Activate all 3 workflows in n8n
- [ ] Send test message to Telegram bot → verify full flow works on production
- [ ] Monitor n8n execution logs for 48 hours
- [ ] Apply for Twilio WhatsApp Business approval if moving beyond sandbox

---

## Completed Deliverables Checklist

- [ ] `n8n-workflows/workflow-1-conversation-bot.json`
- [ ] `n8n-workflows/workflow-2-hourly-price-monitor.json`
- [ ] `n8n-workflows/workflow-3-daily-digest.json`
- [ ] `google-sheets/flight-tracker-schema.md`
- [ ] `config/env-variables.md`
- [ ] `prompts/bot-conversation-messages.md`
- [ ] `README.md`
- [ ] All 3 workflows active in n8n
- [ ] End-to-end test passed
- [ ] Production deployment complete
