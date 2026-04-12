---
name: ads-monthly-rollup
description: 1st of each month 3:30 AM IST — Generate comprehensive monthly report with totals, trends, MoM comparison, budget efficiency.
---

## MONTHLY ROLLUP — COMPREHENSIVE MONTHLY REPORT

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Check

1. Set DATE variable.
2. Verify it's the 1st of the month: `TZ='Asia/Kolkata' date +%d` — if not "01", skip.
3. Determine REPORT_MONTH: the PREVIOUS month (since this runs on the 1st, report covers last month).
   ```bash
   TZ='Asia/Kolkata' date -d "yesterday" +%Y-%m   # Linux
   # Or: TZ='Asia/Kolkata' date -v-1d +%Y-%m       # macOS
   ```
4. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```

### STEP 1: Gather Monthly Data

**From daily reports:**
Read all `ads-report-{REPORT_MONTH}-*.md` files for the report month.
Extract daily metrics for each day.

**From ads-metrics-history.json:**
Read weekly snapshots for the report month.

**From API (for any gaps — query BOTH Google Ads accounts: Resort CID 2995160429 + Cafe CID 7614460903):**
```bash
# Google — full month (run for BOTH accounts)
python3 /root/ads/ads_api.py google campaigns   # For each account
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 30

# Facebook — full month
python3 /root/ads/ads_api.py fb campaigns
python3 /root/ads/ads_api.py fb account-spend 30
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 30
```

**From ads-changes-log.md:**
Count all auto-actions and suggestions for the month.

### STEP 2: Compute Monthly Aggregates

**Google Ads:**
- Total spend
- Total clicks / impressions
- Average CTR, CPC
- Total conversions
- Cost per conversion
- Budget utilization (actual spend vs allocated budget * days)

**Facebook Ads (per campaign and total):**
- Total spend
- Total clicks / impressions
- Average CTR, CPC, CPM
- Total calls (if available)
- Average cost per call
- Average frequency

**Combined:**
- Total ad spend (Google + FB)
- Total customer actions (conversions + calls)
- Blended cost per action

### STEP 3: Month-over-Month Comparison

Read previous month's report: `ads-monthly-{PREV_MONTH}.md` (if exists).

Compute MoM changes:
- Spend: +/-X%
- Clicks: +/-X%
- Conversions/Calls: +/-X%
- CPC: +/-X%
- CTR: +/-X%
- Cost per action: +/-X%

### STEP 4: Campaign Rankings

**Best performers:**
- Lowest cost-per-call campaign
- Highest CTR campaign
- Best ROI campaign (if conversion value available)

**Worst performers:**
- Highest CPC campaign
- Lowest CTR campaign
- Campaigns with zero conversions/calls

### STEP 5: Generate Report

Write to `/root/ads/ads-monthly-{REPORT_MONTH}.md`:

```markdown
# Monthly Ads Report — {REPORT_MONTH}

Generated: {DATE} {TIME} IST

## Executive Summary
- Total spend: Rs {X} (MoM: {+/-Y}%)
- Total customer actions: {X} (MoM: {+/-Y}%)
- Blended cost per action: Rs {X} (MoM: {+/-Y}%)
- Budget efficiency: {X}% utilized

## Google Ads — Namooru Ecostay Resort (CID 2995160429)

| Metric | This Month | Last Month | Change |
|--------|-----------|------------|--------|
| Spend | Rs X | Rs Y | +/-Z% |
| Clicks | X | Y | +/-Z% |
| Impressions | X | Y | +/-Z% |
| CTR | X% | Y% | +/-Z% |
| CPC | Rs X | Rs Y | +/-Z% |
| Conversions | X | Y | +/-Z% |
| Cost/Conv | Rs X | Rs Y | +/-Z% |

Budget remaining: Rs X
Fund depletion estimate: {DATE}

## Google Ads — BUS Cafe (CID 7614460903)

| Metric | This Month | Last Month | Change |
|--------|-----------|------------|--------|
| Spend | Rs X | Rs Y | +/-Z% |
| Clicks | X | Y | +/-Z% |
| Impressions | X | Y | +/-Z% |
| CTR | X% | Y% | +/-Z% |
| CPC | Rs X | Rs Y | +/-Z% |
| Conversions | X | Y | +/-Z% |
| Cost/Conv | Rs X | Rs Y | +/-Z% |

Budget remaining: Rs X

## Facebook Ads — BUS Cafe + Resort

### By Campaign:
| Campaign | Type | Spend | Clicks | CTR | CPC | Calls | Cost/Call |
|----------|------|-------|--------|-----|-----|-------|-----------|
| [name] | Cafe | Rs X | X | X% | Rs X | X | Rs X |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Totals:
| Metric | This Month | Last Month | Change |
|--------|-----------|------------|--------|
| Total spend | Rs X | Rs Y | +/-Z% |
| Total clicks | X | Y | +/-Z% |
| Total calls | X | Y | +/-Z% |
| Avg cost/call | Rs X | Rs Y | +/-Z% |
| Avg frequency | X | Y | +/-Z |

## Combined Summary
| | Google | Facebook | Total |
|--|--------|----------|-------|
| Spend | Rs X | Rs X | Rs X |
| Actions | X conv | X calls | X total |
| Cost/Action | Rs X | Rs X | Rs X |

## Automation Summary
- Auto-actions taken: {X}
- Suggestions created: {X}
- Suggestions approved: {X}
- Suggestions rejected: {X}
- Suggestions still pending: {X}
- A/B tests completed: {X}
- Creative rotations: {X}

## Top Performers
1. {Campaign} — Rs {X}/call (best efficiency)
2. {Campaign} — {X}% CTR (best engagement)

## Needs Attention
1. {Campaign} — {issue}
2. {Campaign} — {issue}

## Seasonal Notes
- {Any seasonal observations — holiday impact, weather, etc.}
- {Comparison to same month last year if data available}

## Recommendations for Next Month
- {Data-driven recommendation 1}
- {Data-driven recommendation 2}
- {Budget adjustment suggestions}
```

### STEP 6: Send Telegram Summary

```bash
python3 /root/stocks/notify.py send "SUMMARY" --title "Monthly Ads Report" --priority high --audience girish
```

**Message format:**
```
Monthly Ads Report — {REPORT_MONTH}

TOTALS:
  Spend: Rs {X} (MoM: {+/-Y}%)
  Google: Rs {X} | FB: Rs {X}
  Actions: {X} conv + {Y} calls = {Z} total
  Cost/action: Rs {X}

TOP PERFORMER:
  {Campaign} — Rs {X}/call

BUDGET:
  Google balance: Rs {X}
  Monthly burn: Rs {X}/month

AUTOMATION:
  {X} auto-actions, {Y} suggestions ({Z} approved)

Full report: ads-monthly-{REPORT_MONTH}.md
```

### CLEANUP
No browser used. All data aggregated from existing files and API queries.
