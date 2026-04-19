# Environment Variables Configuration

Complete this file with your actual API credentials before running the workflows.

## Amadeus API (Flight Search)

```env
AMADEUS_API_KEY=your-amadeus-api-key-here
AMADEUS_API_SECRET=your-amadeus-api-secret-here
AMADEUS_BASE_URL=https://test.api.amadeus.com
```

### How to get credentials:
1. Go to https://developers.amadeus.com
2. Create an account or log in
3. Create a new application
4. Copy the API Key and API Secret

For production, change `AMADEUS_BASE_URL` to `https://api.amadeus.com`

---

## Telegram Bot

```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_WEBHOOK_URL=https://your-n8n-instance.com/webhook/telegram
```

### How to get token:
1. Open Telegram and chat with @BotFather
2. Send `/newbot` to create a new bot
3. Follow instructions and copy the token

### Setting webhook:
```
https://api.telegram.org/bot{TOKEN}/setWebhook?url={YOUR_N8N_URL}/webhook/telegram
```

---

## Twilio WhatsApp (Optional)

```env
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### How to get credentials:
1. Create account at https://www.twilio.com
2. Get Account SID and Auth Token from console
3. Activate WhatsApp Sandbox in Twilio console

---

## Gmail OAuth2 (Email Alerts)

```env
GMAIL_OAUTH_CLIENT_ID=your-gmail-oauth-client-id
GMAIL_OAUTH_CLIENT_SECRET=your-gmail-oauth-client-secret
```

### How to setup:
1. Go to https://console.cloud.google.com
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `https://your-n8n-instance.com/oauth2/callback`
6. Copy Client ID and Client Secret

---

## Google Sheets

```env
GOOGLE_SHEETS_ID=your-google-sheet-id-here
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","universe_domain":"googleapis.com"}
```

### How to get Sheet ID:
- Open your Google Sheet
- The ID is in the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

### How to get Service Account credentials:
1. Go to https://console.cloud.google.com
2. Create a service account
3. Generate a JSON key
4. Share your Google Sheet with the service account email

---

## n8n Credentials Setup Order

1. **Amadeus OAuth2 API** - for flight search authentication
2. **Telegram Bot API** - for sending/receiving messages
3. **Twilio API** - for WhatsApp messages (optional)
4. **Gmail OAuth2 API** - for email alerts (optional)
5. **Google Sheets API** - for database operations