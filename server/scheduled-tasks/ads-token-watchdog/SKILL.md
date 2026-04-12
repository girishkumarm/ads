---
name: ads-token-watchdog
description: Daily 11:30 PM IST — Test Google and FB auth tokens, check FB token expiry, alert on upcoming expiration or auth failure.
---

## TOKEN WATCHDOG — AUTH HEALTH & EXPIRY MONITORING

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: No Gate Check Needed

This task always runs — token health is critical infrastructure.

### STEP 1: Test Google Auth

```bash
python3 /root/ads/ads_api.py auth google
```

**If success:**
- Record as GOOGLE_AUTH: OK
- Run a simple API call to verify token works end-to-end:
  ```bash
  python3 /root/ads/ads_api.py google budget
  ```

**If failure:**
- Record as GOOGLE_AUTH: FAILED
- Send CRITICAL alert:
  ```bash
  python3 /root/stocks/notify.py send "CRITICAL: Google Ads auth FAILED.

  Troubleshooting:
  1. Check if OAuth refresh token expired
  2. Verify credentials in ads-config.json
  3. Try: rm -f .ads-token.json && python3 /root/ads/ads_api.py auth google
  4. If still failing, may need to re-authorize via browser

  Ads WILL STOP if this isn't fixed before morning audit." --title "Google Auth Failed" --priority urgent --audience girish
  ```

### STEP 2: Test Facebook Auth

```bash
python3 /root/ads/ads_api.py auth facebook
```

**If success:**
- Record as FB_AUTH: OK
- The `auth facebook` command already outputs token validity and days until expiry.
  Extract expiry info from the auth output (it calls `fb_debug_token` internally).

**If failure:**
- Record as FB_AUTH: FAILED
- Send CRITICAL alert:
  ```bash
  python3 /root/stocks/notify.py send "CRITICAL: Facebook Ads auth FAILED.

  Troubleshooting:
  1. FB long-lived tokens last ~60 days
  2. Check if token in ads-config.json is still valid
  3. May need to generate new token at developers.facebook.com
  4. Generate new token at developers.facebook.com and update ads-config.json

  FB ads monitoring is DOWN until this is fixed." --title "FB Auth Failed" --priority urgent --audience girish
  ```

### STEP 3: FB Token Expiry Countdown

If FB auth succeeded and token expiry date is available:

Calculate days until expiry.

- **> 30 days** → OK, no action
- **14-30 days** → INFO: note in report
- **7-14 days** → HIGH alert:
  ```bash
  python3 /root/stocks/notify.py send "FB token expires in {N} days ({EXPIRY_DATE}).

  Please refresh before it expires:
  1. Go to developers.facebook.com
  2. Generate new long-lived token
  3. Update ads-config.json

  Or reply 'refresh fb token' for guided steps." --title "FB Token Expiring Soon" --priority high --audience girish
  ```
- **3-7 days** → CRITICAL:
  ```bash
  python3 /root/stocks/notify.py send "CRITICAL: FB token expires in {N} days!

  All FB ad management will STOP on {EXPIRY_DATE}.
  This needs immediate attention.

  Steps to refresh:
  1. Go to developers.facebook.com → Tools → Access Token Tool
  2. Generate new long-lived user token with ads_management permission
  3. Update /root/ads/ads-config.json with new token

  Reply 'refresh fb token' if you need help." --title "FB Token Critical" --priority urgent --audience girish
  ```
- **< 3 days** → CRITICAL with daily reminder:
  ```bash
  python3 /root/stocks/notify.py send "URGENT: FB token expires in {N} DAYS! ({EXPIRY_DATE})

  FB ad automation will BREAK. Fix this TODAY." --title "FB TOKEN EXPIRING" --priority urgent --audience girish
  ```

### STEP 4: Test GBP Auth (If Configured)

```bash
python3 /root/ads/ads_api.py gbp account
```

If fails, note it but don't send urgent alert (GBP is lower priority than ads).

### STEP 5: Send Summary

**If all OK and no expiry concerns:**
```bash
python3 /root/stocks/notify.py send "Token Watchdog — {DATE}
Google Auth: OK
FB Auth: OK (expires in {N} days)
GBP Auth: {OK/N/A}
All systems healthy." --title "Token Health" --audience girish
```

**If any issues:**
Priority escalation already handled in steps above. Send consolidated summary with all issues.

### CLEANUP
No browser used. No locks. Auth-only checks.
