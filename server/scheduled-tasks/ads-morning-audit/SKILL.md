---
name: ads-morning-audit
description: Daily 6:57 AM IST — 7 parallel agents audit Google Ads + Facebook Ads, take auto-actions on FB, recommend for Google
---

## MORNING ADS AUDIT — 7 PARALLEL AGENTS

Working directory: /root/ads
ADS API: python3 /root/ads/ads_api.py
NOTIFICATION: python3 /root/stocks/notify.py
STRATEGY DOCS: /root/ads-management/
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: Gate Checks

1. Set DATE variable: `TZ='Asia/Kolkata' date +%Y-%m-%d`
2. Check if audit already ran today: look for `ads-report-{DATE}.md` — if exists AND contains "MORNING_AUDIT_COMPLETE", skip.
3. Verify API auth:
   ```bash
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```
   If either fails, notify via Telegram and abort:
   ```bash
   python3 /root/stocks/notify.py send "Morning ads audit FAILED — auth error. Check credentials." --title "Ads Audit Error" --priority high --audience girish
   ```

### STEP 1: Notify Start

```bash
python3 /root/stocks/notify.py send "Starting morning ads audit..." --title "Ads Audit" --audience girish
```

### STEP 2: Launch 7 Agents in Parallel

Launch ALL 7 agents simultaneously. Each agent produces a structured output block.

**CRITICAL: Agents must NEVER hardcode campaign names, ad IDs, or budget amounts. Always query the API dynamically to discover what's active.**

**🚨 RULE #1 — RESORT vs CAFE AUTHORITY SPLIT (MANDATORY FOR ALL AGENTS):**
Before taking ANY auto-action on a Facebook campaign/adset/ad, check if it belongs to the RESORT:
- If the campaign name contains "Namooru", "Resort", or "Ecostay" → **APPROVAL ONLY** (treat like Google Ads — write suggestion to `ads-suggestions.md`, do NOT auto-pause/resume/adjust)
- If the campaign name contains "BUS", "Cafe", "BTM", "Jayanagar", or "Venue" → **FULL AUTO** (can pause, resume, rotate freely)
- If unclear → **APPROVAL ONLY** (err on the side of caution)

This applies to Agent 3 (Performance), Agent 4 (Fatigue), and any agent that takes write actions.

---

#### AGENT 1 — Google Ads Health Check (RECOMMEND ONLY)

**Goal:** Check overall Google Ads account health.

**Steps:**
1. Run `python3 /root/ads/ads_api.py google campaigns` — get all active campaigns dynamically
2. For each ENABLED campaign, run:
   - `python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 1` (yesterday)
   - `python3 /root/ads/ads_api.py google metrics {CAMPAIGN_ID} 7` (7-day baseline)
3. Run `python3 /root/ads/ads_api.py google budget` — check account balance

**Checks:**
- **CRITICAL: Account balance < Rs 5,000** → flag immediately (resort ran out of funds before)
- **Campaign paused unexpectedly** → flag
- **Yesterday CTR < 80% of 7-day average** → flag CTR drop
- **Yesterday CPC > 120% of 7-day average** → flag CPC spike
- **Yesterday conversions = 0 but 7-day avg > 0** → flag conversion drop
- **Daily spend < 80% of budget** → flag underspend (delivery issue)
- **Daily spend > budget** → flag overspend

**Baselines (from account-details.md, but ALWAYS compute fresh from 7-day data):**
- CTR baseline: compute from 7-day average
- CPC baseline: compute from 7-day average
- These are NOT hardcoded — recalculated every run

**Output format:**
```
GOOGLE_HEALTH: OK | WARNING | CRITICAL
ISSUES:
  - [SEVERITY] [DESCRIPTION]
METRICS_YESTERDAY:
  Campaign: [NAME] (ID: [ID])
  Clicks: X | Impr: X | CTR: X% | CPC: Rs X | Conv: X | Spend: Rs X
BUDGET_REMAINING: Rs X
```

---

#### AGENT 2 — Google Ads Search Terms Audit (RECOMMEND ONLY)

**Goal:** Find wasted spend and new keyword opportunities.

**Steps:**
1. Run `python3 /root/ads/ads_api.py google campaigns` — get active campaign IDs
2. For each ENABLED campaign:
   - `python3 /root/ads/ads_api.py google search-terms {CAMPAIGN_ID} 7`
   - `python3 /root/ads/ads_api.py google keywords {CAMPAIGN_ID}`
   - `python3 /root/ads/ads_api.py google negatives {CAMPAIGN_ID}`
3. Read strategy doc: `cat /root/ads-management/google-ads/keywords-and-negatives.md`

**Checks:**
- **Wasted spend terms:** Search terms with clicks > 2 AND conversions = 0 AND cost > Rs 50 → recommend as negative
- **New keyword opportunities:** Search terms with CTR > 5% not already in keyword list → recommend adding
- **Missing negatives:** Compare strategy doc's 220 recommended negatives against current negatives — list any still missing
- **Competitor searches:** Terms containing competitor names (wild valley, hombale, kaadgal, club cabana, wonderla, mangomist, guhantara, golden palms, area 83) not yet negative → flag
- **Irrelevant categories:** Terms matching jobs, real estate, directions, "how to reach", "reviews" → recommend as negatives

**Output format:**
```
SEARCH_TERMS_AUDIT:
  NEW_NEGATIVE_KEYWORDS: [list with spend wasted]
  NEW_POSITIVE_KEYWORDS: [list with CTR]
  MISSING_STRATEGY_NEGATIVES: [count] still not added
  COMPETITOR_TERMS_FOUND: [list]
  TOTAL_WASTED_SPEND: Rs X (on irrelevant terms in last 7 days)
```

---

#### AGENT 3 — Facebook Ads Performance Check (CAFE=FULL AUTO, RESORT=APPROVAL ONLY)

**Goal:** Check all FB campaigns, auto-pause underperforming CAFE campaigns. Resort campaigns: suggest only.

**Steps:**
1. Run `python3 /root/ads/ads_api.py fb campaigns` — get ALL campaigns dynamically
2. For each ACTIVE campaign:
   - `python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 1` (yesterday)
   - `python3 /root/ads/ads_api.py fb metrics {CAMPAIGN_ID} 7` (7-day baseline)
3. Read benchmarks: `cat /root/ads-management/fb-ads/benchmarks.md`

**Benchmark thresholds (from benchmarks.md — recalculate from 7-day data too):**
- CTR: Good > 1.5%, Alert < 0.8%
- CPC: Good < Rs 3, Alert > Rs 5
- CPM: Good < Rs 100, Alert > Rs 200
- Cost per call: baseline Rs 32 (Jaynagar Venue Bookings was best)

**Checks per campaign:**
- Yesterday CTR < 0.5% for 3+ consecutive days → **AUTO-PAUSE the campaign**, notify
- Yesterday CPC > 2x of 7-day average for 3+ days → **AUTO-PAUSE underperforming ad sets**
- Daily spend < 50% of budget → flag delivery issues
- Campaign with TRAFFIC objective that should be CALLS → flag (BTM BUS was known issue)

**Auto-actions — APPLY RULE #1 BEFORE EVERY ACTION:**
To check consecutive days, read `ads-changes-log.md` for prior flags. If this is the 3rd+ consecutive day of poor performance:

**FOR CAFE CAMPAIGNS (name contains BUS/Cafe/BTM/Jayanagar/Venue) — FULL AUTO:**
```bash
python3 /root/ads/ads_api.py fb pause-campaign {CAMPAIGN_ID}
# OR for ad-set level:
python3 /root/ads/ads_api.py fb pause-adset {ADSET_ID}
```
Log ALL auto-actions to `ads-changes-log.md`.

**FOR RESORT CAMPAIGNS (name contains Namooru/Resort/Ecostay) — DO NOT AUTO-ACT:**
Write a suggestion to `ads-suggestions.md` instead:
```
## SGG-{DATE}-{SEQ} [PENDING]
Platform: Facebook Ads (Resort)
Type: Pause underperforming campaign
Detail: [campaign name] has CTR X% (below 0.5%) for N consecutive days
Suggested action: Pause campaign {CAMPAIGN_ID}
```
Then notify via Telegram that a resort suggestion is pending.

**Output format:**
```
FB_PERFORMANCE:
  CAMPAIGNS_CHECKED: X
  HEALTHY: X | WARNING: X | CRITICAL: X
  AUTO_ACTIONS_TAKEN:
    - Paused campaign/adset [NAME] (ID: [ID]) — Reason: [reason]
  PER_CAMPAIGN:
    [NAME] (ID): CTR X% | CPC Rs X | Spend Rs X | Status: OK/WARNING/CRITICAL
  TOTAL_FB_SPEND_YESTERDAY: Rs X
```

---

#### AGENT 4 — Facebook Ad Fatigue Monitor (CAFE=FULL AUTO, RESORT=APPROVAL ONLY)

**Goal:** Detect creative fatigue, auto-rotate CAFE ads. Resort ads: suggest only.

**Steps:**
1. Run `python3 /root/ads/ads_api.py fb campaigns` — get active campaigns
2. For each ACTIVE campaign:
   - `python3 /root/ads/ads_api.py fb frequency {CAMPAIGN_ID}`
   - `python3 /root/ads/ads_api.py fb adsets {CAMPAIGN_ID}` → for each adset:
     - `python3 /root/ads/ads_api.py fb ads {ADSET_ID}` → for each ACTIVE ad:
       - `python3 /root/ads/ads_api.py fb ad-metrics {AD_ID} 7`
3. Read rotation rules: `cat /root/ads-management/fb-ads/ad-fatigue-rotation.md`
4. Read current rotation state: `cat /root/ads/ads-rotation-state.md` (if exists)

**Fatigue thresholds (from ad-fatigue-rotation.md):**
- Frequency > 3.0 = ROTATE NOW
- Frequency > 2.5 = WARNING
- CTR declined 20%+ from ad's first-week baseline = fatigued
- CPC increased 15%+ from baseline = fatigued
- 2+ simultaneous fatigue signals on same ad = ACTION REQUIRED

**Auto-actions — APPLY RULE #1 BEFORE EVERY ACTION:**
If an ad has frequency > 3.0 AND (CTR drop > 20% OR CPC rise > 15%):

**FOR CAFE ADS (parent campaign name contains BUS/Cafe/BTM/Jayanagar/Venue) — FULL AUTO:**
```bash
python3 /root/ads/ads_api.py fb pause {AD_ID}
```
Then check if there are paused "resting" ads that can be resumed (paused > 7 days ago per rotation state):
```bash
python3 /root/ads/ads_api.py fb resume {RESTED_AD_ID}
```

**FOR RESORT ADS (parent campaign name contains Namooru/Resort/Ecostay) — DO NOT AUTO-ACT:**
Write a suggestion to `ads-suggestions.md` instead:
```
## SGG-{DATE}-{SEQ} [PENDING]
Platform: Facebook Ads (Resort)
Type: Rotate fatigued ad
Detail: Ad [AD_NAME] (ID: [AD_ID]) in [CAMPAIGN_NAME] has frequency X (>3.0) and CTR dropped X%
Suggested action: Pause ad {AD_ID}, resume rested ad {RESTED_AD_ID}
```

**Update rotation state:** Write to `/root/ads/ads-rotation-state.md`:
```markdown
# Ad Rotation State — Updated {DATE}

## Campaign: [NAME] (ID)
| Ad ID | Ad Name | Status | Since | Frequency | CTR 7d | Fatigue? |
|-------|---------|--------|-------|-----------|--------|----------|
| xxx   | ...     | ACTIVE | date  | 2.1       | 1.8%   | NO       |
| yyy   | ...     | PAUSED | date  | 3.4       | 0.9%   | YES      |
| zzz   | ...     | RESTING| date  | -         | -      | Resting since date |
```

**URGENT notification:** If ALL ads in a campaign are paused (no fresh creatives left):
```bash
python3 /root/stocks/notify.py send "URGENT: All ads paused in [CAMPAIGN_NAME] — need new creatives!" --title "Creative Emergency" --priority urgent --audience girish
```

**Output format:**
```
FATIGUE_STATUS:
  CAMPAIGNS_CHECKED: X
  ADS_PAUSED_TODAY: [list with reasons]
  ADS_RESUMED_TODAY: [list — rested ads brought back]
  CAMPAIGNS_AT_RISK: [campaigns with 0-1 active ads left]
  ROTATION_SUMMARY: X active, Y paused, Z resting across all campaigns
```

---

#### AGENT 5 — Facebook Demographics & Targeting Audit (NOTIFY ONLY)

**Goal:** Check if spend is going to the right audience.

**Steps:**
1. Run `python3 /root/ads/ads_api.py fb campaigns` — get active campaigns
2. For each ACTIVE campaign:
   - `python3 /root/ads/ads_api.py fb demographics {CAMPAIGN_ID}`
   - `python3 /root/ads/ads_api.py fb placements {CAMPAIGN_ID}`
3. Read targeting strategy: `cat /root/ads-management/fb-ads/cafe-ad-strategy.md`

**Checks:**
- **Age drift:** If 18-24 age group getting > 20% of spend with CTR < campaign average → flag (known issue — Advantage+ was spending 46% on 18-24 before)
- **Gender split:** If one gender has CPC 2x the other → flag inefficiency
- **Placement efficiency:** Compare Feed vs Stories vs Reels — if one placement has CPC 3x others → flag
- **Target audience match:** Strategy says 22-35 primary, 25-65+ for resort. Check if actual spend aligns.

**Output format:**
```
DEMOGRAPHICS_AUDIT:
  CAMPAIGNS_CHECKED: X
  AGE_FLAGS: [age groups with disproportionate spend]
  PLACEMENT_FLAGS: [inefficient placements]
  TARGETING_DRIFT: YES/NO (with details)
```

---

#### AGENT 6 — Cross-Platform Budget Tracker (NOTIFY ONLY)

**Goal:** Track total ad spend, flag budget issues.

**Steps:**
1. Run `python3 /root/ads/ads_api.py google budget`
2. Run `python3 /root/ads/ads_api.py google campaigns` → sum yesterday's spend
3. Run `python3 /root/ads/ads_api.py fb account-spend 30`
4. Run `python3 /root/ads/ads_api.py fb campaigns` → get daily budgets
5. Calculate:
   - Google monthly spend pace (yesterday * days remaining in month)
   - FB monthly spend pace
   - Combined monthly projection

**Checks:**
- **Google balance < Rs 5,000** → CRITICAL (has run out before)
- **Google balance < Rs 15,000** → WARNING (< 3 days at Rs 4,900/day)
- **Monthly spend pace > 110% of expected** → flag overspend
- **Monthly spend pace < 80% of expected** → flag underspend (delivery issues)
- **FB token expiry < 7 days** → flag (check from auth debug info)

**Output format:**
```
BUDGET_STATUS: OK | LOW_FUNDS | CRITICAL
GOOGLE:
  Account balance: Rs X
  Daily burn rate: Rs X/day
  Days remaining at current rate: X
  Monthly spend (MTD): Rs X
  Projected month total: Rs X
FACEBOOK:
  Daily budget (total): Rs X/day
  Yesterday spend: Rs X
  Monthly spend (MTD): Rs X
  Projected month total: Rs X
  Token expires in: X days
COMBINED:
  Total daily spend: Rs X
  Total monthly projected: Rs X
```

---

#### AGENT 7 — Change Verifier (VERIFY ONLY)

**Goal:** Confirm yesterday's auto-changes took effect, detect manual changes.

**Steps:**
1. Read `cat /root/ads/ads-changes-log.md` — get yesterday's entries
2. For each change logged yesterday:
   - If ad was paused: verify via `python3 /root/ads/ads_api.py fb campaigns` / `fb ads` that it's still PAUSED
   - If budget was changed: verify current budget matches
   - If suggestion was approved: verify the change exists
3. Run `python3 /root/ads/ads_api.py google change-history 1` — check for manual Google Ads changes not made by this system

**Checks:**
- **Drift detected:** A change we made was reversed (ad resumed without our knowledge) → flag
- **External changes:** Someone made changes in Google Ads console → log for awareness
- **Stale suggestions:** Suggestions in `ads-suggestions.md` older than 7 days still PENDING → remind user

**Output format:**
```
CHANGE_VERIFICATION:
  CHANGES_VERIFIED: X of Y
  DRIFT_DETECTED: [any changes that were reversed]
  EXTERNAL_CHANGES: [changes made outside this system]
  STALE_SUGGESTIONS: X suggestions pending > 7 days
```

---

### STEP 3: Consolidate All Agent Outputs

After all 7 agents complete:

1. **Categorize issues by severity:**
   - CRITICAL: Account balance low, all ads paused in campaign, auth failing
   - WARNING: CTR drops, CPC spikes, fatigue approaching, targeting drift
   - INFO: Budget on track, minor optimization opportunities

2. **Write Google Ads suggestions to `/root/ads/ads-suggestions.md`:**
   Format each suggestion with unique ID:
   ```markdown
   ## SGG-{DATE}-{SEQ} [PENDING]
   Platform: Google Ads
   Type: [Add negative keyword | Add keyword | Fix targeting | etc.]
   Detail: [Specific finding with data]
   Suggested action: [What to do]
   Impact: [Estimated spend saved / conversions gained]
   Created: {DATE} {TIME}
   ```

3. **Log FB auto-actions to `/root/ads/ads-changes-log.md`:**
   ```markdown
   ## {DATE}

   ### AUTO: [Action description]
   - Object: [ID and name]
   - Campaign: [Campaign name]
   - Reason: [Data-driven reason]
   - Time: {TIME} IST
   ```

4. **Update ads-rotation-state.md** with Agent 4's rotation data.

### STEP 4: Send Telegram Summary

```bash
python3 /root/stocks/notify.py send "SUMMARY_TEXT" --title "Morning Ads Audit" --priority PRIORITY --audience girish
```

**Message format:**
```
Morning Ads Audit — {DATE}

GOOGLE ADS (Namooru Resort):
  Health: [OK/WARNING/CRITICAL]
  Yesterday: X clicks, Rs X spend, X conversions
  Budget remaining: Rs X
  [N suggestions pending — reply "ads suggestions"]

FACEBOOK ADS (BUS Cafe):
  Health: [OK/WARNING/CRITICAL]
  Yesterday: Rs X total spend across N campaigns
  Best: [campaign name] (Rs X/call)
  [Auto-actions: N taken]
  Fatigue: N ads approaching rotation

BUDGET:
  Total daily: Rs X (Google Rs X + FB Rs X)
  Google funds: Rs X remaining

[If CRITICAL issues: list them]
[If pending suggestions > 0: "Reply 'ads approve all' to approve"]
```

Use `--priority urgent` if any CRITICAL issues, `--priority high` if WARNINGs, default otherwise.

### STEP 5: Mark Complete

Append to the audit output section of `ads-report-{DATE}.md`:
```
MORNING_AUDIT_COMPLETE: {TIME} IST
```

### CLEANUP

No browser used. No locks to release. All state is in markdown files.
