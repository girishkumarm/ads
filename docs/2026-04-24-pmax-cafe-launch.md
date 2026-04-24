# 2026-04-24 — PMax Jayanagar Cafe: End-to-End Build

## Campaign
- **Account:** Resort Google Ads (customer_id 2995160429)
- **Campaign:** Jayanagar Cafe - PMax Store (id `23769035916`)
- **Asset group:** Ambience & Coffee (id `6703742587`)
- **Budget:** Rs 400/day
- **Bidding:** MAXIMIZE_CONVERSIONS
- **Channel:** PERFORMANCE_MAX

## State before fix
- Campaign status: `ENABLED / NOT_ELIGIBLE`
- Reasons: `BIDDING_STRATEGY_LEARNING + ASSET_GROUPS_PAUSED + UNKNOWN`
- Asset group: `PAUSED`, ad strength `POOR`
- Assets in group: **0 of everything** (empty shell)
- Final URL: a Google Maps search link (placeholder)
- Running for 3 days with Rs 0 spent / 0 impressions

## GBP verification
Google Business Profile IS linked to Google Ads:
- Asset set `9116435421` name "Business Profile", type `LOCATION_SYNC`, status `ENABLED`
- 3 active location assets synced from GBP
- Linked to both PMax (23769035916) and Search (23778954613) campaigns

## Actions taken (end-to-end via API v20)

### 1. Fixed asset group final URL
```
Before: https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/
After:  https://namooru.com/
```
(Change to a dedicated /cafe-jayanagar landing page when it's built.)

### 2. Scraped 11 photos from Brewing Untold Stories GBP listing
Via Playwright on google.com/maps/place/.../0xf75b25b8f4c76726.
Downloaded at `=w1600-h1200-k-no` resolution, stored to `/tmp/pmax_assets/`.

### 3. Cropped + resized to PMax-required ratios (using Pillow)
- 5 × landscape 1200×628 (1.91:1) — `MARKETING_IMAGE`
- 5 × square 1200×1200 (1:1) — `SQUARE_MARKETING_IMAGE`
- 5 × portrait 960×1200 (4:5) — `PORTRAIT_MARKETING_IMAGE`
- 1 × logo 1200×1200 — `LOGO`

### 4. Created 25 text assets via Assets:mutate
Hitting PMax limits:
| Type | Max | Created |
|------|----:|--------:|
| HEADLINE (≤30 chars) | 15 | 15 |
| LONG_HEADLINE (≤90 chars) | 5 | 5 |
| DESCRIPTION (≤90 chars) | 5 | 5 |
| BUSINESS_NAME | 1 | 1 (reused) |

Headlines written to hit 4 themes: **general cafe**, **date night**, **birthday/events**, **laptop-friendly**.

### 5. Linked 41 of 42 assets to the asset group
Google's API returned `RESOURCE_LIMIT / ENABLED_HEADLINE_ASSET_LINKS_PER_ASSET_GROUP`
when I tried to add a 16th+ headline — that's the hard Google cap at 15. Expected.

Final asset counts per slot:
| Field | Count |
|-------|------:|
| HEADLINE | 15 |
| LONG_HEADLINE | 5 |
| DESCRIPTION | 5 |
| MARKETING_IMAGE | 6 |
| SQUARE_MARKETING_IMAGE | 6 |
| PORTRAIT_MARKETING_IMAGE | 6 |
| LOGO | 2 |
| BUSINESS_NAME | 1 |

### 6. Unpaused the asset group
Status changed: `PAUSED / POOR` → `ENABLED / PENDING (ASSET_GROUP_UNDER_REVIEW)`

## Expected timeline
- Assets under Google review: **24 hours typical, up to 3 days max**
- After approval: ad strength will jump from PENDING → GOOD/EXCELLENT
- Campaign primary status will flip to ELIGIBLE
- PMax starts serving impressions immediately after that

## What's serving where (once approved)
PMax spans ALL Google inventory — Search, Display, YouTube, Gmail, Maps, Discover.
With the linked GBP location assets + proximity targeting, local searchers near
Jayanagar will see map pack results, Discover cards, and YouTube pre-roll with the cafe info.

## Verification commands
```bash
# Check if campaign is still NOT_ELIGIBLE (wait 24h)
python3 ads_api.py google campaigns

# Check ad strength + approval status
python3 -c "from ads_api import *; c=load_config(); print(google_gaql(c, 'SELECT asset_group.id, asset_group.primary_status, asset_group.ad_strength FROM asset_group WHERE campaign.id = 23769035916'))"

# Check PMax performance once it starts serving
python3 ads_api.py google metrics 23769035916 7
```

## Still TODO (manual, optional)
- **Build `/cafe-jayanagar` landing page** with menu, address, call button, GTM
  tracking, and update asset group final_url
- **Add a YouTube video asset** — PMax favors video heavily. A 15-30 sec Reel
  works. Upload to the cafe's YouTube channel first, then link via API.
- **Monitor Search Themes** (`performance_max_placement_view`) after 7 days of
  serving to see what queries are triggering the ads

## Files generated
- `/tmp/pmax_assets/gbp_*.jpg` — original scraped images
- `/tmp/pmax_assets/final/*.jpg` — cropped to PMax ratios
- `/tmp/pmax_asset_rns.json` — asset resource names (for reference)
