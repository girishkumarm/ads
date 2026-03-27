# Ads Report — 2026-03-26

## Google Ads — Namooru Ecostay Resort

Google Ads API returning 404 — unable to pull metrics. API needs to be enabled on GCP project.

## Facebook Ads

### By Campaign (Today — 2026-03-26):

| Campaign | Spend | Impr | Clicks | CTR | CPC | Freq | LPV | Vid Views |
|----------|-------|------|--------|-----|-----|------|-----|-----------|
| JNR Video Ads | Rs 339 | 30,950 | 2,106 | 6.80% | Rs 0.16 | 1.15 | 1,556 | 9,064 |
| JNR Hyper Local | Rs 61 | 2,908 | 58 | 1.99% | Rs 1.05 | 1.64 | 22 | 463 |
| BTM Video Ads | Rs 396 | 13,832 | 457 | 3.30% | Rs 0.87 | 1.18 | 347 | 3,362 |
| BTM Hyper Local | Rs 62 | 2,359 | 75 | 3.18% | Rs 0.83 | 1.35 | 55 | 501 |
| Namooru Resort | Rs 419 | 20,990 | 480 | 2.29% | Rs 0.87 | 1.12 | 230 | — |

### 7-Day Averages:

| Campaign | Spend/day | CTR | CPC | LPV/day |
|----------|-----------|-----|-----|---------|
| JNR Video Ads | Rs 410 | 7.47% | Rs 0.24 | 1,440 |
| BTM Video Ads | Rs 144 | 3.84% | Rs 1.31 | 88 |
| Namooru Resort | Rs 492 | 2.65% | Rs 0.52 | 338 |

### Totals:

| Metric | Today | MTD |
|--------|-------|-----|
| Total Spend | Rs 1,416 | Rs 39,402 |
| Total Impressions | 83,679 | 2,197,190 |
| Total Clicks | 3,290 | 59,581 |
| Avg CTR | 3.93% | 2.71% |
| Landing Page Views | 2,210 | — |

## Combined Summary
- Total daily spend (today): Rs 1,416 (FB only — Google API down)
- FB monthly pace: Rs 39,402 spent / 26 days = Rs 1,515/day → Rs 45,461/month projected
- Google budget: Unknown (API down)

## Today's Optimization Actions
- Paused 11 underperforming ads (7 BTM + 4 JNR) — saved ~Rs 5,670/wk
- Tightened targeting: age 18-40, disabled Advantage+ on both locations
- Changed CTA from 'Learn More' to 'Order Now' on all 12 active ads
- Created 2 new Hyper Local campaigns (JNR + BTM, Rs 250/day each)
- Created 8 new angle-based ad creatives (4 per location)
- Created 6 offer-based ads (499 combo, 349 unlimited coffee, BOGO ice cream)
- Created 4 static image ads with real cafe photos
- Updated landing pages from Google Maps to Zomato menu pages
- Updated Resort optimization: LINK_CLICKS → LANDING_PAGE_VIEWS
- Added 2 new automation crons (creative freshness + A/B compare)

## Trends
- JNR Video Ads: Star performer. CTR 6.80% today vs 7.47% 7-day avg (slight dip, normal)
- JNR CPC: Rs 0.16 today vs Rs 0.24 avg — improving
- BTM CPC: Rs 0.87 today vs Rs 1.31 avg — improving significantly
- All frequencies healthy (< 2.0)
- New ads (Hyper Local, offer-based, static) still in learning phase — expect data in 2-3 days

## Notes
- Google Ads API broken (404 on all endpoints). Needs GCP project API enablement.
- FB app switched from Development to Live mode today — enabled new creative creation via API.
- Best of Bangalore campaigns (both locations) paused — ads disabled but campaigns still technically active.
- Meta Pixel not yet installed on namooru.com (user needs to do manually via GoDaddy).

EVENING_REPORT_COMPLETE: 23:48 IST
