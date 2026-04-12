# Pending Ads Suggestions

<!-- Suggestions are added by morning-audit agents. Format:
## SGG-{DATE}-{SEQ} [PENDING|APPROVED|REJECTED|IMPLEMENTED]
Platform: Google Ads
Type: [Add negative keyword | Add keyword | Fix targeting | etc.]
Detail: [Specific finding with data]
Suggested action: [What to do]
Impact: [Estimated spend saved / conversions gained]
Created: {DATE} {TIME}
Approved: {DATE} {TIME} (if approved)
Implemented: {DATE} {TIME} (if implemented)
-->

## SGG-2026-04-02-01 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Add negative keywords — irrelevant geography
Detail: Search terms "ramanagara resort", "resorts near ramanagara", "resorts in ramanagara", "resort near ramanagara", "resorts near bidadi" spent Rs 341 with 0 conversions in 7 days.
Suggested action: Add negative keywords: "ramanagara", "bidadi"
Impact: Save ~Rs 341/week (Rs 1,364/month)
Created: 2026-04-02 12:00

## SGG-2026-04-02-02 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Add negative keyword — irrelevant activity
Detail: "camping near bangalore" — 9 clicks, Rs 117, 0 conversions. Namooru is a resort, not a campsite.
Suggested action: Add negative keyword: "camping"
Impact: Save ~Rs 117/week (Rs 468/month)
Created: 2026-04-02 12:00

## SGG-2026-04-02-03 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Fix low quality score keyword
Detail: "places to stay in kanakapura" has Quality Score = 1 (worst possible). 15 clicks, Rs 189, 0 conversions. Dragging down ad rank and increasing CPC.
Suggested action: Pause this keyword — QS=1 means Google considers the ad/landing page irrelevant for this term
Impact: Improve overall campaign QS, reduce CPC across board
Created: 2026-04-02 12:00

## SGG-2026-04-02-04 [MONITORING]
Platform: Google Ads (Resort)
Type: Fix low quality score keyword
Detail: "weekend getaway bangalore" has Quality Score = 3 (poor). 40 clicks, Rs 516, only 3 conversions. Rs 172/conv is high vs campaign avg.
Suggested action: Either pause or improve landing page relevance for this term
Impact: Better budget allocation to higher-converting terms
Created: 2026-04-02 12:00

## SGG-2026-04-02-05 [PENDING — manual review needed]
Platform: Google Ads (Resort)
Type: Review zero-traffic ads
Detail: 8 of 10 enabled ads have 0 clicks in 7 days. Only 1 ad is receiving all traffic. The inactive ads may have issues or Google may be strongly preferring one ad.
Suggested action: Review ad copy/headlines on the 8 zero-click ads. Consider pausing obviously poor ones and creating fresh alternatives.
Impact: Better ad rotation, potential CTR improvement
Created: 2026-04-02 12:00

## SGG-2026-04-02-06 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Add negative keywords — price-seeking terms
Detail: "resorts in kanakapura road with price" — 7 clicks, Rs 94, 0 conversions. Price-seekers often don't convert.
Suggested action: Add negative keyword: "with price", "price list", "rates"
Impact: Save ~Rs 94/week on low-intent traffic
Created: 2026-04-02 12:00

## SGG-2026-04-03-01 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Consolidate duplicate broad keywords
Detail: "resorts near bangalore" appears in BROAD match across multiple ad groups. Two variants have Rs 33,447+ lifetime spend with ZERO conversions, while one variant has 146 conversions.
Suggested action: Pause zero-conversion duplicates, keep only the converting variant
Impact: Save Rs 33,447+ in wasted spend, focus budget on converting variant
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Already done; "Targeted Groups" ad group and duplicates no longer exist

## SGG-2026-04-03-02 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Pause/restructure high-CPC ad group
Detail: "Targeted Groups" ad group has CPCs of Rs 25-76 (vs Rs 13 account avg), with zero conversions. Keywords: "resorts near bangalore" Rs 37 CPC, "places to stay near bangalore" Rs 76 CPC (Rs 2,732 wasted), "best resorts around bangalore" Rs 29 CPC (Rs 1,354 wasted).
Suggested action: Pause "Targeted Groups" ad group entirely
Impact: Stop Rs 4,000+ waste, redirect budget to better-performing ad groups
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Already done; ad group does not exist in account

## SGG-2026-04-03-03 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Pause zero-conversion broad keywords
Detail: Ultra-generic broad keywords burning budget with 0 conversions: "luxury resorts" (Rs 343), "best resorts" (Rs 909), "nature resorts" (Rs 1,000), "bangalore resorts" (Rs 350), "adventure resorts in bangalore" (Rs 1,136). Total: Rs 3,738+ wasted.
Suggested action: Pause these generic broad match keywords
Impact: Save Rs 3,738+ and redirect to high-converting Kanakapura-specific terms
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Already done; these keywords no longer exist in the account

## SGG-2026-04-03-04 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Add negative keywords
Detail: Search terms with clicks but 0 conversions in 7 days: "resorts near ramanagara" (Rs 53), "resorts in mysore road", "kanakapura resort list" (informational), "outing resorts in bangalore" (day outing intent), "holiday village resort bangalore" (competitor).
Suggested action: Add exact negatives: "ramanagara", "mysore road", "resort list", "outing", "holiday village"
Impact: Save Rs 200-500/week on irrelevant clicks
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Added 14 negatives (mysore road, outing + 12 from morning audit). "resort list", "holiday village", "the gari resorts" already existed.

## SGG-2026-04-03-05 [SKIPPED]
Platform: Google Ads (Resort)
Type: Consider Target CPA bidding
Detail: Campaign has 110+ conversions in 7 days (15/day avg). Cost/conversion ranges Rs 210-447. Enough data for Smart Bidding to optimize.
Suggested action: Switch to Target CPA bidding with target of Rs 250
Impact: Potentially reduce cost per conversion and increase conversion volume
Created: 2026-04-03 22:00
Skipped: 2026-04-04 — Bidding strategy change too risky during optimization phase. Will revisit later.

## SGG-2026-04-03-06 [IMPLEMENTED]
Platform: Google Ads (Cafe BTM)
Type: Set up conversion tracking
Detail: ZERO conversions tracked despite Rs 5,694 spend in 7 days and 307 clicks. Flying blind on ROI — cannot optimize without conversion data.
Suggested action: Add conversion actions: phone calls, direction clicks, website form submissions
Impact: Enable data-driven optimization, measure actual ROI
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Previously completed

## SGG-2026-04-03-07 [IMPLEMENTED]
Platform: Google Ads (Cafe BTM)
Type: Add negative keywords
Detail: Irrelevant search terms: "fast food near me" (Rs 54), "cafe coffee day near me" (Rs 27, competitor), "non veg hotel near me" (Rs 25), "birthday surprise for wife" (Rs 24, gift intent).
Suggested action: Add negatives: "fast food", "cafe coffee day", "CCD", "non veg hotel", "surprise for wife", "surprise for husband", "delivery"
Impact: Save Rs 100-150/week on irrelevant clicks
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Previously completed (44 negatives added)

## SGG-2026-04-03-08 [IMPLEMENTED]
Platform: Google Ads (Cafe BTM)
Type: Fix low quality score keyword
Detail: "cafe in btm layout" has QS=1 (worst possible), inflating CPC. "restaurants near me" QS=3, "places to eat near me" QS=3, "best cafe near me" QS=2.
Suggested action: Create dedicated ad groups with tailored ad copy for low-QS keywords, or pause QS=1 keyword
Impact: Lower CPCs across campaign, improve ad rank
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Previously completed (QS 1-2 keywords paused)

## SGG-2026-04-03-09 [IMPLEMENTED]
Platform: Facebook (Resort)
Type: Resume paused adset for redundancy
Detail: Resort campaign has only 1 active ad. "Fresh Adset v2" is paused. If the single active ad gets disapproved or fatigued, entire campaign goes dark.
Suggested action: Resume "Fresh Adset v2" or create new ad under active adset
Impact: Prevent campaign blackout risk, improve ad rotation
Created: 2026-04-03 22:00
Approved: 2026-04-04 (ads approve all)
Implemented: 2026-04-04 — Resumed adset 6968174064344 via Facebook API

## SGG-2026-04-05-01 [WITHDRAWN]
Platform: Google Ads (Resort)
Type: Add negative keywords — budget/cheap seekers
Detail: 411 negative keywords already in place including budget, free, discount, under 2000/3000, sasta. Most cheap/budget terms already blocked.
Withdrawn: 2026-04-05 — Girish confirmed negatives already exist. Account already well-covered.

## SGG-2026-04-05-02 [IMPLEMENTED]
Platform: Google Ads (Resort)
Type: Re-enable paused keywords + remove ad schedule
Detail: Apr 4 optimization was too aggressive — 52 keywords paused, ad schedule restricted to 8AM-10PM. Result: 66% impression share lost to rank, spend dropped from Rs 5K to Rs 1.6K. High-traffic keywords with good CTR were incorrectly paused.
Suggested action:
  A) Re-enable 8 keywords: stay in kanakapura resort, resorts near kanakapura bangalore (QS=5), night stay in kanakapura, weekend getaway bangalore, couples resort near bangalore, staycation resorts near bangalore, resorts near bangalore for weekend (QS=6), resort stay in bangalore (QS=6)
  B) Remove ad schedule restriction (back to 24/7)
Impact: Restore spend to Rs 4-5K/day, recover ~66% lost impression share
Created: 2026-04-05 19:30
Approved: 2026-04-05 19:45 (Girish via Telegram)
Implemented: 2026-04-05 19:45 — Re-enabled 8 keywords + removed 7 ad schedule restrictions (back to 24/7)


## SGG-2026-04-06-01 [PENDING]
Platform: Google Ads (Resort)
Type: Add negative keywords — generic Bangalore queries
Detail: "resorts near bangalore" (Rs 817, 0 conv), "resort near bangalore" (Rs 584, 0 conv), "resort bangalore" (Rs 243, 0 conv), "resorts near bangalore for family" (Rs 228, 0 conv), "resort near bangalore for family" (Rs 150, 0 conv). Total Rs 2,022 wasted in 7 days.
Suggested action: Add as phrase match negatives: "resorts near bangalore", "resort near bangalore", "resort bangalore", "resorts near bangalore for family", "resort near bangalore for family"
Impact: Save ~Rs 2,000/week on non-converting generic queries
Created: 2026-04-06 07:00

## SGG-2026-04-06-02 [PENDING]
Platform: Google Ads (Resort)
Type: Add exact match keyword — branded misspelling
Detail: "nammuru eco stay" has 2 conversions at Rs 19/conv (extremely efficient). Currently not an exact match keyword. Also "nammura eco stay" and "nammoora eco stay" have high CTR (43-64%) but 0 conv — possible landing page issue.
Suggested action: Add [nammuru eco stay] as exact match keyword. Investigate why branded misspellings show 0 conversions despite high CTR.
Impact: Capture branded traffic at very low CPC
Created: 2026-04-06 07:00

## SGG-2026-04-06-03 [PENDING]
Platform: Google Ads (Resort + Cafe)
Type: Add tracking templates — UTM parameters missing
Detail: Creative health check 2026-04-06 found all 4 active Google Ads (2 Resort + 2 Cafe BTM Search) have no tracking URL template. UTM attribution is missing in GA4 for all Google Ads traffic.
Suggested action: Add tracking template to both accounts:
  Resort campaign "Ecostay - Kanakapura" (IDs: 714615920326, 803687131360):
    {lpurl}?utm_source=google&utm_medium=cpc&utm_campaign=ecostay-kanakapura&utm_term={keyword}
  Cafe campaign "BTM Search" (IDs: 756088212365, 764996596294):
    {lpurl}?utm_source=google&utm_medium=cpc&utm_campaign=btm-search&utm_term={keyword}
Impact: Restore Google Ads attribution in GA4 — currently all Google Ads traffic shows as "direct"
Created: 2026-04-06 08:30

## SGG-2026-04-06-04 [PENDING]
Platform: Google Ads (Resort)
Type: Add competitor negative keywords
Detail: Today 17+ competitor names triggered clicks with 0 conversions: vara farms (Rs 39), panchavati resort, lasya resort, gari resorts, hideck resort, rds nature, portico resort, wood resort, jaladhama resort, kargil resort, kadugalu resort, banjara resort, sterling resort, saffronstays, mayank resort. Estimated Rs 400-600/day wasted.
Suggested action: Add as exact/phrase negatives: vara farms, panchavati, lasya, hideck, portico, wood resort, kadugalu, kargil, banjara, sterling, saffronstays, mayank
Impact: Save Rs 400-600/day on competitor clicks
Created: 2026-04-06 22:00

## SGG-2026-04-06-05 [PENDING]
Platform: Google Ads (Resort)
Type: Desktop bid adjustment -50%
Detail: Desktop had 26 clicks, Rs 476 spend, 0 conversions today. Mobile has 6% conversion rate. Desktop consistently underperforms.
Suggested action: Set desktop bid adjustment to -50% on campaign 21740834372
Impact: Save ~Rs 250-300/day, redirect to mobile
Created: 2026-04-06 22:00

## SGG-2026-04-06-06 [PENDING]
Platform: Google Ads (Resort)
Type: Reduce 8-9 AM bids
Detail: Hours 8-9 AM IST had Rs 523 spend with 0 conversions (34 clicks). Peak conversion hours are 10 AM-2 PM.
Suggested action: Add -40% bid adjustment for 8-9 AM IST
Impact: Save ~Rs 200-300/day on low-converting morning hours
Created: 2026-04-06 22:00

## SGG-2026-04-10-02 [APPROVED]
Platform: Google Ads (Cafe BTM)
Type: Set up conversion tracking
Detail: Zero conversions tracked on BTM Search campaign despite Rs 8,500 spend in 7 days (410 clicks). Cannot optimize without conversion data.
Suggested action: Add conversion actions in Google Ads:
  1. Phone calls from ads → 9901978999 (SK Singh)
  2. Direction clicks to BTM cafe
  3. Store visits (auto-tracked if eligible)
Impact: Enable ROI measurement and Smart Bidding optimization
Created: 2026-04-10 23:30
Approved: 2026-04-10 23:30 (Girish via voice)

## SGG-2026-04-10-03 [APPROVED]
Platform: Google Ads (Cafe BTM)
Type: Pause generic/low-QS keywords
Detail: Generic keywords burning budget with 0 conversions: "restaurants near me" (QS 3, Rs 1,903), "places to eat near me" (QS 3, Rs 216), "breakfast near me" (QS 3, Rs 140), "work from cafe bangalore" (QS 3, Rs 19). Total Rs 2,278 wasted in 7 days.
Suggested action: Pause these 4 keywords
Impact: Save Rs 2,278/week, redirect budget to cafe/birthday keywords
Created: 2026-04-10 23:30
Approved: 2026-04-10 23:30 (Girish via voice)

## SGG-2026-04-10-04 [APPROVED]
Platform: Google Ads (Cafe BTM)
Type: Add negative keywords — generic food terms + wrong locations
Detail: Generic food terms and wrong-location searches burning budget: "food near me", "eating places near me", "dinner near me", "lunch near me", "restaurants nearby my location", "peenya" (wrong location), "party hall/halls" (not a hall).
Suggested action: Add as negatives: food, eating places, dinner, lunch, peenya, party hall, party halls
Impact: Block Rs 500+/week in irrelevant clicks
Created: 2026-04-10 23:30
Approved: 2026-04-10 23:30 (Girish via voice)

## SGG-2026-04-10-01 [APPROVED]
Platform: Google Ads (Resort)
Type: Add negative keywords — competitor/off-location search terms
Detail: Today's search terms audit found spend on irrelevant queries with 0 conversions:
  - "gold coins club & resort prices" — Rs 78 (competitor)
  - "secret valley resort about" — Rs 77 (competitor)
  - "ramnagar resort near bangalore" — Rs 58 (off-location)
  - "resort in sarjapur" — Rs 34 (off-location)
  - "cylinder resort" — Rs 20 (irrelevant)
  - "kab kabana resort" — Rs 20 (competitor)
  - "tattva stays hennur" — Rs 19 (competitor)
  - "resorts in hesaraghatta" — Rs 22 (off-location)
Suggested action: Add exact match negatives: "gold coins", "secret valley", "cylinder resort", "kab kabana", "tattva stays", "hesaraghatta", "sarjapur", "ramnagar"
Impact: Save ~Rs 300+/day on irrelevant clicks
Created: 2026-04-10 16:45
Approved: 2026-04-10 17:15 (Girish via Telegram)
Note: Needs manual implementation in Google Ads UI (API is read-only)
