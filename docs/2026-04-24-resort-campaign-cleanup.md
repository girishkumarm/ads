# 2026-04-24 — Ecostay Resort Campaign Cleanup

## Campaign
- **Account:** Resort (customer_id 2995160429)
- **Campaign:** Ecostay - Kanakapura (id `21740834372`)
- **Ad group:** Ad group 1 (id `167245531185`)
- **Budget:** Rs 4,000/day (recently reduced from Rs 5,000)

## 30-day baseline (before cleanup)
- 47,479 impressions, 6,179 clicks, 13.01% CTR
- Rs 1,03,189 spend, 420 primary conversions, Rs 246 per conversion
- Top driver: `staycation near bangalore` (101 conversions, Rs 298 each)
- Healthiest: `pet friendly resort near bangalore` QS 8 (Rs 121 per conversion)

## Discovery
Initial analysis thought 17 BROAD keywords (wedding, jobs, kerala, goa, etc.)
were sitting as positive traps. Turned out on pause attempt they were ALREADY
ad-group-level NEGATIVES — the API error `CANT_UPDATE_NEGATIVE: Negative ad
group criteria are not updateable` confirmed it. No action needed — they were
blocking traffic correctly all along.

## Actions taken (via Google Ads API v20)

### 1. Paused 3 low-QS keywords that were wasting budget
| Match | Keyword | QS | Why paused |
|-------|---------|---:|------------|
| PHRASE | `best resort stay in bangalore` | 3 | High volume (288 clicks, 28 conv) but QS=3 → overpaying 2-3× for same traffic. Needs its own ad group + ad copy. |
| PHRASE | `weekend getaway bangalore` | 3 | 113 clicks, only 5.5 conv — landing page mismatch. Needs dedicated creative. |
| PHRASE | `glamping near bangalore` | 4 | 9 clicks, 0 conv in 30 days. Not worth keeping. |

### 2. Added 15 BROAD negatives at campaign level (belt-and-suspenders)
The 17 "trap" words already existed as ad-group-level negatives, but `jobs` and
`career` were also already campaign-level. Added 15 more at campaign level for
redundancy across future ad groups:

`wedding, review, images, photos, low price, rating, honeymoon, under,
internship, goa, ooty, kerala, coorg, function hall, namooru ecostay`

Total campaign-level negatives: 427 → **442**

### 3. Rebuilt the active RSA with "Namooru Ecostay" pinned to HEADLINE_1
- Old RSA: 15 unpinned headlines — Google rotated brand name randomly
- New RSA: same 15 headlines, but "Namooru Ecostay" pinned as HEADLINE_1
- Old RSA paused (history preserved for reporting)

## Final state
```
Ecostay - Kanakapura (Rs 4,000/day)
└── Ad group 1 (ENABLED)
    ├── Keywords: 56 enabled, 35 paused
    ├── Ads: 1 enabled (new, with pin), 1 paused (old, history kept)
    └── Campaign-level negatives: 442
```

## What this should do
- **Save ~Rs 4,300/month** from the 3 low-QS pauses (won't be rebuilt until
  dedicated ad groups + ad copy are created — see "still TODO")
- **Brand consistency** on searches — every impression now starts with
  "Namooru Ecostay" instead of a random one of 15 headlines
- **Belt-and-suspenders** on the 15 duplicate negatives — even if ad-group
  negatives ever get wiped, campaign-level blocks will hold

## Still TODO

### Rebuild the 3 paused keywords with dedicated ad groups + copy
The "best resort" and "weekend getaway" themes converted but at a premium.
With dedicated ad groups + ad copy matching the intent (headlines like
"Bangalore's Best Resort" or "Your Perfect Weekend Getaway"), QS would jump
from 3 to 6-7 and cut CPC 40%.

Run this when ready:
```bash
# Create new ad group "Best Resort Bangalore"
python3 ads_api.py google ad-group create 21740834372 "Best Resort Bangalore" 20
# Add keywords matching the intent
# Create RSA with "Best Resort" in multiple headlines
```

### Build a `/weekend-getaway-bangalore` landing page
All 3 paused keywords would benefit from a landing page that matches the
search intent. Currently all ads point to `https://namooru.com` which is a
generic resort page.

### Monitor for 7 days
Check daily:
```bash
python3 ads_api.py google metrics 21740834372 7
```

Expected outcome:
- Same or higher conversions (primary drivers weren't touched)
- Lower wasted spend
- Brand headline always visible on impression 1
