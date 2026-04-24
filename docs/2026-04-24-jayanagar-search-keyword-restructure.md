# 2026-04-24 — Jayanagar Cafe Search: Keyword Restructure

## Campaign
- **Account:** Resort (customer_id 2995160429)
- **Campaign:** Jayanagar Cafe - Search (id `23778954613`)
- **Budget:** Rs 600/day

## Problems fixed
1. Single ad group with mixed intent (walk-in, dates, birthdays, laptop-work) → low Quality Score on `cafe near me` (QS=1)
2. No dedicated ads/keywords for couple outings, birthdays/events, or laptop-friendly/work use cases
3. Rs 351 wasted spend in first 4 days on search terms that had no matching keyword (Google was forcing traffic onto `cafe near me` EXACT)
4. 4 dormant keywords with 0 impressions (too-narrow phrase matches)

## What was done

### Paused (4 keywords) — too narrow, zero traffic
- `work cafe Jayanagar wifi` (PHRASE)
- `literary cafe Bangalore` (PHRASE)
- `laptop friendly cafe Jayanagar` (PHRASE) — replaced with new Work & Laptop Friendly ad group
- `study cafe Jayanagar` (PHRASE) — replaced with new Work & Laptop Friendly ad group

### Added to Core ad group `195096525985` (14 new keywords, all PHRASE)
Plural/variant captures missed by original EXACT keywords:
- `cafes near me`, `coffee shop near me`, `coffee shops near me`, `coffee places near me`, `coffee cafe near me`
- `cafes in jayanagar`, `jayanagar cafes`, `cafe jayanagar 4th block`, `cafe in jayanagar 4th block`, `best cafe in jayanagar`
- `pure veg cafe jayanagar`, `pure veg cafe near me`
- `bus cafe jayanagar`, `brewing untold stories cafe`

### Created 3 new themed ad groups (with 40 keywords + 1 RSA each)

**1. Couple Outing - Jayanagar** (id `193683802457`, Max CPC Rs 7)
- 12 keywords: date cafe jayanagar, couple friendly cafe jayanagar, romantic cafe jayanagar, romantic cafe bangalore, cozy cafe jayanagar, couple cafe bangalore, best date place jayanagar, private cafe jayanagar, date places in bangalore (BROAD), couple cafe near me, couple cafe jayanagar, date night cafe jayanagar
- RSA: 15 headlines + 4 descriptions, all focused on date-night/couples angle

**2. Birthday & Events - Jayanagar** (id `193683802497`, Max CPC Rs 10)
- 14 keywords: birthday cafe jayanagar, birthday cafe bangalore, birthday celebration cafe jayanagar, birthday venue jayanagar, cafe for birthday party jayanagar, birthday place jayanagar, cafe to celebrate birthday, birthday booking cafe jayanagar, small party venue jayanagar, cafe party venue jayanagar, private dining jayanagar, group cafe jayanagar, cafe for events jayanagar, birthday cake cafe jayanagar
- Higher CPC because event-goers are high-value (group bookings)
- RSA: focused on private dining, event space, group bookings

**3. Work & Laptop Friendly - Jayanagar** (id `193683802537`, Max CPC Rs 6)
- 14 keywords: laptop friendly cafe jayanagar, laptop friendly cafe bangalore, work friendly cafe jayanagar, cafe with wifi jayanagar, wifi cafe jayanagar, cafe to work from jayanagar, work from cafe jayanagar, study cafe jayanagar, quiet cafe jayanagar, cafe for meetings jayanagar, cafe with plug points jayanagar, co working cafe jayanagar, remote work cafe bangalore, cafe to study jayanagar
- RSA: WiFi, plug points, quiet vibe, all-day work welcome

## Final campaign structure
```
Campaign: Jayanagar Cafe - Search (Rs 600/day)
├── Core Keywords (28 keywords, 1 RSA)          — Max CPC Rs 18 [original ad group]
├── Couple Outing (12 keywords, 1 RSA)          — Max CPC Rs 7
├── Birthday & Events (14 keywords, 1 RSA)      — Max CPC Rs 10
└── Work & Laptop Friendly (14 keywords, 1 RSA) — Max CPC Rs 6

Total: 68 keywords, 4 ad groups, 4 RSAs
```

## Still TODO (for the ads bot / Girish)

### High priority — landing page (fixes Quality Score)
The QS=1 problem on `cafe near me` will not fix until we have a dedicated cafe landing page. Currently all ads point to `https://namooru.com/` which is the resort homepage. Build:
- `namooru.com/cafe-jayanagar` (or separate domain) with:
  - BUS Cafe - Jayanagar branding front and center
  - Address, phone, map, hours
  - Menu (or menu link)
  - Sections matching each theme: "Date nights", "Birthday parties", "Work-friendly"
  - Phone call button (tracked by GTM `Click to Call - Phone Links` trigger)
  - WhatsApp button
- Update `finalUrls` in each RSA to point the right section of the landing page:
  - Couple Outing → `/cafe-jayanagar#dates`
  - Birthday → `/cafe-jayanagar#events`
  - Work → `/cafe-jayanagar#work-friendly`
  - Core → `/cafe-jayanagar`

### Medium priority — add negatives based on next 7 days of search terms
Check search term report daily via:
```bash
python3 ads_api.py google search-terms 23778954613 7
```
Add as campaign-level negatives any term with 3+ clicks and 0 conversions after 7 days.

### Low priority
- Add sitelink extensions per ad group (Menu, Call Now, Directions, Book a Table)
- Add call extension with phone +918618547729
- Add location extension once Google Business Profile is linked

## Verification commands
```bash
# Check all keywords
python3 ads_api.py google keywords 23778954613

# Check daily performance per ad group
python3 ads_api.py google metrics 23778954613 7

# Check search terms + waste
python3 ads_api.py google search-terms 23778954613 7
```
