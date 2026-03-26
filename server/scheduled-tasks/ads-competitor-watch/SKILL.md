---
name: ads-competitor-watch
description: Sunday 2:30 AM IST — Google auction insights, competitor impression share trends, Google Maps review tracking.
---

## COMPETITOR WATCH — WEEKLY COMPETITIVE INTELLIGENCE

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Check

1. Set DATE variable.
2. Verify Google auth:
   ```bash
   python3 /root/ads/ads_api.py auth google
   ```
   If fails, notify and abort.

### STEP 1: Google Auction Insights

```bash
python3 /root/ads/ads_api.py google campaigns
```

For each ENABLED campaign:
```bash
python3 /root/ads/ads_api.py google auction-insights {CAMPAIGN_ID} 7
```

Extract for each competitor:
- Display URL / domain
- Impression share
- Overlap rate
- Position above rate
- Top of page rate

### STEP 2: Track Trends

Read `/root/ads/competitor-tracking.md` (create if doesn't exist).

Compare this week's data to last week's entry:
- Which competitors gained impression share? (> 5% increase)
- Which competitors lost impression share?
- Any NEW competitors appearing?
- Any competitors disappeared?

Update `/root/ads/competitor-tracking.md`:
```markdown
# Competitor Tracking

## Week of {DATE}

### Auction Insights — Campaign: {NAME}
| Competitor | Impression Share | vs Last Week | Overlap Rate | Position Above |
|------------|-----------------|--------------|--------------|----------------|
| {domain}   | {X}%            | +/-{Y}%      | {Z}%         | {W}%           |

### Notable Changes:
- {Competitor X} gained {Y}% impression share — possible budget increase
- {New competitor Z} appeared this week
```

### STEP 3: Google Maps Competitor Reviews

Check known competitors for review count changes. Search for each:
```bash
python3 /root/ads/ads_api.py gbp competitor-reviews "Wild Valley" "Hombale" "Kaadgal" "Club Cabana"
```

If the API doesn't support competitor review lookup directly, skip this step and note it in the report.

Track in `competitor-tracking.md`:
```markdown
### Google Maps Review Counts
| Competitor | Reviews | vs Last Week | Rating |
|------------|---------|--------------|--------|
| Namooru (us) | X | +Y | 4.X |
| Wild Valley | X | +Y | 4.X |
| Hombale | X | +Y | 4.X |
```

### STEP 4: Send Weekly Summary

```bash
python3 /root/stocks/notify.py send "Competitor Watch — Week of {DATE}

AUCTION INSIGHTS:
  Our impression share: {X}% (vs {Y}% last week)
  Top competitor: {NAME} at {Z}% impression share
  {Notable changes}

REVIEW COUNTS:
  Namooru: {X} reviews ({RATING})
  Top competitor: {NAME} with {Y} reviews

{If any competitor gained >10% impression share: flag as alert}
{If our impression share dropped >10%: flag as warning}" --title "Competitor Watch" --audience girish
```

Use `--priority high` if our impression share dropped significantly.

### CLEANUP
No browser used. All data stored in competitor-tracking.md for historical tracking.
