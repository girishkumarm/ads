---
name: ads-approval-reminder
description: Daily 1:30 PM IST — Re-send pending suggestions older than 6 hours. Escalate overdue (>48h) suggestions.
---

## APPROVAL REMINDER — PENDING SUGGESTION FOLLOW-UP

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.
TIME: Run `TZ='Asia/Kolkata' date +%H:%M` to get current IST time.

### STEP 0: Gate Check

1. Set DATE and TIME variables.
2. Read `/root/ads/ads-suggestions.md` — if file doesn't exist or is empty, skip with no notification.

### STEP 1: Parse Pending Suggestions

Read `/root/ads/ads-suggestions.md` and find all entries marked `[PENDING]`.

For each PENDING suggestion, extract:
- Suggestion ID (e.g., SGG-2026-03-25-01)
- Platform
- Type
- Detail (brief summary)
- Created timestamp

### STEP 2: Categorize by Age

Calculate age of each PENDING suggestion from its `Created` timestamp:

- **< 6 hours old** → Skip (too fresh, give Girish time)
- **6-48 hours old** → REMINDER — re-send to Telegram
- **> 48 hours old** → OVERDUE — escalate with urgency

### STEP 3: Send Reminders

**For suggestions 6-48 hours old:**
```bash
python3 /root/stocks/notify.py send "REMINDER: {N} pending ad suggestions need your review.

{For each suggestion:}
{SGG_ID}: {TYPE} — {BRIEF_DETAIL}

Reply 'ads approve {SGG_ID}' to approve
Reply 'ads reject {SGG_ID}' to reject
Reply 'ads suggestions' to see full details" --title "Pending Suggestions" --audience girish
```

**For suggestions > 48 hours old:**
```bash
python3 /root/stocks/notify.py send "OVERDUE: {N} ad suggestions have been waiting 48+ hours!

{For each overdue suggestion:}
OVERDUE {SGG_ID} ({AGE}h old): {TYPE} — {BRIEF_DETAIL}

These may be costing you money or missing opportunities. Please review ASAP.

Reply 'ads approve all' to approve all
Reply 'ads suggestions' to see full details" --title "OVERDUE Suggestions" --priority high --audience girish
```

### STEP 4: Summary

If there were any pending suggestions:
```bash
python3 /root/stocks/notify.py send "Suggestion status:
Fresh (<6h): {N} (not reminded yet)
Pending (6-48h): {N} (reminder sent)
OVERDUE (>48h): {N} (escalated)
Total pending: {N}" --title "Approval Status" --audience girish
```

If no pending suggestions exist, stay silent.

### CLEANUP
No browser used. No locks. Read-only check of ads-suggestions.md.
