# A/B Tests — Active and Completed

## How to create a test
Add a new section below with format:
```
## TEST-{NNN} [PENDING|RUNNING|WINNER_A|WINNER_B|INCONCLUSIVE]
Campaign: {campaign name}
Variant A (Control): AD_ID — "ad description"
Variant B: AD_ID — "ad description"
Primary metric: {cost_per_call|ctr|cpc}
Start: {DATE}
Min duration: 7 days
Min impressions per variant: 1000
```

The `ads-ab-test-manager` agent will manage running tests automatically.

---

## TEST-001 [RUNNING]
Campaign: BUS Cafe Jayanagar - Work From Cafe (6971285053744)
Variant A (Control): 6971285626744 — "JNR WFC - ₹349 Unlimited Coffee" (static offer-led)
Variant B: 6971311546144 — "JNR WFC - NEW Video Reel" (video creative)
Primary metric: ctr
Start: 2026-04-06
Min duration: 7 days
Min impressions per variant: 1000
Notes: Static vs video reel format test. A has 24,784 impr/3.21% CTR vs B with 5,030 impr/2.13% CTR after unequal budget split. Need balanced delivery for 7 days.

## TEST-002 [RUNNING]
Campaign: BUS Cafe Jayanagar - Dining Booking (6971285051144)
Variant A (Control): 6971310788744 — "JNR Dining - Reel 2" (established reel, higher volume)
Variant B: 6971310113944 — "JNR Dining - NEW Video Reel" (newer video, lower volume)
Primary metric: cpc
Start: 2026-04-06
Min duration: 7 days
Min impressions per variant: 5000
Notes: Two video reels competing. A: 26,729 impr, CTR 2.11%, CPC Rs 0.78. B: 10,743 impr, CTR 1.68%, CPC Rs 1.13. Budget appears skewed toward A. Monitor if B catches up.

## TEST-003 [RUNNING]
Campaign: BUS Cafe BTM - Dining Booking (6971314053344)
Variant A (Control): 6971376570144 — "BTM Dining - New Reel 3"
Variant B: 6971376588944 — "BTM Dining - New Reel 4"
Primary metric: ctr
Start: 2026-04-06
Min duration: 7 days
Min impressions per variant: 5000
Notes: Two new reels launched at similar time with similar budget split. A: 9,486 impr/2.75% CTR/Rs 0.98 CPC. B: 9,194 impr/2.48% CTR/Rs 0.93 CPC. Near-even delivery — clean comparison. Reel 3 leads on CTR, Reel 4 slightly cheaper. Evaluate Friday.

---

## Completed Tests

*None yet.*
