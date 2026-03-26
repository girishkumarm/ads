---
name: ads-forecast
description: Sunday 2:30 AM IST — Weekly forecast: spend projections, fund depletion date, creative fatigue prediction, seasonal signals.
---

## ADS FORECAST — WEEKLY PROJECTIONS & PREDICTIONS

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Check

1. Set DATE variable.
2. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```
3. Read `/root/ads/ads-metrics-history.json` — if doesn't exist, create skeleton and note limited data.

### STEP 1: Monthly Spend Projection

**Google Ads:**
```bash
python3 /root/ads/ads_api.py google campaigns
# For each ENABLED campaign, get last 30 days:
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 30
python3 /root/ads/ads_api.py google budget
```

**Facebook Ads:**
```bash
python3 /root/ads/ads_api.py fb campaigns
python3 /root/ads/ads_api.py fb account-spend 30
# For each ACTIVE campaign, get last 30 days:
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 30
```

**Compute weighted moving average (WMA):**
- Last 7 days weight: 3x
- Days 8-14 weight: 2x
- Days 15-30 weight: 1x
- WMA daily spend = weighted sum / total weights
- Monthly projection = WMA daily spend * days in current month

### STEP 2: Google Fund Depletion Date

```bash
python3 /root/ads/ads_api.py google budget
```

- Current balance: Rs X
- WMA daily burn rate: Rs Y/day (from Step 1)
- Days remaining = balance / daily burn rate
- Depletion date = today + days remaining

**Alerts:**
- Depletion < 7 days → HIGH priority
- Depletion < 14 days → WARNING
- Depletion < 3 days → CRITICAL

### STEP 3: Creative Fatigue Prediction

For each active FB campaign:
```bash
python3 /root/ads/ads_api.py fb frequency {CAMPAIGN_ID}
```

Read `/root/ads/ads-rotation-state.md` for historical frequency data.

**Compute frequency growth rate:**
- If current frequency is F and was F_prev last week:
  - Weekly growth rate = (F - F_prev) / F_prev
  - Days until frequency hits 3.0 = (3.0 - F) / (daily growth rate)
  - If < 7 days → flag for imminent rotation

**Check ad count health:**
- Count active ads per campaign
- Count paused/resting ads per campaign
- If active <= 1 and frequency > 2.0 → URGENT: need new creatives soon

### STEP 4: Seasonal Demand Signals

Based on current month and historical data in `ads-metrics-history.json`:
- Compare current week's metrics to same period last year (if data available)
- Check for upcoming holidays/long weekends (Indian calendar):
  - Flag if a long weekend is within 14 days — expect demand spike for resort
- Note seasonal trends:
  - Oct-Mar: peak season for resort (pleasant weather)
  - Apr-Jun: summer — cafe may do better, resort slower
  - Jul-Sep: monsoon — lower outdoor demand

### STEP 5: Update Metrics History

Append this week's summary to `/root/ads/ads-metrics-history.json`:
```json
{
  "week_of": "{DATE}",
  "google": {
    "daily_avg_spend": X,
    "daily_avg_clicks": X,
    "avg_cpc": X,
    "avg_ctr": X,
    "conversions": X,
    "balance": X
  },
  "facebook": {
    "daily_avg_spend": X,
    "daily_avg_clicks": X,
    "avg_cpc": X,
    "avg_ctr": X,
    "total_calls": X,
    "avg_frequency": X
  }
}
```

### STEP 6: Send Weekly Forecast

```bash
python3 /root/stocks/notify.py send "FORECAST" --title "Weekly Ads Forecast" --priority {PRIORITY} --audience girish
```

**Message format:**
```
Weekly Ads Forecast — {DATE}

SPEND PROJECTIONS (this month):
  Google: Rs {X} projected (budget: Rs {Y})
  Facebook: Rs {X} projected
  Combined: Rs {X}/month

GOOGLE FUND DEPLETION:
  Balance: Rs {X}
  Burn rate: Rs {Y}/day
  Runs out: {DATE} ({N} days)
  {ACTION NEEDED if < 14 days}

CREATIVE FATIGUE:
  {Campaign}: frequency {X}, hits 3.0 in ~{N} days
  {Campaign}: OK — frequency {X}, stable
  Active creatives available: {N}

SEASONAL NOTES:
  {Any relevant seasonal signals}
  {Upcoming holidays/weekends}

WEEK OVER WEEK:
  Google CPC: {trend}
  FB cost/call: {trend}
  Total spend: {trend}
```

Use `--priority urgent` if fund depletion < 3 days, `--priority high` if < 14 days.

### CLEANUP
No browser used. All data stored in ads-metrics-history.json and rotation state files.
