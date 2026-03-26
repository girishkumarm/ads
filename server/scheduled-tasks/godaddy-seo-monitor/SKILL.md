---
name: godaddy-seo-monitor
description: Weekly Monday 6:00 AM IST — Check namooru.com DNS, SSL, domain status. Alert on expiry. Suggest SEO improvements only when asked.
---

## GODADDY — WEEKLY SEO & DOMAIN MONITOR

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### AUTHORITY LEVELS
- DNS record checks: AUTO (read-only monitoring)
- SSL certificate checks: AUTO (read-only)
- Domain expiry checks: AUTO (read-only)
- DNS record changes: ASK FIRST (suggest via Telegram, wait for approval)
- Website content changes: MANUAL ONLY (never touch — Girish does this himself)

### STEP 0: Gate Check

1. Verify GoDaddy API credentials:
   ```bash
   python3 /root/ads/ads_api.py godaddy domain
   ```
   If "not configured" error, notify Girish that GoDaddy API key is needed and abort.

### STEP 1: Domain Health Check

```bash
python3 /root/ads/ads_api.py godaddy domain
```

**Checks:**
- **Domain expiry < 60 days** → WARNING notification
- **Domain expiry < 30 days** → CRITICAL notification
- **Auto-renew disabled** → WARNING (should always be on)
- **Domain locked** → Good (prevents unauthorized transfers)

### STEP 2: SSL Certificate Check

```bash
python3 /root/ads/ads_api.py godaddy ssl
```

**Checks:**
- **SSL expires < 30 days** → WARNING notification
- **SSL expires < 7 days** → CRITICAL notification (site will break!)
- **SSL not found / error** → CRITICAL notification

If CRITICAL:
```bash
python3 /root/stocks/notify.py send "🚨 CRITICAL: SSL certificate for namooru.com expires in [X] days! Renew immediately." --title "SSL Expiry Alert" --priority urgent --audience girish
```

### STEP 3: DNS Records Audit

```bash
python3 /root/ads/ads_api.py godaddy dns
```

**Verify these records exist and are correct:**
- **A record** → Points to hosting IP (verify site loads)
- **CNAME www** → Points to domain or hosting
- **MX records** → Email routing (if using custom email)
- **TXT records:**
  - SPF record (`v=spf1...`) → Email deliverability
  - DKIM record → Email authentication
  - DMARC record (`_dmarc`) → Email security
  - Google site verification → For Google Search Console / GBP

**Flag if missing:**
- No SPF record → Suggest adding (emails may go to spam)
- No DMARC record → Suggest adding
- No Google verification TXT → Suggest adding for Search Console

**DO NOT add DNS records automatically.** Always suggest via Telegram:
```bash
python3 /root/stocks/notify.py send "DNS Suggestion: [DESCRIPTION]
Record: [TYPE] [NAME] → [VALUE]
Reason: [WHY]
To approve: reply 'godaddy dns-add [TYPE] [NAME] [VALUE]'" --title "DNS Suggestion" --audience girish
```

### STEP 4: SEO Quick Check (via HTTP)

Check namooru.com basic SEO health:
```bash
# Check if site loads and has proper headers
curl -sI https://namooru.com | head -20
```

**Check for:**
- HTTP → HTTPS redirect working
- Proper status code (200)
- X-Frame-Options header present
- Content-Security-Policy present
- Cache-Control headers

If issues found, notify Girish with specifics.

### STEP 5: Send Weekly Summary

```bash
python3 /root/stocks/notify.py send "GoDaddy Weekly Check — {DATE}

Domain: namooru.com
  Expires: [DATE] ([X] days)
  Auto-renew: [YES/NO]

SSL: [OK/WARNING/CRITICAL]
  Expires: [DATE] ([X] days)

DNS: [X] records
  SPF: [✓/✗]
  DMARC: [✓/✗]

[Any suggestions or alerts]" --title "Domain Health" --audience girish
```

### CLEANUP
No browser used. No locks. Pure API + HTTP checks.
