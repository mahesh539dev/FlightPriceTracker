# Bot Conversation Messages

All message templates used in the Flight Price Tracker bot.

---

## Onboarding Messages

### Welcome (step_0)
```
Welcome to FlightTracker Bot!
I'll monitor flight prices for you and alert you when they drop.

First — do you want to receive email alerts?
Reply: YES or NO
```

### Email Collection (step_1)
```
Great! Please provide your email address for alerts.
(We'll only use it for price drop notifications)
```

### Origin Airport (step_2)
```
Where will you be flying from?
Enter your departure city or airport code (e.g., YYZ or Toronto)
```

### Destination Airport (step_3)
```
Where do you want to fly to?
Enter your destination city or airport code (e.g., BOM or Mumbai)
```

### Travel Date (step_4)
```
When do you want to travel?
Enter date in YYYY-MM-DD format (e.g., 2024-12-15)
```

### Return Date (step_5)
```
What's your return date?
Enter in YYYY-MM-DD format or type ONEWAY if it's a one-way trip
```

### Passenger Count (step_6)
```
How many adults will be traveling?
(Enter a number between 1 and 9)
```

### Nearby Airports (step_7)
```
Should I check prices from nearby airports too?
For example, if you enter Toronto, I can also check YTZ, YHM, and YKF.
Reply: YES or NO
```

### Alert Threshold (step_8)
```
How do you want to be alerted about price drops?

1) 5% drop
2) 10% drop
3) 15% drop
4) Custom amount (enter dollar amount)

Reply with 1, 2, 3, or 4 (or a dollar amount for option 4)
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

---

## Price Result Messages

### Search Results (after step_9)
```
Current Prices for {from} → {to}:
━━━━━━━━━━━━━━━━━━━━

{price_1} - {airline_1}
Flight: {flights_1}

{price_2} - {airline_2}
Flight: {flights_2}

{price_3} - {airline_3}
Flight: {flights_3}

━━━━━━━━━━━━━━━━━━━━
Tracking is now ACTIVE!
I'll check prices hourly and alert you when they drop.

Send /stop to stop tracking
Send /status for current prices
```

### No Results Found
```
No flights found for this route/date.
Try different dates or check your airport codes.

You can restart by sending any message.
```

---

## Alert Messages

### Price Drop Alert
```
Price Drop Alert! 📉
✈ {from} → {to}
{travel_date}

Was: {currency} {last_price}
Now: {currency} {current_price} (down {percent_drop}%)

Airline: {airline}
Flight: {flight_numbers}

Book quickly — prices can change!
```

### Best Deal Alert (3+ days tracking)
```
🏆 BEST PRICE in {days} Days of Tracking!

✈ {from} → {to}
{travel_date}

Lowest Ever: {currency} {lowest_price}
(Was {currency} {initial_price} when you started)

That's a saving of {currency} {saving}! (down {percent_drop}%)

This is the lowest we've seen — act fast!
```

---

## Command Responses

### /stop
```
✅ Tracking stopped!

You were tracking:
✈ {from} → {to}

To restart, send any message to begin a new search.
```

### /status
```
📊 Current Status for {from} → {to}

Current Price: {currency} {current_price}
Lowest Ever: {currency} {lowest_price}
Tracking Since: {tracking_since} ({days} days)

Status: {status}
Next check: Every hour automatically
```

### Unknown Command (while tracking)
```
Tracking is active.
Send /stop to stop or /status for latest prices.
```

---

## Daily Digest Message

```
Daily Flight Price Report – {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✈ {from} → {to}
Today: {currency} {price} | Yesterday: {currency} {yesterday_price}
Lowest Ever: {currency} {lowest} | Tracking: {days} days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Email Templates

### Confirmation Email
```
Subject: Flight Tracking Activated - {from} → {to}

Hello!

Your flight price tracking is now active.

Route: {from} → {to}
Travel Date: {travel_date}
Return: {return_date}

Current lowest price: {currency} {price}
Airline: {airline}

We'll notify you when prices drop.

- FlightTracker Bot
```

### Price Drop Email
```
Subject: Price Drop Alert! {from} → {to}

Hello!

Price drop detected on your tracked flight!

Route: {from} → {to}
Travel Date: {travel_date}

Was: {currency} {last_price}
Now: {currency} {current_price}
Saving: {currency} {saving} ({percent_drop}%)

Book now: {booking_link}

- FlightTracker Bot
```

### Daily Digest Email
```
Subject: Your Daily Flight Price Report

Hello!

Here's your daily flight price summary:

{formatted_digest}

- FlightTracker Bot
```