---
name: ads-creative-health
description: Mon/Thu 8:30 AM IST — Verify all active ad destination URLs return 200, check UTM parameters exist. Alert on broken links.
---

## CREATIVE HEALTH — DESTINATION URL & UTM VALIDATION

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Check

1. Set DATE variable.
2. Check day of week: `TZ='Asia/Kolkata' date +%u`
   - 1 (Monday) or 4 (Thursday) → proceed
   - Otherwise → skip
3. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```

### STEP 1: Check Facebook Ad Destination URLs

```bash
python3 /root/ads/ads_api.py fb campaigns
```

For each ACTIVE campaign:
```bash
python3 /root/ads/ads_api.py fb adsets {CAMPAIGN_ID}
```

For each ACTIVE adset:
```bash
python3 /root/ads/ads_api.py fb ads {ADSET_ID}
```

For each ACTIVE ad, extract the destination URL (website_url or link field).

**Check each URL:**
```bash
curl -s -o /dev/null -w "%{http_code}" -L --max-time 15 "{DESTINATION_URL}"
```

**Checks:**
- HTTP 200 → OK
- HTTP 3xx → WARNING: redirect chain — verify final destination is correct
- HTTP 4xx/5xx → **BROKEN LINK** — alert immediately
- Timeout → **BROKEN LINK** — alert

**Check UTM parameters exist:**
Parse the URL for:
- `utm_source` (should exist — e.g., facebook)
- `utm_medium` (should exist — e.g., paid_social)
- `utm_campaign` (should exist — matches campaign name)

If any UTM parameter is missing, flag as WARNING.

### STEP 2: Check Google Ads Final URLs

```bash
python3 /root/ads/ads_api.py google campaigns
```

For each ENABLED campaign:
```bash
python3 /root/ads/ads_api.py google ads {CAMPAIGN_ID}
```

For each ENABLED ad, extract `final_urls`.

**Check each URL:**
```bash
curl -s -o /dev/null -w "%{http_code}" -L --max-time 15 "{FINAL_URL}"
```

Same checks as FB: 200 = OK, 4xx/5xx = BROKEN, timeout = BROKEN.

**Check for Google tracking template:**
Verify the ad or campaign has a tracking template with UTM parameters.

### STEP 3: Build Results

Compile results:
```
CREATIVE_HEALTH:
  FB ADS:
    Total active ads checked: X
    URLs OK: X
    URLs BROKEN: X [list with ad name, campaign, URL, HTTP status]
    UTM missing: X [list with ad name, missing params]
  GOOGLE ADS:
    Total active ads checked: X
    URLs OK: X
    URLs BROKEN: X [list with ad name, campaign, URL, HTTP status]
    Tracking template missing: X [list]
```

### STEP 4: Send Alerts

**If any broken links found:**
```bash
python3 /root/stocks/notify.py send "BROKEN AD LINKS FOUND:

{For each broken link:}
Platform: {Google/FB}
Campaign: {NAME}
Ad: {AD_NAME} (ID: {AD_ID})
URL: {URL}
Status: HTTP {CODE}

These ads are sending users to broken pages. Fix URLs or pause ads immediately." --title "Broken Ad Links" --priority urgent --audience girish
```

**If only UTM issues:**
```bash
python3 /root/stocks/notify.py send "Creative Health — {DATE}

All links working. {N} UTM issues found:
{List missing UTMs}

UTM tracking helps attribute conversions correctly." --title "Creative Health" --audience girish
```

**If all OK:**
```bash
python3 /root/stocks/notify.py send "Creative Health — {DATE}
All {N} active ad URLs returning 200. UTM parameters present. All good." --title "Creative Health" --audience girish
```

### CLEANUP
No browser used. No locks. URL checks via curl only.
