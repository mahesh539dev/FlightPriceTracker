# Flight Price Tracker Bot

A fully automated flight price tracking system built on **n8n** that monitors flight prices and sends alerts via Telegram, WhatsApp, and Gmail.

## What It Does

- **Telegram bot** guides users through a 10-step onboarding conversation to set up flight tracking
- **Hourly price checks** via the Kiwi.com Tequila API, comparing against your alert threshold
- **Smart alerts**: standard price drop alerts plus "Best Deal" alerts after 3+ days of tracking
- **Daily digest** at 9 AM summarising all tracked routes and their current prices
- **Multi-channel delivery**: Telegram (required), Gmail (optional), WhatsApp via Twilio (optional)
- Supports nearby airport detection, one-way and round-trip flights, multiple passengers

---

## Prerequisites

You need accounts and API credentials for:

| Service | Purpose | Cost |
|---------|---------|------|
| n8n | Automation engine | Free (self-hosted) or $20/mo (cloud) |
| Telegram Bot API | Conversational bot + alerts | Free |
| Kiwi.com Tequila | Flight price data | Free (unlimited API calls) |
| Google Sheets API | Database (Sessions, Tracker, PriceHistory) | Free |
| Gmail OAuth2 | Email alerts | Free |
| Twilio WhatsApp | WhatsApp alerts (optional) | ~$1–$5/100 alerts |

---

## Setup Guide

### Step 1: Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts — give it a name and username
3. Copy the **API Token** (looks like `123456:ABCdef...`)
4. Keep this token — you'll need it in n8n credentials

### Step 2: Kiwi.com Tequila API Key

1. Go to [tequila.kiwi.com](https://tequila.kiwi.com)
2. Click **Get your free API key** and register
3. Copy your **API key** from the dashboard
4. No test/production switching needed — use the same API key everywhere

### Step 3: Google Sheets Database

1. Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet
2. Rename the first sheet tab to **Sessions**
3. Add two more tabs named **Tracker** and **PriceHistory**
4. Add the following column headers to each tab:

**Sessions tab** (row 1 headers):
```
chat_id | platform | step | temp_data | last_active
```

**Tracker tab** (row 1 headers):
```
tracker_id | chat_id | platform | from_airport | to_airport | travel_date | return_date | passengers | check_nearby | initial_price | last_price | lowest_price | last_checked | tracking_since | alert_threshold_percent | alert_threshold_fixed | email_alerts | email_address | whatsapp_number | status | currency
```

**PriceHistory tab** (row 1 headers):
```
tracker_id | timestamp | price | airline | flight_numbers
```

5. Copy the **Spreadsheet ID** from the URL (the long string between `/d/` and `/edit`)
6. Go to [console.cloud.google.com](https://console.cloud.google.com)
7. Create a new project, enable the **Google Sheets API**
8. Go to **IAM & Admin > Service Accounts** and create a service account
9. Download the JSON key file
10. Share your Google Sheet with the service account email (Editor access)

### Step 4: Gmail OAuth2 in n8n

1. In n8n go to **Credentials > New > Gmail OAuth2 API**
2. Follow the Google OAuth consent flow
3. Grant access to send emails from your account
4. Name the credential `gmail-oauth`

### Step 5: Twilio WhatsApp (Optional)

1. Sign up at [twilio.com](https://twilio.com)
2. Go to **Messaging > Try it out > Send a WhatsApp message**
3. Note your **Account SID**, **Auth Token**, and the sandbox number (`whatsapp:+14155238886`)
4. For production: apply for WhatsApp Business API approval through Twilio

### Step 6: Install n8n

**Option A — Docker (recommended):**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Option B — npm:**
```bash
npm install n8n -g
n8n start
```

**Option C — n8n Cloud:**
Sign up at [n8n.io](https://n8n.io) (paid, $20/month starter plan)

Access n8n at `http://localhost:5678`

### Step 7: Configure n8n Credentials

In n8n, go to **Credentials** and create the following:

| Credential Name | Type | Values |
|----------------|------|--------|
| `google-sheets` | Google Sheets OAuth2 / Service Account | Your service account JSON |
| `telegram-bot` | Telegram API | Your bot token |
| `gmail-oauth` | Gmail OAuth2 | Follow OAuth flow |
| `twilio-credentials` | Twilio API | Account SID + Auth Token |

### Step 8: Set Environment Variables

In n8n go to **Settings > Variables** and add:

```
GOOGLE_SHEETS_ID     = your-spreadsheet-id
KIWI_API_KEY         = your-kiwi-api-key
TWILIO_WHATSAPP_FROM = whatsapp:+14155238886
```

### Step 9: Import Workflows

1. In n8n go to **Workflows > Import from file**
2. Import in this order:
   - `n8n-workflows/workflow-1-conversation-bot.json`
   - `n8n-workflows/workflow-2-hourly-price-monitor.json`
   - `n8n-workflows/workflow-3-daily-digest.json`
3. Open each workflow and confirm the correct credentials are attached to each node

### Step 10: Set Telegram Webhook

After importing and activating Workflow 1, get your n8n webhook URL from the Telegram Trigger node, then register it:

```
https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url={YOUR_N8N_WEBHOOK_URL}
```

### Step 11: Activate Workflows

In n8n, open each workflow and click **Activate** (the toggle in the top right). All three workflows must be active.

---

## Using the Bot

1. Open Telegram and find your bot
2. Send any message to start — the bot guides you through the setup
3. Answer each question about your route, dates, and alert preferences
4. After step 9, the bot searches for prices and begins tracking
5. **Commands while tracking:**
   - `/stop` — stop tracking this route
   - `/status` — get current prices right now

---

## Testing

**Test the conversation flow:**
Send any message to your Telegram bot and step through all 10 questions.

**Test hourly monitoring manually:**
Open Workflow 2 in n8n and click **Test workflow**. Check that it reads active Tracker rows and updates `last_checked`.

**Simulate a price drop:**
1. In the Tracker sheet, find your active row
2. Change `last_price` to a value higher than current market price (e.g. set it to 1000)
3. Manually trigger Workflow 2 — you should receive a price drop alert

**Test daily digest:**
Open Workflow 3 and click **Test workflow**. You should receive a digest message in Telegram (and email/WhatsApp if configured).

---

## Project Structure

```
flight-price-tracker/
├── n8n-workflows/
│   ├── workflow-1-conversation-bot.json      # Telegram bot onboarding + commands
│   ├── workflow-2-hourly-price-monitor.json  # Hourly price checks + alerts
│   └── workflow-3-daily-digest.json          # 9 AM daily summary
├── google-sheets/
│   └── flight-tracker-schema.md              # Column definitions for all tabs
├── config/
│   └── env-variables.md                      # All required API keys and tokens
├── prompts/
│   └── bot-conversation-messages.md          # All bot message templates
├── CLAUDE.md                                 # Architecture reference for AI agents
└── README.md                                 # This file
```

---

## How It Works

### Workflow 1 — Conversation Bot
Triggered by every Telegram message. Reads the user's current step from the Sessions sheet, routes to the right question handler, saves the answer, and advances the step. At step 9, it fetches live prices from Amadeus, writes a row to the Tracker sheet, and sends current prices to the user.

### Workflow 2 — Hourly Monitor
Runs every hour. Reads all active Tracker rows, fetches fresh Kiwi prices for each route, calculates if the price drop exceeds the user's threshold, and sends alerts via Telegram, email, and WhatsApp as configured. Always appends to PriceHistory for trend data.

### Workflow 3 — Daily Digest
Runs every day at 9 AM. Groups all active routes by user, fetches today's prices for each route, and sends a formatted summary showing today's price, yesterday's price, and the lowest price ever seen.

---

## Troubleshooting

**Bot not responding:**
- Verify the Telegram webhook is registered: `https://api.telegram.org/bot{TOKEN}/getWebhookInfo`
- Confirm Workflow 1 is Active in n8n
- Check n8n execution logs for errors

**Kiwi returns no results:**
- Verify your Kiwi API key is correct in n8n environment variables
- Confirm the departure date is in the future
- Confirm IATA airport codes are valid (e.g. YYZ, BOM, LHR)
- Try expanding the date range (Kiwi may need 3+ day windows for some routes)

**Google Sheets not updating:**
- Verify the sheet ID in the `GOOGLE_SHEETS_ID` environment variable
- Confirm the service account email has Editor access to the sheet
- Check that all 3 tabs exist with exact names: Sessions, Tracker, PriceHistory

**Email not sending:**
- Re-authenticate the Gmail OAuth2 credential in n8n (tokens expire)
- Check that the credential is named `gmail-oauth` and attached to the Gmail nodes

**WhatsApp not sending:**
- Twilio sandbox: your number must opt in by sending "join {sandbox-keyword}" to the sandbox number
- Verify `TWILIO_WHATSAPP_FROM` includes the `whatsapp:` prefix
- For production, ensure WhatsApp Business API approval is complete

---

## Production Deployment

1. Kiwi.com API works the same in dev and production — no URL switching needed
2. Deploy n8n to a VPS — Railway, Render, or DigitalOcean are good low-cost options
3. Update the Telegram webhook URL to your production n8n address
4. Monitor n8n execution logs for the first 48 hours

---

## Cost Summary

| Service | Free Tier | Estimated Monthly |
|---------|-----------|------------------|
| Kiwi.com Tequila | Unlimited | $0 |
| Telegram Bot API | Unlimited | $0 |
| Twilio WhatsApp | $0 incoming | ~$1–$5 per 100 alerts |
| Gmail | Free | $0 |
| Google Sheets API | Free | $0 |
| n8n Cloud Starter | 5,000 executions | $20/month |
| n8n Self-hosted VPS | — | ~$5–$10/month |

**Total: approximately $5–$30/month** depending on usage and hosting choice.
