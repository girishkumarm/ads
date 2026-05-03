#!/usr/bin/env python3
"""Namooru Ecostay Resort GBP — full SEO push.

Phase 1: Add 4 more categories (Eco resort, Wedding venue, Event venue, Tour operator)
Phase 2: Write 720-char SEO-rich description (was empty!)
Phase 3: Rewrite all 12 service items with proper descriptions + add 4 new
Phase 4: Add CHECK_IN, CHECK_OUT, KITCHEN, POOL more-hours
Phase 5: Special hours for next 90 days (long weekends + festivals)
"""
import os, json, datetime
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, gbp_get_token, http_request

cfg = load_config()
token = gbp_get_token(cfg)
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
LOC = "locations/10815844322260560435"
V1 = "https://mybusinessbusinessinformation.googleapis.com/v1"


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# ─── PHASE 1: ADD CATEGORIES ────────────────────────────────────
section("PHASE 1: Add 4 more categories")
url = f"{V1}/{LOC}?readMask=categories"
r, _ = http_request("GET", url, headers=H)
current_pri = r.get("categories", {}).get("primaryCategory", {}).get("name", "categories/gcid:resort_hotel")
current_add = [c["name"] for c in r.get("categories", {}).get("additionalCategories", [])]
print(f"  Current additional: {len(current_add)}")

NEW_CATS = [
    "categories/gcid:wedding_venue",
    "categories/gcid:event_venue",
    "categories/gcid:tour_operator",
    "categories/gcid:vacation_home_rental_agency",
]
combined = list(set(current_add) | set(NEW_CATS))
print(f"  Adding: {NEW_CATS}")
body = {"categories": {"primaryCategory": {"name": current_pri},
                       "additionalCategories": [{"name": c} for c in combined]}}
url = f"{V1}/{LOC}?updateMask=categories"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] {len(combined)} additional categories total")
else:
    print(f"  [FAIL] {str(r)[:300]}")
    # Try one-by-one to see which is invalid
    for c in NEW_CATS:
        if c in current_add: continue
        single_combined = list(set(current_add) | {c})
        body = {"categories": {"primaryCategory": {"name": current_pri},
                               "additionalCategories": [{"name": x} for x in single_combined]}}
        r1, _ = http_request("PATCH", url, headers=H, data=body)
        if r1 and "error" not in r1:
            print(f"    [OK] added {c}")
            current_add.append(c)
        else:
            print(f"    [SKIP] {c}: {str(r1)[:120]}")


# ─── PHASE 2: DESCRIPTION ───────────────────────────────────────
section("PHASE 2: Write 720-char SEO-rich description (was EMPTY)")
NEW_DESC = (
    "Namooru Ecostay is an award-winning eco resort 60 km from Bangalore on "
    "Kanakapura Road, set across 35 acres of untouched nature in Banthamari "
    "State Forest. Premium AC cottages, family suites, and romantic couples "
    "retreats with mountain views. Enjoy organic farm-to-table meals, infinity "
    "pool, bonfire nights, trekking, ATV rides, archery, and bird watching. "
    "Pet-friendly and family-welcoming. Ideal for weekend getaways, day-outs, "
    "corporate offsites, weddings, and honeymoons. Day packages from Rs 1,499 "
    "with pool, lunch, and activities. Stays from Rs 5,499/night with breakfast. "
    "Located at Kootagondanahalli village, Kanakapura. Book direct on "
    "namooru.com for best rates and same-day confirmation."
)
print(f"  Length: {len(NEW_DESC)} chars (max 750)")
body = {"profile": {"description": NEW_DESC}}
url = f"{V1}/{LOC}?updateMask=profile.description"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] description set")
else:
    print(f"  [FAIL] {str(r)[:300]}")


# ─── PHASE 3: SERVICE ITEMS WITH FULL DESCRIPTIONS ──────────────
section("PHASE 3: Rewrite all 12 service items + add new ones")
RESORT_SERVICES = [
    ("Day Outing Package",       "Pool, lunch, indoor games & activities. 9am-7pm. From Rs 1,499/head."),
    ("Couples Cottage Stay",     "AC private cottage with mountain view, breakfast included. From Rs 5,499/night."),
    ("Family Cottage 4-Pax",     "Two-room AC cottage, breakfast included. Ideal for family of 4. From Rs 8,499/night."),
    ("Corporate Offsite",        "Day or overnight team package with activities, meals, AV. From Rs 1,999/head, 15+ pax."),
    ("Wedding & Reception",      "Open-air mandap or banquet hall. 100-300 guest capacity. From Rs 2,499/head."),
    ("Honeymoon Package",        "Candle-lit dinner, room decor, breakfast in bed, complimentary spa. From Rs 9,999/night."),
    ("Adventure Activities",     "Trekking, ATV rides, archery, zorbing, rappelling, bird watching. Inclusive of day packages."),
    ("Bonfire & BBQ Night",      "Bonfire setup, live BBQ, music. Rs 599/head additional. Available 7-10pm."),
    ("Pet-Friendly Stay",        "Pets stay free. Open lawns, outdoor seating, pet-friendly cottages on request."),
    ("Birthday Celebration",     "Venue + decor + custom cake. Indoor or outdoor setup. From Rs 5,999."),
    ("Pre-Wedding Shoot",        "4-hour venue access for photography. Pool, forest, lawn locations. From Rs 7,999."),
    ("Pool Day Pass",            "Pool-only access 11am-6pm with welcome drink. From Rs 999/head."),
    ("Holiday Resort",           "Weekend or weekday stays with full board, activities, pool. From Rs 6,999/night."),
    ("Forest Resort Stay",       "Eco cottages bordering Banthamari State Forest. Birdwatching, nature trails. From Rs 5,499."),
    ("Group Stay 10+ Pax",       "Bulk booking 10+ rooms. Discount packages with custom meal plans."),
    ("Kanakapura Resort",        "Stay at South Bangalore's top-rated eco resort, 60 km from Bangalore."),
]
service_items = []
for name, desc in RESORT_SERVICES:
    service_items.append({
        "freeFormServiceItem": {
            "category": "categories/gcid:resort_hotel",
            "label": {"displayName": name, "description": desc, "languageCode": "en"}
        }
    })
print(f"  Setting {len(service_items)} service items")
body = {"serviceItems": service_items}
url = f"{V1}/{LOC}?updateMask=serviceItems"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] {len(service_items)} service items rewritten with full descriptions")
else:
    print(f"  [FAIL] {str(r)[:300]}")


# ─── PHASE 4: MORE HOURS (Check-in, Check-out, Restaurant, Pool) ─
section("PHASE 4: More Hours — Check-in, Check-out, Pool, Kitchen")
DAYS_ALL = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]
moreHours = [
    {
        "hoursTypeId": "BREAKFAST",
        "periods": [{"openDay": d, "openTime": {"hours": 7, "minutes": 30},
                     "closeDay": d, "closeTime": {"hours": 10, "minutes": 30}}
                    for d in DAYS_ALL]
    },
    {
        "hoursTypeId": "KITCHEN",
        "periods": [{"openDay": d, "openTime": {"hours": 7, "minutes": 0},
                     "closeDay": d, "closeTime": {"hours": 22, "minutes": 30}}
                    for d in DAYS_ALL]
    },
]

# Check-in / Check-out / Pool may not be valid hoursTypeIds — try
EXPERIMENTAL = [
    ("CHECK_IN",  [{"openDay": d, "openTime": {"hours": 14, "minutes": 0},
                    "closeDay": d, "closeTime": {"hours": 22, "minutes": 0}} for d in DAYS_ALL]),
    ("CHECK_OUT", [{"openDay": d, "openTime": {"hours": 11, "minutes": 0},
                    "closeDay": d, "closeTime": {"hours": 12, "minutes": 0}} for d in DAYS_ALL]),
    ("POOL",      [{"openDay": d, "openTime": {"hours": 6, "minutes": 0},
                    "closeDay": d, "closeTime": {"hours": 21, "minutes": 0}} for d in DAYS_ALL]),
    ("HAPPY_HOUR",[{"openDay": d, "openTime": {"hours": 18, "minutes": 0},
                    "closeDay": d, "closeTime": {"hours": 20, "minutes": 0}} for d in DAYS_ALL]),
]

# Set base ones first
body = {"moreHours": moreHours}
url = f"{V1}/{LOC}?updateMask=moreHours"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] base moreHours set ({len(moreHours)} types)")
    final_more = list(moreHours)
else:
    print(f"  [WARN] base failed: {str(r)[:200]}")
    final_more = []

# Try adding experimental ones one at a time
for type_id, periods in EXPERIMENTAL:
    test = final_more + [{"hoursTypeId": type_id, "periods": periods}]
    body = {"moreHours": test}
    r, _ = http_request("PATCH", url, headers=H, data=body)
    if r and "error" not in r:
        print(f"  [OK] added {type_id}")
        final_more = test
    else:
        print(f"  [skip] {type_id}: {str(r)[:120]}")


# ─── PHASE 5: SPECIAL HOURS for next 90 days ────────────────────
section("PHASE 5: Special hours for upcoming holidays (next 90d)")
SPECIALS = [
    # Indian holidays/long weekends 2026 May-July
    ("2026-05-01", 9, 0, 23, 30, False, "May Day"),
    ("2026-05-23", 9, 0, 23, 30, False, "Buddha Purnima"),
    ("2026-06-15", 9, 0, 23, 30, False, "Father's Day"),
    ("2026-07-29", 9, 0, 23, 30, False, "Bakrid"),
]
periods = []
for d, oh, om, ch, cm, closed, name in SPECIALS:
    y, m, day = map(int, d.split("-"))
    p = {
        "startDate": {"year": y, "month": m, "day": day},
        "endDate":   {"year": y, "month": m, "day": day},
        "closed": closed,
    }
    if not closed:
        p["openTime"]  = {"hours": oh, "minutes": om}
        p["closeTime"] = {"hours": ch, "minutes": cm}
    periods.append(p)

body = {"specialHours": {"specialHourPeriods": periods}}
url = f"{V1}/{LOC}?updateMask=specialHours"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] {len(periods)} special-hour periods set")
else:
    print(f"  [FAIL] {str(r)[:300]}")


print("\n=== RESORT GBP SEO PUSH COMPLETE ===")
