# Automated Ads & SEO Management System

## What This Is
Automated 4-platform ads + SEO management system. Claude Code runs scheduled tasks on the Hetzner VPS — daily audits, auto-optimization, Telegram commands.

**Owner:** Girish Kumar
**Businesses:**
1. **Namooru Ecostay Resort** — Google Ads, Google Business Profile, GoDaddy (namooru.com)
2. **BUS Cafe** (Jayanagar + BTM Layout) — Facebook Ads

## Authority Matrix (CRITICAL — READ THIS FIRST)
| Platform | Business | Authority | Rule |
|----------|----------|-----------|------|
| Facebook Ads | **BUS Cafe** campaigns | **FULL AUTO** | Pause, rotate, optimize freely |
| Facebook Ads | **Namooru Resort** campaigns | **APPROVAL ONLY** | Suggest via Telegram, wait for OK |
| Google Ads | Namooru Resort | **APPROVAL ONLY** | Read metrics, suggest, wait for OK |
| Google Business Profile | Namooru Resort | **AUTO + APPROVAL** | Read auto, replies/posts need approval |
| GoDaddy | namooru.com | **AUTO checks, ASK for changes** | DNS/SSL monitoring auto, changes need OK |

**Resort detection for Facebook:** If campaign name contains "Namooru", "Resort", or "Ecostay" → treat as APPROVAL ONLY. Everything else (BUS, Cafe, BTM, Jayanagar, Venue) → FULL AUTO.

**Telegram notifications:** `python3 /root/stocks/notify.py send "message" --title "Title" --priority high --audience girish`

## Server Environment
- **Working directory:** /root/ads
- **Timezone:** Server runs UTC. IST = UTC + 5:30. All cron times must be UTC.
- **Strategy docs:** /root/ads-management/ (cloned from girishkumarm/ads-management)
- **Trading system:** /root/stocks/ (shared notify.py for Telegram)

## Key Files
| File | Purpose |
|------|---------|
| `ads_api.py` | Core API — Google Ads, Facebook Ads, Google Business Profile, GoDaddy |
| `ads-config.json` | API credentials for all 4 platforms (gitignored) |
| `.ads-token.json` | Cached OAuth tokens (gitignored) |
| `ads-suggestions.md` | Pending recommendations (Google Ads + Resort FB) |
| `ads-changes-log.md` | History of all auto-actions and approved changes |
| `ads-rotation-state.md` | Facebook ad creative rotation tracking |
| `ads-report-{DATE}.md` | Daily metrics report |
| `ads-weekly-review-{DATE}.md` | Weekly deep analysis |
| `server/scheduled-tasks/*/SKILL.md` | Instructions for each scheduled task |

## Scheduled Tasks

| UTC Time | IST Time | Task | Purpose |
|----------|----------|------|---------|
| `20 1 * * *` | 6:50 AM | ads-self-renewal | Verify all crons exist, recreate if missing |
| `27 1 * * *` | 6:57 AM | ads-morning-audit | 7 agents: health, search terms, FB perf, fatigue, demographics, budget, verify |
| `0 2 * * *` | 7:30 AM | gbp-daily-seo | GBP: reviews, insights, posts, monthly audit |
| `0 3 * * 1,4` | 8:30 AM Mon/Thu | ads-creative-health | Validate creative URLs, UTM params, landing pages |
| `0 3 * * 1` | 8:30 AM Mon | ads-ab-test-manager | A/B test setup (Mon) and evaluation (Fri) |
| `0 4 * * 1-5` | 9:30 AM weekdays | ads-budget-optimizer | Dynamic budget reallocation based on performance |
| `0 5 * * *` | 10:30 AM | gbp-qa-monitor | GBP Q&A monitoring, draft answers |
| `30 6 * * 1-5` | 12:00 PM weekdays | ads-midday-pulse | Midday spend pacing, anomaly detection |
| `0 8 * * *` | 1:30 PM | ads-approval-reminder | Re-ping stale suggestions |
| `33 12 * * *` | 6:03 PM | ads-evening-report | Full-day metrics, daily report, persist to JSON |
| `0 18 * * *` | 11:30 PM | ads-token-watchdog | Verify all tokens, warn on expiry |
| `0 */2 * * *` | Every 2 hours | ads-health-ping | Landing page uptime, campaign status, disapproved ads |
| `17 0 * * 1` | 5:47 AM Mon | ads-weekly-review | Deep weekly analysis, strategy review |
| `30 0 * * 1` | 6:00 AM Mon | godaddy-seo-monitor | Domain/SSL expiry, DNS audit |
| `0 21 * * 0` | 2:30 AM Sun | ads-competitor-watch | Auction insights, competitor reviews/pricing |
| `0 21 * * 0` | 2:30 AM Sun | ads-forecast | Spend projections, fatigue predictions, seasonal signals |
| `0 22 1 * *` | 3:30 AM 1st | ads-monthly-rollup | Monthly aggregates, MoM comparison, budget efficiency |

### Key State Files
| File | Purpose |
|------|---------|
| `ads-metrics-history.json` | Structured daily metrics for trend analysis |
| `ads-ab-tests.md` | A/B test definitions and results |
| `competitor-tracking.md` | Weekly competitor snapshots |
| `install-scripts/meta-pixel.html` | Meta Pixel code ready to install on namooru.com |
| `install-scripts/schema-markup.html` | JSON-LD schema markup for namooru.com |

## Ads API Quick Reference

```bash
# Authentication
python3 ads_api.py auth google              # Test Google OAuth
python3 ads_api.py auth facebook            # Test FB token + expiry

# Google Ads (read-only)
python3 ads_api.py google campaigns         # List campaigns
python3 ads_api.py google metrics CID 7     # 7-day metrics
python3 ads_api.py google keywords CID      # Keywords with quality score
python3 ads_api.py google negatives CID     # Negative keywords
python3 ads_api.py google search-terms CID 7  # What people searched
python3 ads_api.py google budget            # Account balance
python3 ads_api.py google recommendations   # Google's optimization suggestions
python3 ads_api.py google impression-share CID 7  # Search impression share
python3 ads_api.py google device-metrics CID 7    # Mobile vs desktop breakdown
python3 ads_api.py google hourly-metrics CID 7    # Hour-of-day performance
python3 ads_api.py google geo-metrics CID 7       # Geographic breakdown
python3 ads_api.py google auction-insights CID 30 # Competitor bidding data

# Facebook Ads (read + write)
python3 ads_api.py fb campaigns             # List all campaigns
python3 ads_api.py fb metrics CID 7         # Campaign insights
python3 ads_api.py fb frequency CID         # Fatigue detection
python3 ads_api.py fb demographics CID      # Age/gender breakdown
python3 ads_api.py fb pause AD_ID           # Pause ad (FULL AUTO)
python3 ads_api.py fb resume AD_ID          # Resume ad
python3 ads_api.py fb update-budget CID AMT # Change daily budget
python3 ads_api.py fb quality-ranking AD_ID 7   # Ad quality/engagement/conversion ranking
python3 ads_api.py fb video-metrics AD_ID 7     # Video view-through rates (25/50/75/100%)
python3 ads_api.py fb ad-review AD_ID           # Check if ad is disapproved + reason
python3 ads_api.py fb cost-unique CID 7         # Cost per unique click/impression

# Google Business Profile (Namooru Resort)
python3 ads_api.py gbp reviews              # List recent reviews
python3 ads_api.py gbp reply REVIEW_ID TEXT # Reply to a review
python3 ads_api.py gbp insights 7           # Views, searches, calls (7 days)
python3 ads_api.py gbp create-post TEXT     # Create a Google Post
python3 ads_api.py gbp info                 # Business info (hours, desc, etc.)
python3 ads_api.py gbp account              # GBP account info
python3 ads_api.py gbp locations            # List business locations

# GoDaddy (namooru.com)
python3 ads_api.py godaddy domain           # Domain info + expiry
python3 ads_api.py godaddy dns              # List DNS records
python3 ads_api.py godaddy dns-add TYPE NAME VALUE  # Add DNS record
python3 ads_api.py godaddy ssl              # SSL certificate status + expiry

# Combined
python3 ads_api.py summary                  # Both platforms overview
```

## Telegram Commands

**Ads commands:**
| Command | Action |
|---------|--------|
| `ads status` | Combined overview of both platforms |
| `ads issues` | Current CRITICAL/WARNING items |
| `ads resort` / `ads google` | Google Ads campaign details |
| `ads cafe` / `ads fb` | All FB campaign metrics |
| `ads cafe jnr` / `ads cafe btm` | Location-filtered FB metrics |
| `ads spend` | Monthly budget tracker |
| `ads suggestions` | Pending recommendations (Google + Resort FB) |
| `ads approve SGG-...` | Approve a specific suggestion |
| `ads approve all` | Approve all pending suggestions |
| `ads reject SGG-...` | Reject a suggestion |
| `ads pause AD_ID` | Manually pause an FB ad |
| `ads resume AD_ID` | Manually resume an FB ad |
| `ads report` | Latest daily report |
| `ads fatigue` | Creative rotation status |

**GBP commands:**
| Command | Action |
|---------|--------|
| `gbp reviews` | Latest reviews + pending replies |
| `gbp insights` | Views, searches, calls this week |
| `gbp post "text"` | Create a Google Post |
| `gbp reply REVIEW_ID "text"` | Reply to a review |

**GoDaddy commands:**
| Command | Action |
|---------|--------|
| `domain status` | Domain + SSL expiry |
| `dns check` | Current DNS records |
| `ssl check` | SSL certificate status |

## Rules
- **NEVER hardcode campaign names, ad IDs, or budget amounts.** Always query APIs dynamically.
- **ALWAYS read the SKILL.md** for each task before executing it.
- **ALWAYS notify via Telegram** on errors, decisions, and completions. Use `--audience girish`.
- **Google Ads = RECOMMEND ONLY.** Write suggestions to ads-suggestions.md, never make direct changes.
- **Facebook Ads (Cafe) = FULL AUTO.** Can pause/resume/adjust. Always log to ads-changes-log.md.
- **Facebook Ads (Resort) = APPROVAL ONLY.** Treat like Google — suggest, don't act.
- **Resort detection:** Campaign name contains "Namooru"/"Resort"/"Ecostay" → APPROVAL ONLY.
- **GBP = AUTO read, APPROVAL for replies/posts.** Draft and send to Telegram, wait for OK.
- **GoDaddy = AUTO monitoring, ASK for changes.** Never modify DNS without Girish's explicit approval.
- **Strategy docs in /root/ads-management/** are reference material. Read but don't rely on hardcoded values — always compute baselines from fresh API data.

## Telegram Listener (Girish AdsBot)

**Bot Name:** Girish AdsBot
**Poll frequency:** Every 1 minute (`* * * * *`)
**How it works:** Poll messages via `python3 /root/stocks/notify.py poll --since 2m`. Parse and respond to commands.

When polling messages, respond to these prefixes:
- **"ads ..."** → Ads management commands (see table above)
- **"gbp ..."** → Google Business Profile commands
- **"domain ..."** / **"dns ..."** / **"ssl ..."** → GoDaddy commands
- **"status"** → Combined overview of all platforms
- **"help"** → List available commands
- Any other message → Respond intelligently based on context

Always reply via: `python3 /root/stocks/notify.py send "response" --title "Ads Bot"`

## Startup / Recovery

When the bot starts (or restarts after a crash):

1. **Run setup:** `bash /root/ads/server-deploy.sh`
2. **Schedule ALL crons** (see Scheduled Tasks table above) — they expire after 7 days
3. **Check current state:**
   ```bash
   TZ='Asia/Kolkata' date +"%H:%M %A"
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py auth facebook
   ```
4. **Notify user:**
   ```bash
   python3 /root/stocks/notify.py send "Ads bot online. [X] crons scheduled." --title "Ads Bot Online" --priority high
   ```

## Google Ads Accounts

Two separate Google Ads accounts, BOTH managed by this bot:

| Account | Customer ID | Email | Business |
|---------|------------|-------|----------|
| Resort | 299-516-0429 | namooruresortsads@gmail.com | Namooru Ecostay |
| Cafe | 761-446-0903 | btm@brewinguntoldstories.com | BUS Cafe |

Both are under MCC 394-768-4492. The `cafe_customer_id` field in ads-config.json holds the cafe ID.

When querying Google Ads data, run commands for BOTH accounts and combine in reports.

## Google Ads Playwright Fallback (TEMPORARY)

**STATUS:** The Google Ads API developer token is currently "Test Account" access — cannot access production accounts. Basic Access has been applied for (takes 1-3 business days). Until approved, use Playwright browser automation to get Google Ads data.

**How to check if API is working:**
```bash
python3 ads_api.py google campaigns
```
If this returns data (not 404/error), the API is approved — **stop using Playwright and switch to API**.

**Playwright login credentials:**

| Account | URL | Email | Password |
|---------|-----|-------|----------|
| Resort | ads.google.com | namooruresortsads@gmail.com | Yuvan@123. |
| Cafe | ads.google.com | btm@brewinguntoldstories.com | Yuvan@123. |

**IMPORTANT:** If Google asks for mobile OTP or any 2FA/approval during login:
1. Send the prompt to Girish via Telegram: `python3 /root/stocks/notify.py send "Google Ads login needs OTP/approval for [account]. Please check your phone." --title "OTP Needed" --priority high`
2. Wait for Girish to respond via Telegram with the OTP or confirm approval
3. NEVER enter OTPs yourself — always ask Girish

**What to scrape via Playwright:**
- Campaign names, status, daily budget
- Clicks, impressions, CTR, CPC, cost, conversions (from Overview page)
- Search terms report (from Keywords → Search terms)
- Account balance (from Billing)
- Any warnings/recommendations

**Xvfb display:** `export DISPLAY=:99` (already running on VPS via systemd)

**Once API Basic Access is approved:** Delete this entire "Playwright Fallback" section from CLAUDE.md and switch all Google Ads operations to `ads_api.py` commands. The Playwright workaround is temporary only.

## Troubleshooting

### Google Ads API auth fails
```bash
rm -f .ads-token.json
python3 ads_api.py auth google
```
If still fails: refresh_token may be expired. Need to re-run OAuth flow.

### Facebook token expired
FB long-lived tokens last 60 days. System warns when < 7 days remain.
Generate new token: developers.facebook.com → Graph API Explorer → Generate User Token → Exchange for long-lived token.
Update `ads-config.json` with new `access_token`.

### API rate limits
Google Ads: 15,000 queries/day (more than enough for daily audits).
Facebook: 200 calls per hour per ad account. Morning audit uses ~50-80 calls.
