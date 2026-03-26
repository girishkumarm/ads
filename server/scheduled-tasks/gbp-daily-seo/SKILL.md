---
name: gbp-daily-seo
description: Daily 7:30 AM IST — Monitor Google Business Profile for Namooru Ecostay Resort. Check reviews, Q&A, insights. Draft replies for approval.
---

## GOOGLE BUSINESS PROFILE — DAILY SEO CHECK

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.
DAY OF WEEK: Run `TZ='Asia/Kolkata' date +%u` (1=Monday, 7=Sunday)
DAY OF MONTH: Run `TZ='Asia/Kolkata' date +%d`

### AUTHORITY: AUTO SEO + APPROVAL FOR REPLIES

- Reading data: AUTO (no approval needed)
- Monitoring insights: AUTO
- Drafting review replies: DRAFT ONLY — send to Telegram for Girish to approve
- Creating Google Posts: DRAFT ONLY — send to Telegram for approval
- Updating business info: ASK FIRST — suggest via Telegram

### STEP 0: Gate Check

1. Verify Google auth works:
   ```bash
   python3 /root/ads/ads_api.py auth google
   ```
   If fails, notify and abort.

2. Check if GBP credentials are configured:
   ```bash
   python3 /root/ads/ads_api.py gbp account
   ```
   If "not configured" error, notify Girish that GBP setup is needed and abort.

### STEP 1: Check New Reviews

```bash
python3 /root/ads/ads_api.py gbp reviews
```

For each review found:
- If **no reply exists** and review is **less than 7 days old**:
  - Draft a professional, warm reply that:
    - Thanks the guest by name
    - References something specific from their review
    - Invites them back
    - Keeps it under 100 words
  - Send draft to Telegram for approval:
    ```bash
    python3 /root/stocks/notify.py send "New review from [AUTHOR] (⭐ [RATING]):
    \"[REVIEW_TEXT]\"

    Suggested reply:
    \"[DRAFT_REPLY]\"

    To approve: reply 'gbp reply [REVIEW_ID] [REPLY_TEXT]'
    To skip: ignore this message" --title "GBP Review Reply" --priority high --audience girish
    ```
  - **DO NOT post the reply automatically.** Wait for Girish's approval via Telegram.

- If review is **negative (1-2 stars)**:
  - Flag as URGENT
  - Draft an empathetic reply acknowledging the issue
  - Use `--priority urgent` in Telegram notification

### STEP 2: Monitor Insights (Daily)

```bash
python3 /root/ads/ads_api.py gbp insights 7
```

Track week-over-week trends:
- Total views (maps + search)
- Total searches
- Direction requests
- Phone calls
- Website clicks

If any metric **dropped > 20%** vs previous week, flag in Telegram:
```bash
python3 /root/stocks/notify.py send "GBP Alert: [METRIC] dropped [X]% this week vs last week" --title "GBP Insights" --priority high --audience girish
```

### STEP 3: Weekly Post Suggestion (Monday Only)

Check day of week. If Monday (`date +%u` = 1):

1. Read business info: `python3 /root/ads/ads_api.py gbp info`
2. Consider seasonal context (check current month/upcoming holidays)
3. Draft a Google Post:
   - Keep under 300 characters
   - Include a call-to-action (Book now, Visit us, Call us)
   - Rotate topics: amenities, nature, activities, events, offers, testimonials
4. Send to Telegram for approval:
   ```bash
   python3 /root/stocks/notify.py send "Weekly GBP Post suggestion:

   \"[DRAFT_POST_TEXT]\"

   To post: reply 'gbp post [TEXT]'" --title "GBP Weekly Post" --audience girish
   ```

### STEP 4: Monthly Business Info Audit (1st of Month)

Check day of month. If 1st (`date +%d` = 01):

1. Fetch current info: `python3 /root/ads/ads_api.py gbp info`
2. Check:
   - Business hours match reality (especially holiday/seasonal changes)
   - Description is up-to-date and keyword-rich
   - Contact info is correct
   - Categories are appropriate
   - Photos are recent (suggest adding new ones if stale)
3. If anything needs updating, send suggestions via Telegram

### STEP 5: Send Daily Summary

```bash
python3 /root/stocks/notify.py send "GBP Daily Check — {DATE}

Reviews: [X new, Y total] [Z pending reply]
Insights (7d): [views] views, [searches] searches, [calls] calls
[Any alerts or suggestions]" --title "GBP Daily" --audience girish
```

### CLEANUP
No browser used. No locks. All state tracked via GBP API.
