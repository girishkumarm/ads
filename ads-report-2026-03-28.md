# Ads Report — 2026-03-28

## Google Ads
API still down (Test Account access, Basic Access pending).

## Facebook Ads — Morning Audit (7 Agents)

### By Campaign (Yesterday — last_1d):
| Campaign | Spend | Impr | Clicks | CTR | CPC | LPV | Freq |
|----------|-------|------|--------|-----|-----|-----|------|
| JNR Video | Rs 3,084 | 205,042 | 15,385 | 7.50% | Rs 0.20 | 13,098 | 1.12 |
| JNR Hyper | Rs 359 | 18,657 | 451 | 2.42% | Rs 0.79 | 214 | 1.33 |
| BTM Video | Rs 1,839 | 51,839 | 2,106 | 4.06% | Rs 0.87 | 1,643 | 1.30 |
| BTM Hyper | Rs 450 | 19,741 | 729 | 3.69% | Rs 0.62 | 619 | 1.14 |
| Resort | Rs 3,036 | 186,325 | 4,591 | 2.46% | Rs 0.66 | 1,900 | 1.22 |
| BTM Best of Blr | Rs 1,842 | 134,856 | 1,449 | 0.77% | Rs 1.27 | 620 | 1.66 |
| JNR Best of Blr | Rs 1,835 | 135,206 | 2,208 | 1.36% | Rs 0.83 | 1,006 | 1.39 |

### Fatigue Status:
All campaigns below fatigue threshold (< 2.5 frequency). BTM Best of Blr at 1.66 is highest — watch.

### Demographics Flags:
- JNR Hyper Local: 57% spend on 45+ audience — SEVERE targeting drift (target is 18-40)
- BTM Hyper Local: 18-24 = 55% spend, below-avg CTR
- Resort: 18-24 = 29% spend at 0.56% CTR (below avg) + 69% male skew

### Budget:
| Metric | Value |
|--------|-------|
| FB Yesterday Spend | Rs 2,032 |
| FB MTD | Rs 42,429 |
| FB Projected Month | Rs 46,974 |
| FB Token Expiry | 58 days (May 25) |
| Google Balance | UNAVAILABLE (API down) |

### Change Verification:
- JNR Video budget: Rs 650/day ✓ (applied)
- JNR Hyper budget: Rs 200/day ✓ (exact match)
- All Mar 26 paused ads still paused ✓
- No drift detected, no stale suggestions

MORNING_AUDIT_COMPLETE: 12:45 IST

## Facebook Ads — Today (2026-03-28)

### By Campaign:
| Campaign | Spend | Impr | Clicks | CTR | CPC | LPV | Vid Views |
|----------|-------|------|--------|-----|-----|-----|-----------|
| JNR Video | Rs 688 | 50,977 | 4,123 | 8.09% | Rs 0.17 | 3,286 | 18,526 |
| JNR Hyper | Rs 119 | 5,443 | 169 | 3.10% | Rs 0.70 | 90 | 903 |
| BTM Video | Rs 255 | 11,358 | 638 | 5.62% | Rs 0.40 | 504 | 3,432 |
| BTM Hyper | Rs 83 | 3,986 | 168 | 4.21% | Rs 0.50 | 129 | 946 |
| Resort | Rs 362 | 11,536 | 402 | 3.48% | Rs 0.90 | 249 | — |
| Basavanagudi Sale | Rs 134 | 9,535 | 117 | 1.23% | Rs 1.15 | 30 | — |

### Totals:
| Metric | Today | Yesterday | MTD |
|--------|-------|-----------|-----|
| Spend | Rs 1,640 | Rs 1,996 | Rs 43,230 |
| Impressions | 92,835 | 104,073 | 2,405,939 |
| Clicks | 5,617 | 5,105 | 70,844 |
| CTR | 6.05% | 4.91% | 2.94% |
| LPV | 4,288 | 4,008 | ~40,600 |

## Today's Actions
- Morning audit (7 agents): 5 OK, 2 warnings, no auto-actions
- A/B test: JNR Video dominates Hyper (+210% CTR). Budget shifted: Video 650→750, Hyper 200→100
- Basavanagudi Cafe Sale campaign CREATED: 3 ads, Rs 300/day, CALL_NOW CTA
- Resort optimization changed: LPV → OFFSITE_CONVERSIONS (Contact/calls) — user approved
- BTM ads temporarily switched to Google Business link, then REVERTED per user request
- BTM IPL Live Screening ad created
- 10-agent deep analysis of cafe sales patterns completed
- Cron log file created, pushed to GitHub
- GA4 API: new refresh token installed, needs API enablement in GCP

## Key Findings
- JNR Video: 8.09% CTR — highest ever recorded (new record!)
- BTM Video: 5.62% CTR — best since geo-fix optimization
- BTM Hyper: 4.21% CTR at Rs 0.50/click — solid
- Basavanagudi Sale: Rs 134 spent, 9,535 impressions, 30 LPV, 117 clicks
- Both cafes hit ~Rs 9-9.5K revenue ceiling on Saturday (capacity constraint identified)
- JNR: strong morning/afternoon, weak evening (family/brunch crowd)
- BTM: weak morning, strong evening (IT/PG crowd)
- Revenue ceiling likely operational, not ad-driven

## Trends
- JNR CTR: IMPROVING (8.09% today vs 7.50% 7d avg — new record)
- BTM CTR: IMPROVING (5.62% today vs 4.06% yesterday — geo fix working)
- BTM Hyper: stable (4.21% CTR, Rs 0.50 CPC)
- Resort: stable (3.48% CTR, now optimizing for calls)
- All frequencies healthy (< 2.0)
- FB Token: 57.6 days remaining

## Budget
| Metric | Value |
|--------|-------|
| FB Today Spend | Rs 1,640 |
| FB MTD | Rs 43,230 |
| FB Projected Month | Rs 44,870 (3 days left) |
| FB Token Expiry | 57.6 days (May 25) |
| Google Balance | UNAVAILABLE (API down) |

EVENING_REPORT_COMPLETE: 23:48 IST
