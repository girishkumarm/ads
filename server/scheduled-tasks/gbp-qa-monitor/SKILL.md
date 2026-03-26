---
name: gbp-qa-monitor
description: Daily 10:30 AM IST — Check GBP for new Q&A questions, draft answers for approval. Auto-suggest for common topics.
---

## GBP Q&A MONITOR — QUESTION DETECTION & DRAFT REPLIES

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### AUTHORITY: DRAFT ONLY — ALL REPLIES NEED APPROVAL

- Reading Q&A: AUTO
- Drafting answers: AUTO (draft only, never post)
- Posting answers: **APPROVAL REQUIRED** — send to Telegram, wait for Girish

### STEP 0: Gate Check

1. Set DATE variable.
2. Verify GBP auth:
   ```bash
   python3 /root/ads/ads_api.py gbp account
   ```
   If fails or not configured, notify and abort.

### STEP 1: Fetch Q&A

```bash
python3 /root/ads/ads_api.py gbp questions
```

Identify questions that:
- Have NO answer from the business owner
- Were asked in the last 7 days

### STEP 2: Draft Answers

For each unanswered question, draft a helpful, professional response.

**Common topic templates (customize based on actual question):**

**Check-in / Check-out times:**
> "Check-in time is 2:00 PM and check-out is 11:00 AM. Early check-in and late check-out may be available based on occupancy — please call us to check."

**Pet policy:**
> "Yes, Namooru Ecostay is pet-friendly! We welcome well-behaved pets. There may be a nominal cleaning fee. Please inform us at the time of booking."

**Distance from Bangalore:**
> "Namooru Ecostay is approximately 60 km from Bangalore city center, about a 1.5-2 hour drive via NH44. We're located near Doddaballapur."

**Activities available:**
> "We offer swimming pool, outdoor games, bonfire, nature walks, bird watching, and more. The property is spread across 5 acres with lush greenery. Perfect for a weekend getaway!"

**Food / catering:**
> "We provide home-style vegetarian and non-vegetarian meals. Breakfast, lunch, and dinner can be arranged. Please inform us about dietary preferences when booking."

**Booking / pricing:**
> "For the latest rates and availability, please call us directly or book through our website namooru.com. We offer packages for families, couples, and groups."

**For questions that don't match common topics:**
Draft a custom response that is:
- Friendly and professional
- Factually accurate based on known business info
- Under 200 characters if possible (GBP has limits)
- Includes a call-to-action (call us, visit website)

### STEP 3: Send Drafts for Approval

For each question with a draft answer:
```bash
python3 /root/stocks/notify.py send "New GBP Question:
Q: \"{QUESTION_TEXT}\"
Asked by: {AUTHOR_NAME} on {DATE}

Suggested answer:
\"{DRAFT_ANSWER}\"

To approve: reply 'gbp answer {QUESTION_ID} {ANSWER_TEXT}'
To edit: reply with your preferred answer
To skip: ignore this message" --title "GBP Question" --priority high --audience girish
```

**DO NOT post any answer automatically. Wait for Girish's explicit approval.**

### STEP 4: Check for Spam / Inappropriate Questions

Flag questions that appear to be:
- Spam (links, promotional content)
- Competitor sabotage (misleading information)
- Inappropriate content

If found:
```bash
python3 /root/stocks/notify.py send "Suspicious GBP Q&A detected:
Q: \"{QUESTION_TEXT}\"

This appears to be {spam/competitor/inappropriate}. Consider reporting it on Google Maps.

To report: Go to Google Maps → Namooru Ecostay → Q&A → Flag this question" --title "Suspicious GBP Q&A" --priority high --audience girish
```

### STEP 5: Daily Summary

```bash
python3 /root/stocks/notify.py send "GBP Q&A — {DATE}

New questions: {N}
Drafts sent for approval: {N}
Previously unanswered (>7d): {N}
Flagged (spam/suspicious): {N}

{If N=0: 'No new questions today.'}" --title "GBP Q&A" --audience girish
```

### CLEANUP
No browser used. No locks. All answers require human approval before posting.
