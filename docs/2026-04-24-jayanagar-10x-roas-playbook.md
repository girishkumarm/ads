# 2026-04-24 — BUS Cafe Jayanagar: The 10x ROAS Playbook (Synthesis of 10+ Expert Agents)

## TL;DR — The honest truth about "10x ROAS"

You asked 10 specialists how to hit 10x ROAS. Here's what they actually said, combined:

**You're already past 10x Gross ROAS on first visit (~12.5x) and at ~90x on LTV.** The question "how do I get to 10x" is the wrong question. The right question is: **how do I scale profit per ad rupee without the ratio collapsing?** Because right now Rs 1,000/day ad spend on a saturation-curve model hits peak blended ROAS at ~Rs 1,500/day, after which marginal returns crater.

**The real growth is NOT ad optimization. It is monetization depth per customer.** Ad tuning buys you +20%. Business-model changes (loyalty, BUS Club membership, B2B catering, resort cross-sell) buy you +200-500%. The 12-month P&L swing, if all levers fire, is ~Rs 80 lakh: from -Rs 22L/yr loss → +Rs 60L/yr profit. **85% of that lift comes from business model, 15% from ad tuning.**

This document is the prioritized, API-implementable synthesis of every agent's finding.

---

## The 3 biggest levers ranked by ROI

| # | Lever | Effort | 12-month profit impact | Time-to-value |
|---|-------|--------|------------------------:|---------------|
| **1** | **Build `/cafe-jayanagar` landing page + proper tracking** | 1 week dev | **Unblocks everything** — enables Quality Score fix, bandits, store visits, attribution | 7 days |
| **2** | **Launch BUS Club Rs 999/mo membership + loyalty punch card** | 3 weeks | +Rs 30L/yr recurring | 30 days to 250 members |
| **3** | **B2B corporate catering outbound (20 offices within 500m)** | Weekly ongoing | +Rs 6L/mo by M12 | 60-90 days |

Everything else below is important but subordinate to these three.

---

## 30-60-90 day execution plan

### Week 1 — Unblock (fixes 80% of current waste)

| Day | Task | Owner | Done when |
|-----|------|-------|-----------|
| 1 | Tighten Search radius to 3.5 km, "Presence" only, add Jayanagar micro-neighborhood bid layers | Bot | API call done |
| 1 | Add 15 account-level audience exclusions (job seekers, bargain hunters, 65+, bottom-50% HHI) | Bot | API call done |
| 1 | **PAUSE PMax** until landing page is live (Rs 400/day saved) | Bot | Campaign PAUSED |
| 1 | Cut bids 50% during 11 AM-2 PM (you're already winning, stop overpaying) | Bot | Ad schedule updated |
| 1 | Cut bids 70% during 2-6 PM, kill 10 PM+ entirely | Bot | Ad schedule updated |
| 2 | Install Google Ads remarketing tag + 6 GA4 remarketing audiences site-wide | Girish + bot | Tag firing, audiences populating |
| 2 | Add 3 Custom Segments (Premium Coffee Searchers, Jayanagar Cafe Browsers, Work-from-Cafe) | Bot | Observation mode on all 4 ad groups |
| 3 | Seed 15 GBP Q&A (5 core + 3 couple + 4 birthday + 3 work) | Girish | All 15 live, upvoted |
| 3 | Upload first 30 GBP photos from cafe location (GPS match) | Girish | 30 live, diverse |
| 4 | Fix 5 GBP categories: Cafe (primary) + Coffee shop + Breakfast restaurant + Vegetarian restaurant + Event venue + Meeting place | Girish | Saved in GBP |
| 4 | Toggle all relevant GBP attributes (WiFi, outdoor seating, accessibility, UPI, LGBTQ+ friendly, etc.) | Girish | All true attrs on |
| 5 | Add 15 GBP Products with photos and prices (maps to 4 ad group themes) | Girish | 15 published |
| 5 | Add 8 GBP Services (dine-in, takeaway, birthday booking, catering, etc.) | Girish | 8 published |
| 5 | Enable GBP Messaging + set up canned responses | Girish | Chat button live |
| 6 | Start bill-flip review cards in every bill folder (target 7 reviews/day) | Girish | Cards printed + deployed |
| 7 | Build `namooru.com/cafe-jayanagar/` landing page (see spec below) | Dev | Page live at root + 4 anchor sections |

### Week 2-4 — Track + Test

- GA4 events wired: `get_directions`, `phone_call`, `menu_view`, `whatsapp_click`, `scroll_90`, `session_start_paid`
- Launch Week 1 ad copy A/B (RSA: "Cozy Cafe • Jayanagar 4th Block • Open till 11PM" vs current control)
- Launch Week 4 landing page bandit (namooru.com root vs `/cafe-jayanagar`) — Thompson sampling, 10% exploration
- Activate Zomato Book → appointment URL in GBP
- 5 GBP photos/day cadence, 3 GBP posts/week
- Reply to 100% reviews <24 hrs (replies are a ranking signal)
- Kick off BUS Club membership landing page + signup form (Rs 999/mo unlimited filter coffee + 15% off food)
- First B2B outbound batch: 20 office drops within 500m with cookies + rate card

### Week 5-8 — Optimize + Scale What Works

- Switch Search bid strategy Max Conversions → Target CPA Rs 30 (conversions have matured past 30 total — required threshold for tCPA)
- Switch attribution Last-Click → Data-Driven (should cross 300 conv/30-day threshold by day 16)
- Build Customer Match lists from: Zomato order history + WhatsApp inquiries + reservation log → upload (need 1,000+ records, hashed SHA-256, E.164 phone format)
- Launch dedicated RSAs per ad group (Core, Couple, Birthday, Work) instead of single shared copy
- Re-activate PMax with real audience signal (Customer Match + search converters + in-market Cafes)
- Add 1,500+ new GBP reviews pipeline underway (target 402 → 700 by Day 60)
- First corporate account signs (target: 3 accounts by M3 = Rs 2L/mo B2B revenue)

### Week 9-12 — Incrementality + Business Model Compound

- Run geo-holdout incrementality test (§4 Analytics agent) — 3 weeks, split 60/40 treatment/control, measure GBP panel directions in both
- Incrementality ratio decision: if IR > 0.65 → scale to Rs 1,500/day Search; if IR < 0.5 → stay at Rs 600/day and push budget into B2B + membership
- BUS Club at 150+ members (Rs 1.5L MRR recurring, locks 11 AM-3 PM dead hours)
- Launch merchandise line: 250g branded beans (Rs 650 retail / Rs 200 COGS = Rs 450 margin × 5 units/day = Rs 2,250/day pure margin)
- Launch Resort cross-sell: any cafe customer who spent >Rs 800 → Rs 500 Ecostay voucher via WhatsApp (one resort weekend conversion pays 6 months of cafe ad spend)

---

## What the bot can do autonomously via API (no user input needed)

These are implemented automatically as soon as the user approves this playbook:

1. Search radius → 3.5 km + presence-only (`location_criterion.location_type.presence_only`)
2. Jayanagar micro-neighborhood bid layers (+20% 3rd/4th/5th/7th/8th Block, -30% Koramangala, -20% HSR)
3. Dayparting: -50% 11-14h, -70% 14-18h, -100% 22h+, +30% 8-11h + 18-22h
4. Account-level audience exclusions (job seekers, bargain hunters, <lower-50% HHI, 65+, >5km radius, competitor offices)
5. 3 custom segments (Premium Coffee, Jayanagar Cafe Browsers, Work-from-Cafe) as Observation
6. In-market + Affinity + Life Events Observation mode on all 4 ad groups
7. Demographic bid adjustments (25-34 +30%, female +15%, top 10% HHI +40%, bottom 50% HHI -50%)
8. Pause PMax campaign 23769035916
9. RSA pinning: "BUS Cafe • Jayanagar 4th Block" pinned to HEADLINE_1 across all 4 ad groups
10. Negative keyword list additions from search-term report daily
11. SPC alerts on daily CPA (Shewhart chart, Western Electric rules)
12. Weekly budget reallocation script (§11 Analytics agent) — caps at ±30%/week, honors 14-day learning floor

## What needs you (Girish)

1. **Build `namooru.com/cafe-jayanagar/` landing page** — full JSON-LD schema, 4 anchor sections matching ad groups, GA4 dataLayer events, GBP embed, menu, phone CTA, WhatsApp button, Zomato book button
2. **GBP grunt work** — upload photos from the cafe location (GPS match matters), fix categories, toggle attributes, add 15 products + 8 services, seed 15 Q&A (needs owner account access Google won't give bot)
3. **BUS Club membership launch** — price at Rs 999/mo unlimited filter coffee + 15% off food, break-even is 12 drinks/mo per member
4. **B2B corporate outbound** — 20 office drops within 500m, LinkedIn Sales Nav outreach to admin/HR, sample voucher drops
5. **Bill-flip review cards** — print, deploy, train staff script
6. **Staff training** — review ask at UPI QR screen, WhatsApp post-visit review request, loyalty punch card discipline
7. **Upload hashed customer list** — Zomato orders + WhatsApp inquiries + reservations (need 1,000+ records to activate Customer Match)

---

## Landing page specification (`/cafe-jayanagar/`)

Required sections (anchor links match ad group final URLs):
- `#hero` — "BUS Cafe Jayanagar 4th Block" + hours + directions CTA + phone CTA + WhatsApp CTA
- `#dates` — couple/date messaging, cozy photos, propose-here CTA
- `#events` — birthday package Rs 4,999/10-pax, private upper floor, outside cake allowed
- `#work-friendly` — WiFi 150 Mbps, power sockets, quiet upper floor, no time limit
- `#menu` — full menu with prices + Zomato order button
- `#reviews` — GBP reviews embed (404+ reviews trust signal)
- `#contact` — map + address + phone + email

Technical requirements:
- JSON-LD `Restaurant` + `Menu` + `LocalBusiness` schema
- GA4 dataLayer events: `page_view`, `scroll_90`, `get_directions`, `phone_call`, `whatsapp_click`, `menu_view`, `book_table`
- Meta Pixel `PageView` + `Contact` + `ViewContent` on each section scroll
- GCLID captured to cookie + attached to form submissions (enables Enhanced Conversions for Leads via CSV upload)
- Mobile-first (99% of traffic is mobile per device data)
- Core Web Vitals: LCP <2.5s, CLS <0.1, INP <200ms (Quality Score factor)

Final URLs per ad group:
- Core → `namooru.com/cafe-jayanagar/`
- Couple Outing → `namooru.com/cafe-jayanagar/#dates`
- Birthday & Events → `namooru.com/cafe-jayanagar/#events`
- Work & Laptop Friendly → `namooru.com/cafe-jayanagar/#work-friendly`

---

## North Star metric — replace "10x ROAS" with a 3-tier dashboard

| Tier | Metric | Target | Cadence |
|------|--------|--------|---------|
| 1 | Contribution margin added per Rs 100 ad spend | Rs 150+ | Daily |
| 2 | New unique customers × blended LTV / weekly ad spend | **≥3:1 minimum, 5:1 healthy** | Weekly |
| 3 | **MRR growth from recurring sources** (BUS Club members + corporate + loyalty regulars) | 15%/month | Monthly |

Tier 3 is the only metric that makes the business worth franchising or selling. Directions clicks are an input, not an output.

---

## Statistical control on CPA (Shewhart SPC)

Daily CPA is expected to noise ±40% at current volume. Don't fix random variation. Fix only when Western Electric rules trip:
1. One point beyond ±3σ
2. Two of three consecutive points beyond ±2σ (same side)
3. Four of five consecutive points beyond ±1σ (same side)
4. Eight consecutive points on one side of μ

When alarm fires: pause new tests, check search terms, competitor auction insights, GBP status, landing page uptime. Bot runs this check daily at 9 AM IST via ads_api.py.

---

## Saturation model — when to stop scaling

Per Hill function calibration from current 4-day data (K ≈ Rs 2,720/day half-saturation):

| Daily spend | Walk-ins/mo | Revenue | Blended ROAS | Marginal ROAS |
|------------:|------------:|--------:|-------------:|--------------:|
| Rs 500 | 240 | 1.44L | 9.6x | 9.6x |
| Rs 1,000 (current) | 580 | 3.48L | **11.6x** | **13.6x** |
| Rs 1,500 | 780 | 4.68L | 10.4x | 8.0x |
| Rs 2,000 | 915 | 5.49L | 9.2x | 6.7x |
| Rs 3,000 | 1,140 | 6.84L | 7.6x | 4.5x |
| Rs 5,000 | 1,400 | 8.40L | 5.6x | 2.1x |
| Rs 10,000 | 1,700 | 10.20L | 3.4x | 0.6x |

**Rs 1,000-1,500/day is optimal for blended ROAS on ad spend alone.** Above that, marginal ROAS drops below 10x. Any additional rupee should go to **business-model levers (membership, catering, merch, loyalty)**, not into the ad auction.

---

## Realistic 12-month P&L (all 10 levers deployed)

| Revenue stream | M3 | M6 | M12 |
|----------------|---:|---:|----:|
| Walk-in dine-in (price+volume lift) | 5.0L | 6.5L | 8.0L |
| BUS Club membership | 0.5L | 1.5L | 2.5L |
| Corporate B2B catering | 0.8L | 3.0L | 6.0L |
| Events / private buyouts | 0.4L | 0.8L | 1.5L |
| Merch + beans + gift cards | 0.2L | 0.5L | 1.0L |
| Resort cross-sell attribution | 0.3L | 1.0L | 2.5L |
| **Total MRR** | **7.2L** | **13.3L** | **21.5L** |
| Blended contribution margin | 38% | 42% | 45% |
| Contribution Rs | 2.7L | 5.6L | 9.7L |
| Ad spend (scaled 3x if IR supports) | 60k | 90k | 90k |
| Fixed overhead | 3.0L | 3.3L | 3.8L |
| **Net profit/month** | **-0.9L** | **+1.3L** | **+5.0L** |

Annual swing: **-Rs 22L → +Rs 60L**. Ads = 15% of lift. Business model = 85%.

---

## Top 12 tactical plays — ranked by expected lift per rupee of effort

| # | Play | Expected lift | Implementation |
|---|------|---------------|----------------|
| 1 | Build `/cafe-jayanagar/` landing page | Unblocks QS, bandits, store visits, attribution | Week 1 dev |
| 2 | Dayparting cut (11-14 -50%, 14-18 -70%, 22+ kill) | +25% CPA on remaining spend | Today, API |
| 3 | Radius 3.5 km + presence-only + micro-neighborhood bids | -30% CPA | Today, API |
| 4 | Account-level audience exclusions (15 segments) | -15% waste | Today, API |
| 5 | Pause PMax until LP live + audience signal ready | Save Rs 400/day × 14 days = Rs 5,600 | Today, API |
| 6 | 3 custom segments as observation on all ad groups | -22% CPA (biggest audience lever) | Today, API |
| 7 | GBP: 5 secondary categories + 15 products + 8 services + 15 Q&A + attributes | 5-10x organic multiplier | Week 1, user |
| 8 | BUS Club Rs 999/mo membership launch | +Rs 2.5L/mo by M12 | Week 3, user |
| 9 | Loyalty punch card (6th coffee free) | LTV 60% → 150% | Week 2, user |
| 10 | Customer Match upload (Zomato + WhatsApp + reservation) | -38% CPA on matched | Week 5, user + bot |
| 11 | B2B corporate outbound (20 offices + LinkedIn + ad campaign) | +Rs 6L/mo B2B MRR by M12 | Week 4+, user |
| 12 | Resort cross-sell audience + Display retargeting | 1 resort conversion pays 6mo cafe ads | Week 6, bot |

---

## What the bot tracks daily (automated Telegram report at 6:03 PM IST)

From `scheduled-tasks/ads-evening-report/SKILL.md`:

- **Hero metrics:** today's CPA, yesterday's CPA, 7-day CPA, implied ROAS, implied contribution ROAS, LTV:CAC
- **Leading indicators:** IS lost rank %, CTR on top 5 terms, CPD 3-day MA, intent rate (calls + menu views / clicks), peak-hour density
- **Campaign health:** Search vs PMax spend + conv, ad group CPA chart, Quality Score distribution
- **Search waste:** top 10 cost terms with 0 conversions → negative keyword candidates
- **SPC alarm:** Shewhart rule fires → paged to Girish within 60s
- **Business metric tier 3:** BUS Club MRR growth, corporate account pipeline, loyalty punch completions

---

## The uncomfortable truth

Quote from the Business Model agent, unedited:

> You're already past 10x Gross ROAS on first visit. You're at ~90x on LTV. The question "how do I get to 10x" is moot. The real question is: how do I scale ad spend 5-10x without this ratio collapsing? Because right now you're spending Rs 1,000/day and probably leaving Rs 5-10k/day of profit on the table.

Quote from the Analytics agent, unedited:

> Scaling above Rs 1,500/day will actively destroy blended ROAS per the saturation model. The real work is proving it's incremental and compounding it with repeat visits — not scaling spend.

Quote from the GBP agent, unedited:

> 77 of 77 primary Ads conversions = "Get Directions" = pure local intent. GBP is already doing the heavy lifting — Ads just amplified it. Ranking BUS in the Google Local 3-Pack for "cafe in Jayanagar" / "cafe near me" is worth 5-10x the current Rs 1,000/day ad spend. It's free, compounds, and doesn't stop when you pause the budget.

**Bottom line:** Stop chasing 10x. Start compounding. Build the landing page this week, launch BUS Club in 3 weeks, start B2B outbound Monday. That's the actual path from -Rs 22L/yr to +Rs 60L/yr.

---

## Agent contributions index (full research backing this doc)

| # | Agent | Key deliverable |
|---|-------|-----------------|
| 1 | Keywords | 12 TTAG structure, Jayanagar landmark combos, SKAG transition plan |
| 2 | Bidding | Max Conv → tCPA Rs 20 at D+10, pin device bids Desktop/Tablet -90%, dayparting -25-70% dead hours |
| 3 | Landing page | Full `/cafe-jayanagar/` spec with JSON-LD schema + dataLayer wiring |
| 4 | Creative | 15 headlines + 5 long + 4 descriptions per ad group, 6 sitelinks each, 10 callouts, structured snippets, price extensions |
| 5 | PMax | PAUSE now; budget Rs 400/day too low for local (needs Rs 1,500+); gate re-activation on LP + walk-in tracking |
| 6 | Competitor | 8 Jayanagar competitors mapped (Third Wave, Matteo, Araku, Blue Tokai, Filter Coffee, Terra, Glen's, Smoor), Rs 130/day brand-defense strategy |
| 7 | Conversion tracking | Table tent QR + WhatsApp check-in for walk-in attribution; Enhanced Conversions for Leads via CSV; value per action |
| 8 | **Business model** | **10x ROAS is wrong goal; LTV:CAC 31x already; BUS Club + B2B + resort cross-sell = 85% of lift; -Rs 22L → +Rs 60L 12mo swing** |
| 9 | **GBP / Local SEO** | 5 secondary categories, 150 photos Day-1 plan, 402 → 1,000 reviews in 90 days, 15 seeded Q&A, 15 products, 8 services, Zomato Book integration |
| 10 | **Audience + Targeting** | 3.5 km presence-only radius, 3 custom segments (Premium Coffee, Jayanagar Cafe Browsers, Work-from-Cafe), demographic bid table, Customer Match 1k-seed path, -48% stacked CPA |
| 11 | **Analytics + Test-and-Learn** | 5 leading KPIs, 12-week A/B calendar with sample sizes, Thompson bandit code, geo-holdout incrementality test, Shewhart SPC control limits, Hill saturation model, budget reallocation algorithm |

---

## Files this playbook depends on (or must create)

| Status | File | Purpose |
|--------|------|---------|
| Exists | `docs/2026-04-24-jayanagar-search-keyword-restructure.md` | 4 ad group structure baseline |
| Exists | `docs/2026-04-24-pmax-cafe-launch.md` | PMax asset group state (currently PAUSED recommended) |
| Exists | `docs/2026-04-23-call-tracking-restored.md` | GTM phone_call + Meta Pixel Contact events |
| **TODO** | `namooru.com/cafe-jayanagar/` (live site) | Landing page (blocks everything) |
| **TODO** | `namooru.com/bus-corporate-catering/` | B2B landing page (Month 2) |
| **TODO** | `namooru.com/bus-club/` | Membership signup (Week 3) |
| **TODO** | `docs/gbp-90day-plan.md` | GBP execution checklist (extract from agent 9 output) |
| **TODO** | `docs/bus-club-membership-model.md` | BUS Club economics + signup flow |
| **TODO** | `docs/b2b-corporate-outbound-playbook.md` | 20-office outbound sequence |

---

*Synthesized from 10+ parallel specialist agents on 2026-04-24. Ground truth at `/tmp/cafe_ground_truth.md`. Full agent transcripts preserved in session a3324c1b-ddd2-42ff-838e-7b39266ecf3d.*
