# Flight Price Tracker Bot

A fully automated flight price tracking system built on **n8n** that monitors flight prices and alerts you via Telegram, WhatsApp, and email when prices drop.

## Features

- **Conversational Bot**: Walks you through setup via Telegram or WhatsApp
- **Hourly Price Monitoring**: Automatically checks for price drops every hour
- **Multi-channel Alerts**: Get notified via Telegram, WhatsApp, and email
- **Nearby Airports**: Checks multiple airports in your area for better deals
- **Daily Digest**: Morning summary of all your tracked flights

---

## Prerequisites

1. **Node.js 18+** (for n8n)
2. **n8n** (self-hosted or cloud)
3. Active accounts for:
   - Telegram (free)
   - Amadeus (free for test environment)
   - Google Sheets (free)
   - Twilio WhatsApp (optional, ~$1-5/month)
   - Gmail OAuth2 (free)

---

## Setup Guide

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts:
   - Enter a name for your bot (e.g., "FlightTracker")
   - Enter a username (e.g., "MyFlightTrackerBot")
4. Copy the **Bot Token** - you'll need it later

### Step 2: Get Amadeus API Credentials

1. Go to https://developers.amadeus.com
2. Click **Get Started**
3. Create an account or log in
4. Go to **My Workspace** → **Create New App**
5. Select **Flight Offers Search API v2**
6. Copy your **API Key** and **API Secret**
7. For testing, use: `https://test.api.amadeus.com`
8. For production, switch to: `https://api.amadeus.com`

### Step 3: Set Up Google Sheets

#### Create the Spreadsheet:

1. Go to https://sheets.google.com
2. Click **+ New** → **Google Sheets**
3. Name it "FlightTracker"
4. Rename the default sheet to "Sessions"
5. Add two more sheets: "Tracker" and "PriceHistory"

#### Set Up Sessions Tab:

| Column A | Column B | Column C | Column D | Column E |
|----------|----------|----------|----------|----------|
| chat_id | platform | step | temp_data | last_active |

#### Set Up Tracker Tab:

| Column A | Column B | Column C | Column D | Column E | Column F | Column G | Column H | Column I | Column J | Column K | Column L | Column M | Column N | Column O | Column P | Column Q | Column R | Column S | Column T | Column U |
|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|-----------|
| tracker_id | chat_id | platform | from_airport | to_airport | travel_date | return_date | passengers | check_nearby | initial_price | last_price | lowest_price | last_checked | tracking_since | alert_threshold_percent | alert_threshold_fixed | email_alerts | email_address | whatsapp_number | status | currency |

#### Set Up PriceHistory Tab:

| Column A | Column B | Column C | Column D | Column E |
|----------|----------|----------|----------|----------|
| tracker_id | timestamp | price | airline | flight_numbers |

#### Enable Google Sheets API:

1. Go to https://console.cloud.google.com
2. Create a new project (or select existing)
3. Search for and enable **Google Sheets API**
4. Search for and enable **Google Drive API**

#### Create Service Account:

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **Service Account**
3. Name it (e.g., "flight-tracker")
4. Click **Done**
5. Click on your new service account
6. Go to **Keys** → **Add Key** → **JSON**
7. Download the JSON file - this is your `GOOGLE_SHEETS_CREDENTIALS`
8. Copy the `client_email` from the JSON

#### Share the Spreadsheet:

1. Open your FlightTracker spreadsheet
2. Click **Share**
3. Paste the `client_email` from your service account
4. Set as **Editor**
5. Click **Send**

#### Get Your Sheet ID:

1. Open the spreadsheet
2. Copy the ID from the URL:
   `https://docs.google.com/spreadsheets/d/{THIS_IS_YOUR_SHEET_ID}/edit`

### Step 4: Set Up Gmail OAuth2 (Optional)

1. Go to https://console.cloud.google.com
2. Select your project
3. Search for and enable **Gmail API**
4. Go to **APIs & Services** → **OAuth consent screen**
5. Select **External** → **Create**
6. App name: "FlightTracker"
7. Add your email as test user
8. Click **Credentials** → **+ Create Credentials** → **OAuth client ID**
9. Application type: **Web application**
10. Add authorized redirect URI: `https://your-n8n-url.com/oauth2/callback`
11. Copy **Client ID** and **Client Secret**

### Step 5: Set Up Twilio WhatsApp (Optional)

1. Create account at https://www.twilio.com
2. Go to Console → Account Info
3. Copy **Account SID** and **Auth Token**
4. Go to **Messaging** → **Settings** → **WhatsApp Sandbox**
5. Activate sandbox (send code to WhatsApp number)
6. Copy your WhatsApp sender number

### Step 6: Install and Configure n8n

#### Option A: n8n Cloud (Easier)

1. Sign up at https://n8n.io
2. Create a new instance
3. Install required community nodes (if any)

#### Option B: Self-hosted (Recommended for cost savings)

```bash
# Using Docker
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# Or using npm
npm install -g n8n
n8n start
```

#### Configure Webhook URL:

1. Note your n8n URL (e.g., `https://your-n8n.onrender.com`)
2. Set up Telegram webhook:
   ```
   https://api.telegram.org/bot{TOKEN}/setWebhook?url={YOUR_N8N_URL}/webhook/telegram
   ```

### Step 7: Configure n8n Credentials

In n8n, go to **Settings** → **Credentials** and add:

#### Amadeus OAuth2:
- Auth URL: `https://test.api.amadeus.com/v1/security/oauth2/token`
- Access Token URL: `https://test.api.amadeus.com/v1/security/oauth2/token`
- Client ID: (from Amadeus)
- Client Secret: (from Amadeus)
- Grant Type: `client_credentials`

#### Telegram Bot API:
- Bot Token: (from @BotFather)

#### Google Sheets API:
- Service Account JSON: (from downloaded JSON)

#### Gmail OAuth2:
- Client ID: (from Google Cloud)
- Client Secret: (from Google Cloud)
- Authorization URL: `https://accounts.google.com/o/oauth2/auth`
- Access Token URL: `https://oauth2.googleapis.com/token`

#### Twilio:
- Account SID: (from Twilio)
- Auth Token: (from Twilio)

---

## Import Workflows

### Import Workflow 1 (Conversation Bot):

1. In n8n, click **Workflows** → **Import from JSON**
2. Paste the contents of `n8n-workflows/workflow-1-conversation-bot.json`
3. Save

### Import Workflow 2 (Hourly Monitor):

1. Import `n8n-workflows/workflow-2-hourly-price-monitor.json`

### Import Workflow 3 (Daily Digest):

1. Import `n8n-workflows/workflow-3-daily-digest.json`

### Configure Workflow Connections:

1. Open each workflow
2. Set the Google Sheets credential to your configured account
3. Set the Telegram credential
4. Activate all three workflows

---

## Testing Your Setup

### Test the Telegram Bot:

1. Open Telegram and find your bot
2. Send `/start` or any message
3. You should receive the welcome message

### Complete Onboarding:

1. Reply to each question
2. At step 9, you should see flight prices
3. A Tracker row should appear in your Google Sheet

### Test Commands:

- `/stop` - Should stop tracking
- `/status` - Should show current price

### Test Price Monitoring:

1. Manually edit the `last_price` in your Tracker sheet to a higher value
2. Trigger Workflow 2 manually
3. You should receive a Telegram alert

---

## Project Structure

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

## Cost Summary

| Service | Monthly Cost |
|---------|--------------|
| Amadeus API (Test) | $0 |
| Telegram Bot | $0 |
| Google Sheets | $0 |
| Gmail | $0 |
| n8n Cloud Starter | $20/month |
| Twilio WhatsApp (optional) | $1-5 |

**Total: $0-25/month** depending on hosting choice

---

## Troubleshooting

### Bot not responding?

1. Check Telegram webhook is set correctly
2. Verify n8n workflow is active
3. Check n8n execution logs

### No flight results?

1. Verify Amadeus credentials are correct
2. Check if test environment is working
3. Try different dates

### Price alerts not working?

1. Check Tracker row has status="active"
2. Verify threshold settings
3. Check Telegram bot is working

---

## Production Deployment

When ready for production:

1. Switch Amadeus URL from `test.api.amadeus.com` to `api.amadeus.com`
2. Deploy n8n to a production server
3. Update Telegram webhook to production URL
4. Test all workflows end-to-end
5. Monitor for 48 hours