---
name: ads-evening-report
description: Daily 6:03 PM IST — Pull full-day metrics, generate daily report, send Telegram summary
---

## EVENING ADS REPORT

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Checks

1. Set DATE: `TZ='Asia/Kolkata' date +%Y-%m-%d`
2. Check if report already exists: `ads-report-{DATE}.md` with "EVENING_REPORT_COMPLETE" → skip
3. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```

### STEP 1: Pull Full-Day Metrics

**Google Ads:**
```bash
python3 /root/ads/ads_api.py google campaigns
# For each ENABLED campaign:
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 1   # Today
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 7   # 7-day avg
python3 /root/ads/ads_api.py google budget
```

**Facebook Ads:**
```bash
python3 /root/ads/ads_api.py fb campaigns
# For each ACTIVE campaign:
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 1     # Today
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 7     # 7-day avg
python3 /root/ads/ads_api.py fb account-spend 1             # Today total
python3 /root/ads/ads_api.py fb account-spend 30            # MTD
```

### STEP 2: Read Yesterday's Report for Comparison

If `ads-report-{YESTERDAY}.md` exists, read it to compute day-over-day changes.
YESTERDAY = date one day before DATE.

### STEP 3: Generate Daily Report

Write to `/root/ads/ads-report-{DATE}.md`:

```markdown
# Ads Report — {DATE}

## Google Ads — Namooru Ecostay Resort

| Metric | Today | Yesterday | 7-Day Avg | Trend |
|--------|-------|-----------|-----------|-------|
| Clicks | X | Y | Z | up/down/flat |
| Impressions | X | Y | Z | |
| CTR | X% | Y% | Z% | |
| CPC | Rs X | Rs Y | Rs Z | |
| Conversions | X | Y | Z | |
| Spend | Rs X | Rs Y | Rs Z | |

Budget remaining: Rs X
Days until fund depletion: X (at current daily burn rate)

## Facebook Ads — BUS Cafe

### By Campaign:
| Campaign | Status | Spend | Clicks | CTR | CPC | Freq | Calls |
|----------|--------|-------|--------|-----|-----|------|-------|
| [name] | ACTIVE | Rs X | X | X% | Rs X | X.X | X |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Totals:
| Metric | Today | Yesterday | 7-Day Avg | Trend |
|--------|-------|-----------|-----------|-------|
| Total spend | Rs X | Rs Y | Rs Z | |
| Total clicks | X | Y | Z | |
| Total calls | X | Y | Z | |
| Avg cost/call | Rs X | Rs Y | Rs Z | |

## Combined Summary
- Total daily spend: Rs X (Google Rs X + FB Rs X)
- Google budget remaining: Rs X
- FB monthly pace: Rs X/month

## Morning Audit Actions
- Suggestions created: X
- Suggestions approved: X
- Auto-actions taken: X
- Issues flagged: X

## Trends (7-Day)
- Google CPC: rising / falling / stable (X% change)
- Google CTR: rising / falling / stable
- FB avg frequency: rising / falling / stable
- FB best campaign: [name] at Rs X/call
- FB worst campaign: [name] at Rs X CPC

EVENING_REPORT_COMPLETE: {TIME} IST
```

### STEP 4: Update Changes Log

Append a day summary to `/root/ads/ads-changes-log.md`:
```markdown
### DAY SUMMARY — {DATE}
- Google spend: Rs X | FB spend: Rs X | Total: Rs X
- Auto-actions: X | Suggestions: X pending, X approved
- Notable: [any significant events]
```

### STEP 5: Send Telegram Summary

```bash
python3 /root/stocks/notify.py send "SUMMARY" --title "Daily Ads Report" --audience girish
```

**Message format:**
```
Daily Ads Report — {DATE}

GOOGLE ADS:
  Clicks: X (trend) | CTR: X% | CPC: Rs X
  Spend: Rs X | Conv: X
  Budget: Rs X remaining

FB ADS:
  Spend: Rs X across N campaigns
  Best: [campaign] Rs X/call
  Total calls: X

COMBINED: Rs X/day total spend
Month projected: Rs X (Google) + Rs X (FB) = Rs X

[If suggestions pending: X suggestions waiting — "ads suggestions"]
[If trends concerning: flag them]
```

Use `--priority high` if any concerning trends or budget issues, default otherwise.
