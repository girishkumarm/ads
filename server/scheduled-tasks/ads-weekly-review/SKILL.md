---
name: ads-weekly-review
description: Monday 5:47 AM IST — Deep weekly analysis, week-over-week trends, strategy review
---

## WEEKLY ADS REVIEW

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
STRATEGY DOCS: /root/ads-management/
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d`

### STEP 0: Gate Checks

1. Set DATE. Confirm it's Monday: `TZ='Asia/Kolkata' date +%A` should be "Monday"
2. Verify APIs: `python3 /root/ads/ads_api.py auth google && python3 /root/ads/ads_api.py auth facebook`

### STEP 1: Collect Week's Data

**Read daily reports from past 7 days:**
```bash
# Read ads-report-{DATE}.md for each of the last 7 days
# Extract: daily spend, clicks, CTR, CPC, conversions, calls
```

**Pull fresh 14-day and 30-day data for BOTH Google Ads accounts (Resort CID 2995160429 + Cafe CID 7614460903):**
```bash
# Google — run for BOTH accounts
python3 /root/ads/ads_api.py google campaigns   # For each account
python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 14
python3 /root/ads/ads_api.py google search-terms {CAMPAIGN_ID} 14
python3 /root/ads/ads_api.py google keywords {CAMPAIGN_ID}
python3 /root/ads/ads_api.py google budget   # For each account
python3 /root/ads/ads_api.py google recommendations

# Facebook — per campaign
python3 /root/ads/ads_api.py fb campaigns
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 14
python3 /root/ads/ads_api.py fb frequency {CAMPAIGN_ID}
python3 /root/ads/ads_api.py fb demographics {CAMPAIGN_ID}
python3 /root/ads/ads_api.py fb account-spend 30
```

### STEP 2: Week-Over-Week Analysis

Compute for each metric:
- **This week** (last 7 days) vs **Previous week** (days 8-14)
- Calculate % change
- Flag any metric that changed > 20%

**Metrics to compare:**
| Metric | This Week | Last Week | Change % | Status |
|--------|-----------|-----------|----------|--------|
| Google clicks | | | | |
| Google CTR | | | | |
| Google CPC | | | | |
| Google conversions | | | | |
| Google spend | | | | |
| FB total spend | | | | |
| FB total clicks | | | | |
| FB avg CTR | | | | |
| FB avg CPC | | | | |
| FB total calls | | | | |
| FB avg cost/call | | | | |
| FB avg frequency | | | | |

### STEP 3: Creative Performance Ranking (Facebook)

For each campaign, rank ads by performance:
```bash
# For each campaign → each adset → each ad:
python3 /root/ads/ads_api.py fb ad-metrics {AD_ID} 14
```

Rank by: CTR (primary), CPC (secondary), frequency (lower is better)

**Identify:**
- Top 3 performing ads (to keep running)
- Bottom 3 performing ads (candidates for pause/replace)
- Ads with frequency > 2.5 approaching fatigue
- Any ad paused for > 14 days that could be brought back

### STEP 4: Google Search Terms Deep Dive

Using 14-day search terms data:
1. **Top wasted spend terms** — clicks but no conversions, ranked by spend
2. **Top opportunity terms** — high CTR search terms not in keyword list
3. **Emerging trends** — terms that appeared this week but not last week
4. **Competitor activity** — any competitor name searches increasing?

Compare against `/root/ads-management/google-ads/keywords-and-negatives.md`:
- How many of the recommended 25 new keywords have been added?
- How many of the 220 recommended negatives are still missing?
- Track progress on the action plan items

### STEP 5: Strategy Doc Review

Read and compare current performance against strategy targets:

**Google Ads (from `/root/ads-management/google-ads/action-plan.md`):**
- P0 items completed? (funds, bid strategy, AI Max)
- P1 items progress? (25 keywords, 26 competitor negatives)
- P2 items progress? (220 negative keywords)
- P3 items started? (Corporate Outings campaign, Glamping campaign)

**Facebook Ads (from `/root/ads-management/fb-ads/cafe-ad-strategy.md`):**
- Is targeting aligned with strategy (22-35, 3-5km radius)?
- Are seasonal campaigns running per the calendar?
- Video rotation on schedule per ad-fatigue-rotation.md?
- Meta Pixel setup progress?

**Generate strategy recommendations:**
- What strategy items should be prioritized next week?
- Any strategy items no longer relevant?
- New opportunities discovered from data?

### STEP 6: Budget Efficiency Analysis

Calculate for each platform:
- **Cost per conversion** (Google: cost per call/contact, FB: cost per call)
- **ROAS estimate** (if conversion values available)
- **Budget utilization %** (actual spend / allocated budget)
- **Projected monthly spend** at current rate
- **Google account fund runway** (days until depletion)

Flag if:
- Cost per conversion increasing week-over-week
- Budget utilization below 80% (delivery issues)
- Google funds insufficient for the month

### STEP 7: Generate Weekly Review

Write to `/root/ads/ads-weekly-review-{DATE}.md`:

```markdown
# Weekly Ads Review — Week of {DATE}

## Executive Summary
[2-3 sentence overview of the week: what went well, what needs attention]

## Week-Over-Week Metrics
[Table from Step 2]

## Google Ads — Namooru Ecostay (CID 2995160429)
### Performance
[Weekly totals vs previous week]
### Search Terms Analysis
- Wasted spend: Rs X on irrelevant terms
- New opportunities: [list]
- Negatives still needed: X of 220
### Action Plan Progress
- P0: [status]
- P1: [status]
- P2: [status]

## Google Ads — BUS Cafe (CID 7614460903)
### Performance
[Weekly totals vs previous week]

## Facebook Ads — BUS Cafe
### Performance by Campaign
[Ranked table of all campaigns]
### Creative Performance
- Top performers: [list]
- Fatigued/paused: [list]
- Creative needs: [how many new videos/images needed]
### Targeting Review
[Demographics and placement analysis]

## Budget Summary
- Google Resort: Rs X spent this week, Rs X remaining in account
- Google Cafe: Rs X spent this week, Rs X remaining in account
- Facebook: Rs X spent this week, Rs X/month projected
- Combined: Rs X/week, Rs X/month projected

## Recommendations for Next Week
1. [Highest priority recommendation]
2. [Second priority]
3. [Third priority]
...

## Strategy Alignment
[Which strategy doc items are on track, which are behind]
```

### STEP 8: Send Telegram Summary

```bash
python3 /root/stocks/notify.py send "SUMMARY" --title "Weekly Ads Review" --priority high --audience girish
```

**Message format:**
```
Weekly Ads Review — {DATE}

GOOGLE ADS:
  This week: X clicks, Rs X spend, X conv
  vs last week: [up/down X%]
  Budget: Rs X remaining (X days)
  Suggestions: X pending

FB ADS:
  This week: Rs X spend, X calls
  vs last week: [up/down X%]
  Top campaign: [name] Rs X/call
  Creatives: X active, X need rotation

COMBINED: Rs X/week → Rs X/month projected

TOP 3 PRIORITIES:
1. [most important]
2. [second]
3. [third]

Full review: ads-weekly-review-{DATE}.md
```

### STEP 9: Update ads-management Repo

If the review identified strategy updates needed, push changes to the ads-management repo:
```bash
cd /root/ads-management
# Update relevant .md files with new findings
git add -A && git commit -m "weekly review: update metrics and recommendations ({DATE})"
git push origin master
```

Only update strategy docs if there are concrete, data-driven changes (not speculative).
