# Migration Guide: Amadeus → Kiwi.com Tequila API

## Overview

This guide explains the changes needed to migrate all three n8n workflows from Amadeus Flight Offers API to Kiwi.com Tequila API.

---

## Key Differences

| Aspect | Amadeus | Kiwi.com |
|--------|---------|---------|
| **Auth** | OAuth2 (token required) | Simple API key in query params |
| **Endpoint** | `https://test.api.amadeus.com/v2/shopping/flight-offers` | `https://tequila-api.kiwi.com/v2/search` |
| **Params** | `originLocationCode`, `destinationLocationCode` | `fly_from`, `fly_to` |
| **Development** | Separate test/prod URLs | Single URL works everywhere |
| **Response** | Complex nested JSON structure | Simpler flat array structure |
| **Rate Limits** | 500 calls/month (prod) | Unlimited (free tier) |

---

## Workflow 1: Conversation Bot - Changes

### Remove OAuth Node
**OLD:**
```
Amadeus OAuth → POST https://test.api.amadeus.com/v1/security/oauth2/token
```

**NEW:**
- Delete the "Amadeus OAuth" node entirely
- Skip directly from "Send Confirmation" → "Merge Token With Context"

### Update "Merge Token With Context" Code Node

**OLD JavaScript:**
```javascript
const oauthData = $input.first().json;
const ctx = $('Step 9 - Build Search Context').first().json;
const accessToken = oauthData.access_token;
if (!accessToken) throw new Error('No Amadeus access token received');

const searchTasks = ctx.origin_codes.map(code => ({
  access_token: accessToken,
  from_airport: code,
  ...ctx
}));
return searchTasks;
```

**NEW JavaScript (with Kiwi API key):**
```javascript
const ctx = $('Step 9 - Build Search Context').first().json;
const kiwiApiKey = $env.KIWI_API_KEY;
if (!kiwiApiKey) throw new Error('KIWI_API_KEY environment variable not set');

const searchTasks = ctx.origin_codes.map(code => ({
  api_key: kiwiApiKey,
  from_airport: code,
  to_airport: ctx.to_airport,
  travel_date: ctx.travel_date,
  return_date: ctx.return_date,
  passengers: ctx.passengers,
  email_alerts: ctx.email_alerts,
  email_address: ctx.email_address,
  alert_threshold_percent: ctx.alert_threshold_percent,
  alert_threshold_fixed: ctx.alert_threshold_fixed,
  check_nearby: ctx.check_nearby,
  currency: ctx.currency,
  chat_id: ctx.chat_id,
  temp_data: ctx.temp_data
}));
return searchTasks;
```

### Replace Flight Search HTTP Request Node

**OLD HTTP Request:**
```
Method: GET
URL: https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=...&destinationLocationCode=...&departureDate=...&adults=...&max=5&currencyCode=...
Headers: Authorization: Bearer {access_token}
```

**NEW HTTP Request:**
```
Method: GET
URL: https://tequila-api.kiwi.com/v2/search?apikey={{$env.KIWI_API_KEY}}&fly_from={{$json.from_airport}}&fly_to={{$json.to_airport}}&date_from={{$json.travel_date}}&date_to={{$json.return_date}}&adults={{$json.passengers}}&limit=5&curr={{$json.currency}}
Headers: None (no auth headers needed)
```

**Important:** 
- If `return_date === 'ONEWAY'`, omit the `date_to` parameter
- Add `&return_to={{$json.travel_date}}` when it's a one-way (Kiwi requires both date_from and return_to, but they can be the same)

### Update "Parse And Merge Results" Code Node

**OLD JavaScript (Amadeus response parsing):**
```javascript
if (data.data && data.data.length > 0) {
  for (const offer of data.data) {
    allOffers.push({
      price: parseFloat(offer.price.total),
      currency: offer.price.currencyCode,
      airline: offer.validatingAirlineCodes[0],
      flight_numbers: offer.itineraries[0].segments.map(s => s.number).join(', ')
    });
  }
}
```

**NEW JavaScript (Kiwi response parsing):**
```javascript
if (data.data && data.data.length > 0) {
  for (const offer of data.data) {
    allOffers.push({
      price: parseFloat(offer.price),
      currency: data.currency || 'CAD',
      airline: offer.airlines[0] || 'Unknown',
      flight_numbers: offer.route.map(r => `${r.airline}${r.flight_no}`).join(', ')
    });
  }
}
```

**Kiwi Response Structure:**
```json
{
  "data": [
    {
      "id": "...",
      "price": 450.50,
      "airlines": ["AC", "BA"],
      "route": [
        {
          "id": "...",
          "airline": "AC",
          "flight_no": "872",
          "departure": "2026-12-15T10:00:00",
          "arrival": "2026-12-15T22:30:00"
        }
      ],
      "deep_link": "..."
    }
  ],
  "currency": "CAD"
}
```

---

## Workflow 2: Hourly Price Monitor - Changes

### Remove OAuth Node
- Delete "Amadeus OAuth" node

### Update Flight Search HTTP Request

Replace:
```
https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode={{$json.from_airport}}&destinationLocationCode={{$json.to_airport}}&departureDate={{$json.travel_date}}&adults={{$json.passengers}}&max=5&currencyCode={{$json.currency}}
Authorization: Bearer {access_token}
```

With:
```
https://tequila-api.kiwi.com/v2/search?apikey={{$env.KIWI_API_KEY}}&fly_from={{$json.from_airport}}&fly_to={{$json.to_airport}}&date_from={{$json.travel_date}}&date_to={{$json.return_date}}&adults={{$json.passengers}}&limit=1&curr={{$json.currency}}
```

**Note:** Use `limit=1` (not 5) since we only need the cheapest price for comparison.

### Update "Extract Cheapest Price" Code Node

**Kiwi response is already sorted by price (cheapest first):**
```javascript
const data = $input.first().json;
if (!data.data || data.data.length === 0) {
  return { no_results: true };
}

const offer = data.data[0]; // Kiwi returns sorted by price
return {
  current_price: parseFloat(offer.price),
  airline: offer.airlines[0] || 'Unknown',
  flight_numbers: offer.route.map(r => `${r.airline}${r.flight_no}`).join(', '),
  currency: data.currency || $json.currency
};
```

---

## Workflow 3: Daily Digest - Changes

### Similar to Workflow 2
- Remove OAuth node
- Update HTTP Request URL (use Kiwi endpoint)
- Update response parsing code

---

## Environment Variables to Update

**In n8n Settings > Variables:**

Remove:
- `AMADEUS_API_KEY`
- `AMADEUS_API_SECRET`

Add:
- `KIWI_API_KEY` = your-kiwi-api-key (from https://tequila.kiwi.com)

---

## Testing Checklist

After updating workflows:

1. ✅ Test Workflow 1: Send a message to your Telegram bot and go through the full onboarding. Verify prices are fetched from Kiwi.
2. ✅ Test Workflow 2: Manually trigger the hourly monitor. Check that it reads Tracker rows and fetches prices.
3. ✅ Test Workflow 3: Manually trigger the daily digest. Verify digests are sent to users.
4. ✅ Test one-way flights: Set `return_date` to "ONEWAY" and verify searches work.
5. ✅ Test nearby airports: Enable nearby airports and verify multiple airport codes are searched.

---

## API Response Comparison

### Amadeus Response
```json
{
  "data": [
    {
      "id": "1",
      "type": "flight-offer",
      "source": "GDS",
      "instantTicketingRequired": false,
      "disablePricing": false,
      "nonHomogeneous": false,
      "oneWay": false,
      "lastTicketingDate": "2026-12-08",
      "numberOfBookableSeats": 4,
      "itineraries": [
        {
          "duration": "PT12H30M",
          "segments": [
            {
              "departure": { "at": "2026-12-15T10:00:00" },
              "arrival": { "at": "2026-12-15T22:30:00" },
              "carrierCode": "AC",
              "number": "872"
            }
          ]
        }
      ],
      "price": {
        "total": "450.50",
        "base": "400.00",
        "currency": "CAD"
      },
      "pricingOptions": { "fareType": ["published"] },
      "validatingAirlineCodes": ["AC"]
    }
  ]
}
```

### Kiwi Response
```json
{
  "search_params": {
    "fly_from": "YYZ",
    "fly_to": "BOM",
    "date_from": "2026-12-15",
    "date_to": "2026-12-20",
    "adults": 1
  },
  "data": [
    {
      "id": "...",
      "price": 450.50,
      "local_arrival": "2026-12-16 08:30",
      "utc_arrival": "2026-12-16 13:30",
      "local_departure": "2026-12-15 10:00",
      "utc_departure": "2026-12-15 15:00",
      "fly_duration": "20h 30m",
      "validity": "2026-04-25",
      "availability": {
        "seats": 4
      },
      "airlines": ["AC", "AI"],
      "operating_airlines": ["AC", "AI"],
      "route": [
        {
          "id": "...",
          "airline": "AC",
          "flight_no": "872",
          "operating_airline": "AC",
          "departure": "2026-12-15T10:00:00Z",
          "arrival": "2026-12-15T22:30:00Z"
        }
      ],
      "deep_link": "https://www.kiwi.com/..."
    }
  ],
  "currency": "CAD",
  "server_time": 1234567890
}
```

---

## Important Kiwi API Notes

1. **Date Formats:** Kiwi uses `YYYY-MM-DD`, same as Amadeus ✅
2. **Airport Codes:** Both use IATA codes ✅
3. **Currency:** Kiwi accepts the same currency codes ✅
4. **One-way flights:** Use `date_from` and `date_to` as the same date, or include `&return_to=` parameter
5. **Nearby airports:** No native support; you still need to run separate queries per airport code in Workflow 1
6. **Rate limits:** No rate limits on free tier (unlimited calls)
7. **Response times:** Kiwi typically responds in 1-2 seconds (faster than Amadeus)

---

## Additional Resources

- **Kiwi.com API Docs:** https://tequila.kiwi.com/docs
- **Get API Key:** https://tequila.kiwi.com

---
