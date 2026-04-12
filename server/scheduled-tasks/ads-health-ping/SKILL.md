---
name: ads-health-ping
description: Every 2 hours — Quick health checks: landing page uptime, FB ad disapprovals, Google balance. Critical alerts on failures.
---

## ADS HEALTH PING — QUICK INFRASTRUCTURE CHECK

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.
TIME: Run `TZ='Asia/Kolkata' date +%H:%M` to get current IST time.

### STEP 0: Gate Check

1. Set DATE and TIME variables.
2. This runs every 2 hours, so no dedup needed — always execute.
3. Verify at least one API auth works:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```
   If BOTH fail, send CRITICAL alert and abort:
   ```bash
   python3 /root/stocks/notify.py send "CRITICAL: Both Google and FB auth failed. Check credentials immediately." --title "Auth Failure" --priority urgent --audience girish
   ```

### STEP 1: Landing Page Uptime Check

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://namooru.com
```

**Checks:**
- HTTP status 200 → OK
- HTTP status 3xx → WARNING (redirect — check if intentional)
- HTTP status 4xx/5xx or timeout → **CRITICAL**

**If landing page is DOWN (non-200, non-3xx):**
1. Retry once after 30 seconds to confirm it's not a blip
2. If still down:
   ```bash
   python3 /root/stocks/notify.py send "CRITICAL: namooru.com is DOWN (HTTP {STATUS_CODE}). Landing page unreachable. Consider pausing ALL ads immediately to stop wasting spend." --title "SITE DOWN" --priority urgent --audience girish
   ```
3. Write suggestion to `/root/ads/ads-suggestions.md`:
   ```markdown
   ## SGG-{DATE}-HP-{SEQ} [PENDING]
   Platform: All
   Type: Emergency — pause all campaigns
   Detail: namooru.com returned HTTP {STATUS_CODE} at {TIME} IST
   Suggested action: Pause all Google and FB campaigns until site is back
   Impact: Prevents wasted ad spend on broken landing page
   Created: {DATE} {TIME}
   ```

### STEP 2: Facebook Ad Disapproval Check

```bash
python3 /root/ads/ads_api.py fb campaigns
```

For each ACTIVE campaign:
```bash
python3 /root/ads/ads_api.py fb ads {ADSET_ID}
```

**Check each ad's `effective_status` and `review_feedback`:**
- If any ad has status `DISAPPROVED` or `WITH_ISSUES`:
  - Parse the disapproval reason from review_feedback
  - Map common reasons to fix suggestions:
    - "Policy violation" → Review ad text/image for prohibited content
    - "Landing page issue" → Check namooru.com matches ad content
    - "Text in image" → Reduce text overlay to <20%
    - "Misleading claims" → Review ad copy for accuracy
  - Send alert:
    ```bash
    python3 /root/stocks/notify.py send "Ad DISAPPROVED in [CAMPAIGN_NAME]:
    Ad: [AD_NAME] (ID: [AD_ID])
    Reason: [DISAPPROVAL_REASON]
    Fix: [SUGGESTED_FIX]

    Review in Ads Manager or reply with instructions." --title "Ad Disapproved" --priority high --audience girish
    ```

### STEP 3: Zero-Spend Active Campaign Check (CRITICAL)

**IMPORTANT:** Never trust campaign status alone. An ACTIVE campaign can have zero delivery.

For BOTH Facebook and Google Ads, check each ACTIVE/ENABLED campaign:
- If a campaign is ACTIVE/ENABLED but has Rs 0 spend today (after 10 AM IST), flag as **CRITICAL**:
```bash
python3 /root/stocks/notify.py send "CRITICAL: Campaign [NAME] is ACTIVE but has Rs 0 spend today. Possible delivery issue — check billing, targeting, or ad disapprovals." --title "Zero Delivery" --priority urgent --audience girish
```

### STEP 4: Google Ads Balance Check (BOTH Accounts)

Check BOTH Google Ads accounts (Resort CID 2995160429 + Cafe CID 7614460903):
```bash
python3 /root/ads/ads_api.py google budget   # Run for each account
```

**Checks (per account):**
- Balance < Rs 3,000 → CRITICAL alert
- Balance < Rs 5,000 → HIGH alert
- Balance < Rs 10,000 → INFO note

**If CRITICAL:**
```bash
python3 /root/stocks/notify.py send "CRITICAL: Google Ads balance is Rs {BALANCE}. Ads will stop delivering soon. Top up immediately." --title "Google Funds Critical" --priority urgent --audience girish
```

### STEP 5: Send Summary (Only if Issues Found)

If any issues were detected:
```bash
python3 /root/stocks/notify.py send "Health Ping — {TIME} IST

Site: {OK/DOWN}
FB Ads: {X disapproved / all OK}
Google Balance: Rs {BALANCE} {OK/LOW/CRITICAL}

{Details of any issues}" --title "Health Ping" --priority {PRIORITY} --audience girish
```

If everything is OK, stay silent (no need to spam Telegram every 2 hours with "all good").

### CLEANUP
No browser used. No locks. Lightweight check — should complete in under 60 seconds.
