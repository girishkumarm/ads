---
name: ads-ab-test-manager
description: Mon 8:30 AM IST (setup) + Fri 8:30 AM IST (evaluate) — Manage A/B test lifecycle. Auto-promote winners for Cafe, suggest for Resort.
---

## A/B TEST MANAGER — SETUP & EVALUATION

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.
DAY OF WEEK: Run `TZ='Asia/Kolkata' date +%u` (1=Monday, 5=Friday)

### AUTHORITY RULES

- **Cafe campaigns** (name contains BUS/Cafe/BTM/Jayanagar/Venue) → **FULL AUTO** — can pause losers, promote winners
- **Resort campaigns** (name contains Namooru/Resort/Ecostay) → **APPROVAL ONLY** — write suggestion to `ads-suggestions.md`
- **If unclear** → **APPROVAL ONLY**

### STEP 0: Gate Check

1. Set DATE and DAY_OF_WEEK variables.
2. Check day:
   - Monday (1) → Run SETUP mode
   - Friday (5) → Run EVALUATION mode
   - Otherwise → skip
3. Read `/root/ads/ads-ab-tests.md` — if file doesn't exist, notify Girish that no A/B tests are defined and abort.
4. Verify APIs:
   ```bash
   python3 /root/ads/ads_api.py auth facebook
   python3 /root/ads/ads_api.py auth google
   ```

### MONDAY — SETUP MODE

#### STEP 1: Read Test Definitions

Read `/root/ads/ads-ab-tests.md`. Expected format:
```markdown
## TEST-{ID}: {Test Name}
Status: ACTIVE | PAUSED | COMPLETED
Platform: FB | Google
Campaign: {CAMPAIGN_NAME or ID}
Variant A: {AD_ID or description} (control)
Variant B: {AD_ID or description} (challenger)
Start date: {DATE}
Metric: CTR | CPC | Cost-per-call
Min impressions: 1000
Min duration: 7 days
```

#### STEP 2: Verify Test Variants Are Running

For each ACTIVE test:
1. Check that Variant A ad is ACTIVE:
   ```bash
   python3 /root/ads/ads_api.py {fb|google} ads {ADSET_OR_CAMPAIGN_ID}
   ```
2. Check that Variant B ad is ACTIVE
3. Verify both are in the same adset/ad group (fair comparison)
4. Verify budget is split evenly (or using platform's native split test)

**If a variant is paused or missing:**
```bash
python3 /root/stocks/notify.py send "A/B Test {TEST_ID} issue: Variant {A|B} is not active.
Ad: {AD_NAME} (ID: {AD_ID})
Status: {CURRENT_STATUS}

Please check and re-enable, or update ads-ab-tests.md to mark test as PAUSED." --title "A/B Test Issue" --priority high --audience girish
```

#### STEP 3: Send Monday Summary

```bash
python3 /root/stocks/notify.py send "A/B Test Status — {DATE}

Active tests: {N}
{For each test:}
TEST-{ID}: {Name}
  Variant A: {AD_NAME} — running
  Variant B: {AD_NAME} — running
  Day {X} of test (min {Y} days)
  Impressions: A={X}, B={Y} (need {MIN} each)" --title "A/B Tests" --audience girish
```

### FRIDAY — EVALUATION MODE

#### STEP 1: Pull Metrics for Each Test

For each ACTIVE test:
```bash
# Get metrics since test start date
python3 /root/ads/ads_api.py {fb|google} ad-metrics {VARIANT_A_ID} {DAYS_SINCE_START}
python3 /root/ads/ads_api.py {fb|google} ad-metrics {VARIANT_B_ID} {DAYS_SINCE_START}
```

Extract for each variant:
- Impressions
- Clicks
- CTR
- CPC
- Conversions / Calls (if applicable)
- Cost per conversion/call

#### STEP 2: Statistical Significance Check

For CTR comparison:
1. Compute CTR for each variant: clicks / impressions
2. Compute standard error: SE = sqrt(p*(1-p)/n) for each variant
3. Compute Z-score: Z = (CTR_A - CTR_B) / sqrt(SE_A^2 + SE_B^2)
4. If |Z| > 1.96 → p < 0.05 → STATISTICALLY SIGNIFICANT

**Decision criteria — ALL must be met:**
- Both variants have 1000+ impressions
- Test has run for 7+ days
- p < 0.05 (|Z| > 1.96)

#### STEP 3: Declare Winner & Take Action

**If test is conclusive (all criteria met):**

Determine winner (higher CTR, lower CPC, or lower cost-per-call depending on test metric).

**FOR CAFE CAMPAIGNS — FULL AUTO:**
```bash
# Pause the loser
python3 /root/ads/ads_api.py fb pause {LOSER_AD_ID}
```

Log to `/root/ads/ads-changes-log.md`:
```markdown
### AUTO: A/B Test {TEST_ID} — Winner declared
- Winner: Variant {A|B} — {AD_NAME} (ID: {AD_ID})
  - CTR: {X}% vs {Y}% | CPC: Rs {X} vs Rs {Y}
  - Confidence: {Z-SCORE} (p={P_VALUE})
- Loser paused: {AD_NAME} (ID: {AD_ID})
- Time: {TIME} IST
```

Update `ads-ab-tests.md`: change test status to `COMPLETED`, record winner.

**FOR RESORT CAMPAIGNS — SUGGESTION ONLY:**
Write to `/root/ads/ads-suggestions.md`:
```markdown
## SGG-{DATE}-AB-{SEQ} [PENDING]
Platform: {Platform} (Resort)
Type: A/B Test winner — promote
Detail: Test {TEST_ID}: Variant {A|B} won with CTR {X}% vs {Y}% (p={P_VALUE})
Suggested action: Pause loser ad {AD_ID}, keep winner {AD_ID}
Created: {DATE} {TIME}
```

**If test is NOT yet conclusive:**
- Impressions too low → "Need more data — {X} more impressions needed"
- Duration too short → "Test needs {X} more days"
- No significant difference → "No winner yet — continue running"

#### STEP 4: Send Friday Summary

```bash
python3 /root/stocks/notify.py send "A/B Test Results — {DATE}

{For each test:}
TEST-{ID}: {Name}
  Variant A: CTR {X}%, CPC Rs {X}, {N} impressions
  Variant B: CTR {X}%, CPC Rs {X}, {N} impressions
  Result: {WINNER DECLARED / NEED MORE DATA / NO SIGNIFICANT DIFFERENCE}
  {Action taken / suggested}

{Overall: N tests evaluated, M winners declared}" --title "A/B Test Results" --priority high --audience girish
```

### CLEANUP
No browser used. No locks. Test state tracked in ads-ab-tests.md.
