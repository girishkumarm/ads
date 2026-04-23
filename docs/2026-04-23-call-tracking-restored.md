# 2026-04-23 — Call Tracking Restored via GTM

## Problem (reported by user 2026-04-23)
- 30+ phone calls received today on namooru.com
- Google Ads conversions: **0**
- GA4 phone_call events: **0**
- Phone number on site was changed, and the custom header tracking code in GoDaddy was wiped

## Root cause
GoDaddy Website Builder (current plan) does NOT expose a "site-wide custom header code" field. When the site was edited (phone number change), the tel-click tracking code was lost. Only `Meta Pixel` base code, `Google Analytics` base code, and GTM container were preserved because each has a dedicated field in GoDaddy Settings → Analytics & Tracking.

## Fix — via GTM (GTM-WP7DBHQX)
Instead of re-adding custom code in GoDaddy (not possible in this plan), we added 2 new tags inside the existing GTM container. **This is the correct long-term approach** because:
- Changes in GTM propagate instantly (no GoDaddy republish needed)
- Survives all future GoDaddy edits
- Centralizes all tracking logic

### Existing (unchanged)
| Tag | Trigger | Purpose |
|-----|---------|---------|
| Conversion Linker | All Pages | Required for Google Ads attribution |
| Google Ads - Click to Call Conversion | Click to Call - Phone Links | Fires Google Ads conversion on tel-click |
| Google Tag - AW-11379717907 | Initialization - All Pages | Google Ads tag |
| JSON-LD Schema - Namooru Ecostay | All Pages | SEO structured data |

### Added 2026-04-23 (Version 4, published)
| Tag | Type | Trigger | Details |
|-----|------|---------|---------|
| **GA4 - Phone Call Click** | GA4 Event | Click to Call - Phone Links | Measurement ID `G-H03REW00KK`, Event `phone_call`, param `link_url={{Click URL}}` |
| **Meta Pixel - Phone Call Contact** | Custom HTML | Click to Call - Phone Links | Fires `fbq('track','Contact',{content_name:'Phone Call Click',content_category:'tel_link_click'})` |

### Existing trigger reused
`Click to Call - Phone Links` — Event Type: Just Links, Filter: Click URL **starts with** `tel:`

## Immediate impact
Every phone click on namooru.com now fires 3 things in parallel:
1. Google Ads conversion (existing tag)
2. GA4 `phone_call` event (new) — visible in GA4 DebugView / Realtime
3. Meta Pixel `Contact` event (new) — visible in Meta Events Manager → Test Events

## Still TODO (not yet done by me — needs verification)

### 1. Verify tracking is firing
- Open namooru.com in a browser with these extensions:
  - **Meta Pixel Helper** — should show `PageView` on load, `Contact` on phone click
  - **Google Tag Assistant** — should show GA4 + GTM firing, `phone_call` event on phone click
- Or check server-side:
  - GA4 → Realtime → click phone on site → should see `phone_call` event within 30s
  - Meta Events Manager → Test Events → enter namooru.com → click phone → should see `Contact` event

### 2. Mark `phone_call` as a key event in GA4
- GA4 Admin → Events → wait 24h for `phone_call` to appear after first fire
- Toggle "Mark as key event"

### 3. Import `phone_call` as Google Ads conversion (optional, for Smart Bidding)
- Google Ads → Goals → Conversions → + New → Import → Google Analytics 4 properties → select `phone_call`
- Set counting to "One" per session
- Attribution: Data-driven

### 4. Verify existing Google Ads "Website Call" conversion action is healthy
- Google Ads → Goals → Conversions → Summary
- Find any "Calls from website" / "Phone call" conversion action
- If it's keyed to a SPECIFIC phone number (legacy conversion type), verify it matches the current site number (+918618547729)
- If it has "no recent conversions" status since the phone number change, the old number mismatch is the cause — update or re-create

## Bot actions when running audits
- When reporting call metrics, pull from both:
  - `ads_api.py fb metrics <CAMPAIGN>` — FB Contact events per campaign
  - `ads_api.py ga4 calls 7` — calls by source/medium from GA4
  - `ads_api.py google campaigns` — Google Ads conversions
- Cross-reference to detect attribution drops

## Diagnosis helpers
- Fetch site source and check for `phone_call` string → if missing, GTM not firing (container problem, not site code)
- Fetch site source and check for `GTM-WP7DBHQX` → if missing, GTM itself was removed from GoDaddy
