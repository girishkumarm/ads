---
name: ads-budget-optimizer
description: Daily 9:30 AM IST weekdays — Auto-optimize Cafe FB campaign budgets based on 7-day cost-per-call efficiency. Resort = suggest only.
---

## BUDGET OPTIMIZER — COST-PER-CALL BASED BUDGET SHIFTING

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### AUTHORITY RULES

- **Cafe campaigns** (name contains BUS/Cafe/BTM/Jayanagar/Venue) → **FULL AUTO** — can adjust budgets
- **Resort campaigns** (name contains Namooru/Resort/Ecostay) → **APPROVAL ONLY** — write suggestion to `ads-suggestions.md`
- **If unclear** → **APPROVAL ONLY**
- **Max one budget change per campaign per day** — check `ads-changes-log.md` before acting

### STEP 0: Gate Check

1. Set DATE variable.
2. Check if it's a weekday: `TZ='Asia/Kolkata' date +%u` — if 6 or 7, skip.
3. Check `ads-changes-log.md` for any budget changes made today — if this task already ran today, skip.
4. Verify FB auth:
   ```bash
   python3 /root/ads/ads_api.py auth facebook
   ```

### STEP 1: Pull 7-Day Cost-Per-Call Data

```bash
python3 /root/ads/ads_api.py fb campaigns
```

For each ACTIVE campaign:
```bash
python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 7
```

Build a ranking table:
| Campaign | Type (Cafe/Resort) | 7d Spend | 7d Calls | Cost/Call | Daily Budget | Efficiency Rank |
|----------|-------------------|----------|----------|-----------|--------------|-----------------|

**Sort by cost-per-call ascending** (lowest = most efficient = rank 1).
Campaigns with 0 calls in 7 days get rank = LAST (worst).

### STEP 2: Determine Budget Shifts

**Rules:**
1. Identify the BEST performer (rank 1) and WORST performer (last rank) among Cafe campaigns
2. Only shift if there are at least 2 Cafe campaigns with data
3. Only shift if the cost-per-call difference between best and worst is > 20%
4. Shift amount: +20% budget to best, -20% budget from worst
5. Minimum budget floor: Rs 100/day — never reduce below this
6. Maximum budget ceiling: Rs 2,000/day — never increase above this
7. **Max one change per campaign per day** — check `ads-changes-log.md`

**Calculate:**
```
best_new_budget = best_current_budget * 1.20  (cap at Rs 2,000)
worst_new_budget = worst_current_budget * 0.80  (floor at Rs 100)
```

### STEP 3: Execute Changes

**FOR CAFE CAMPAIGNS — FULL AUTO:**
```bash
# Increase best performer's budget
python3 /root/ads/ads_api.py fb set-budget {BEST_CAMPAIGN_ID} {NEW_BUDGET}

# Decrease worst performer's budget
python3 /root/ads/ads_api.py fb set-budget {WORST_CAMPAIGN_ID} {NEW_BUDGET}
```

Log to `/root/ads/ads-changes-log.md`:
```markdown
## {DATE}

### AUTO: Budget optimization — cost-per-call shift
- INCREASED: [BEST_CAMPAIGN_NAME] (ID: {ID}) budget Rs {OLD} → Rs {NEW} (+20%)
  - Reason: Best cost/call at Rs {X}/call over 7 days
- DECREASED: [WORST_CAMPAIGN_NAME] (ID: {ID}) budget Rs {OLD} → Rs {NEW} (-20%)
  - Reason: Worst cost/call at Rs {X}/call over 7 days (or 0 calls)
- Time: {TIME} IST
```

**FOR RESORT CAMPAIGNS — SUGGESTION ONLY:**
Write to `/root/ads/ads-suggestions.md`:
```markdown
## SGG-{DATE}-BO-{SEQ} [PENDING]
Platform: Facebook Ads (Resort)
Type: Budget optimization
Detail: [CAMPAIGN_NAME] has cost/call Rs X (worst among resort campaigns). Suggest reducing budget by 20% from Rs {OLD} to Rs {NEW}.
Best resort campaign: [NAME] at Rs X/call — suggest increasing by 20%.
Suggested action: fb set-budget {CAMPAIGN_ID} {NEW_BUDGET}
Created: {DATE} {TIME}
```

### STEP 4: Send Telegram Summary

```bash
python3 /root/stocks/notify.py send "SUMMARY" --title "Budget Optimizer" --audience girish
```

**Message format:**
```
Budget Optimizer — {DATE}

CAFE CAMPAIGNS (AUTO):
  Best: [NAME] — Rs X/call — budget Rs {OLD} → Rs {NEW}
  Worst: [NAME] — Rs X/call — budget Rs {OLD} → Rs {NEW}
  {Or "No changes needed — performance spread < 20%"}

RESORT CAMPAIGNS (SUGGESTIONS):
  {N suggestions created — reply "ads suggestions" to review}
  {Or "No resort campaigns active"}

Efficiency ranking:
1. [NAME] — Rs X/call
2. [NAME] — Rs X/call
...
```

### STEP 5: Log Completion

Append to `ads-report-{DATE}.md`:
```
BUDGET_OPTIMIZER_COMPLETE: {TIME} IST
Changes: {N auto-changes, M suggestions}
```

### CLEANUP
No browser used. No locks. Budget changes are logged for verification by morning audit Agent 7.
