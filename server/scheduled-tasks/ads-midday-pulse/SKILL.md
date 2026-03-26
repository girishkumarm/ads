---
name: ads-midday-pulse
description: Daily 12:00 PM IST weekdays — Mid-day spend pacing check, delivery issues, CPC anomalies. Brief Telegram update.
---

## MIDDAY PULSE — SPEND PACING & ANOMALY CHECK

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Check

1. Set DATE variable.
2. Check if it's a weekday: `TZ='Asia/Kolkata' date +%u` — if 6 or 7 (Sat/Sun), skip.
3. Check if already ran: look for `MIDDAY_PULSE_COMPLETE` in `ads-report-{DATE}.md` — if found, skip.
4. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```

### STEP 1: Google Ads Spend Pacing

```bash
python3 /root/ads/ads_api.py google campaigns
```

For each ENABLED campaign:
```bash
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 1   # Today so far
```

**Checks:**
- It's roughly noon (50% of day). Compare today's spend so far vs daily budget:
  - Spend < 30% of daily budget → WARNING: underspend / delivery issue
  - Spend > 70% of daily budget → WARNING: pacing too fast, may exhaust budget early
  - Spend between 30-70% → OK: on track

### STEP 2: Facebook Ads Spend Pacing

```bash
python3 /root/ads/ads_api.py fb campaigns
```

For each ACTIVE campaign:
```bash
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 1   # Today so far
```

**Checks:**
- Compare today's spend vs daily budget (same 30-70% midday range)
- Check if any campaign has Rs 0 spend today → **STOPPED DELIVERING** — flag immediately
- Check if any campaign that was ACTIVE in morning audit is now PAUSED → flag unexpected pause

### STEP 3: CPC Anomaly Detection

For each platform/campaign with today's data:
1. Get 7-day average CPC: `python3 /root/ads/ads_api.py {google|fb} metrics {CAMPAIGN_ID} 7`
2. Compare today's CPC vs 7-day average:
   - Today CPC > 150% of 7-day avg → CPC SPIKE alert
   - Today CPC < 50% of 7-day avg → Unusual — could indicate quality issue or low competition

### STEP 4: Send Telegram Update

```bash
python3 /root/stocks/notify.py send "SUMMARY" --title "Midday Pulse" --audience girish
```

**Message format:**
```
Midday Pulse — {DATE} 12:00 PM

GOOGLE ADS:
  Spend so far: Rs X / Rs Y budget ({Z}% — {ON_TRACK/SLOW/FAST})
  CPC today: Rs X (7d avg: Rs Y) {OK/SPIKE}

FB ADS:
  Spend so far: Rs X / Rs Y budget ({Z}% — {ON_TRACK/SLOW/FAST})
  {Any campaigns stopped delivering}
  CPC today: Rs X (7d avg: Rs Y) {OK/SPIKE}

{If any issues: list them with severity}
{If all OK: "All campaigns pacing normally."}
```

Use `--priority high` if any campaign stopped delivering or CPC spike > 200%, default otherwise.

### STEP 5: Log Completion

Append to `ads-report-{DATE}.md`:
```
MIDDAY_PULSE_COMPLETE: {TIME} IST
Google midday spend: Rs X / Rs Y budget
FB midday spend: Rs X / Rs Y budget
Issues: {none / list}
```

### CLEANUP
No browser used. No locks. Quick check — should complete in under 2 minutes.
