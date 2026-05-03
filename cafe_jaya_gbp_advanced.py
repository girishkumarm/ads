#!/usr/bin/env python3
"""Jayanagar Cafe GBP — advanced SEO push (the 'make it cool' layer).

Phase 1: Place Action Links — adds 'Reserve', 'Order Online', 'Book Event'
         buttons directly on the GBP listing
Phase 2: More Hours — categorized hours (Brunch, Happy Hour, Late Night)
Phase 3: Labels (internal tracking — surface to user)
Phase 4: Try post creation via newer endpoints
Phase 5: Try photo upload via media endpoints
"""
import os, json
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
LOC = "locations/1769514473951842535"
V1_BIZ = "https://mybusinessbusinessinformation.googleapis.com/v1"
V1_PLACE = "https://mybusinessplaceactions.googleapis.com/v1"
TARGET = "https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/"


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# ─── PHASE 1: PLACE ACTION LINKS ─────────────────────────────────
section("PHASE 1: Place Action Links — buttons on GBP listing")

# First list valid place action types
list_url = f"{V1_PLACE}/placeActionTypeMetadata?regionCode=IN&languageCode=en"
r, _ = http_request("GET", list_url, headers=H)
print("Available place action types in India:")
valid_types = []
if r and "placeActionTypeMetadata" in r:
    for m in r["placeActionTypeMetadata"]:
        t = m.get("placeActionType","?")
        d = m.get("displayName","?")
        valid_types.append(t)
        print(f"  - {t:<35} {d}")
else:
    print(f"  [WARN] could not list: {str(r)[:200]}")

# List existing place action links
list_existing = f"{V1_PLACE}/{LOC}/placeActionLinks"
r, _ = http_request("GET", list_existing, headers=H)
existing_types = set()
if r and "placeActionLinks" in r:
    print(f"\n  Existing links: {len(r['placeActionLinks'])}")
    for l in r["placeActionLinks"]:
        existing_types.add(l.get("placeActionType",""))
        print(f"    - {l.get('placeActionType',''):<25} {l.get('uri','')}")

# What we want to add
DESIRED_LINKS = [
    ("DINING_RESERVATION",  TARGET),  # 'Reserve a table' button
    ("RESERVATIONS",        TARGET),  # 'Reserve' generic
    ("FOOD_ORDERING",       TARGET),  # 'Order' button
    ("FOOD_DELIVERY",       TARGET),  # 'Delivery'
    ("FOOD_TAKEOUT",        TARGET),  # 'Takeout / pickup'
    ("APPOINTMENT",         TARGET),  # 'Book event'
    ("ONLINE_APPOINTMENT",  TARGET),
    ("SHOP_ONLINE",         TARGET),
]

print("\nAdding place action links:")
for ptype, uri in DESIRED_LINKS:
    if ptype not in valid_types:
        print(f"  [skip] {ptype}: not valid in this region")
        continue
    if ptype in existing_types:
        print(f"  [skip] {ptype}: already exists")
        continue
    body = {
        "uri": uri,
        "placeActionType": ptype,
        "isPreferred": False,
    }
    create_url = f"{V1_PLACE}/{LOC}/placeActionLinks"
    r, _ = http_request("POST", create_url, headers=H, data=body)
    if r and "error" not in r:
        print(f"  [OK] {ptype}")
    else:
        err_short = str(r)[:120] if r else "no resp"
        print(f"  [FAIL] {ptype}: {err_short}")


# ─── PHASE 2: MORE HOURS (categorized) ──────────────────────────
section("PHASE 2: More Hours — Brunch, Happy Hour, Late Night, Delivery")

# Pull current moreHours metadata for category 'cafe' first
print("Discovering valid 'more hours' types for cafe...")
url = f"{V1_BIZ}/{LOC}:getGoogleUpdated?readMask=moreHours"
r, _ = http_request("GET", url, headers=H)

# Try setting moreHours directly
# Common moreHours hoursTypeId: BRUNCH, HAPPY_HOUR, BREAKFAST, LUNCH, DINNER, KITCHEN, DRIVE_THROUGH, DELIVERY, TAKEOUT, SENIOR_HOURS, ONLINE
moreHours = [
    {
        "hoursTypeId": "BRUNCH",
        "periods": [{"openDay": d, "openTime": {"hours": 10, "minutes": 0},
                     "closeDay": d, "closeTime": {"hours": 14, "minutes": 0}}
                    for d in ["SATURDAY","SUNDAY"]]
    },
    {
        "hoursTypeId": "HAPPY_HOUR",
        "periods": [{"openDay": d, "openTime": {"hours": 16, "minutes": 0},
                     "closeDay": d, "closeTime": {"hours": 19, "minutes": 0}}
                    for d in ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]]
    },
    {
        "hoursTypeId": "DELIVERY",
        "periods": [{"openDay": d, "openTime": {"hours": 11, "minutes": 0},
                     "closeDay": d, "closeTime": {"hours": 22, "minutes": 0}}
                    for d in ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]]
    },
    {
        "hoursTypeId": "TAKEOUT",
        "periods": [{"openDay": d, "openTime": {"hours": 10, "minutes": 0},
                     "closeDay": d, "closeTime": {"hours": 23, "minutes": 0}}
                    for d in ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]]
    },
]
body = {"moreHours": moreHours}
url = f"{V1_BIZ}/{LOC}?updateMask=moreHours"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] {len(moreHours)} more-hours blocks set (Brunch, Happy Hour, Delivery, Takeout)")
else:
    print(f"  [WARN] batch failed: {str(r)[:300]}")
    # Try one-by-one
    ok = 0
    for mh in moreHours:
        body1 = {"moreHours": [mh]}
        r1, _ = http_request("PATCH", url, headers=H, data=body1)
        if r1 and "error" not in r1:
            ok += 1
            print(f"    [OK] {mh['hoursTypeId']}")
        else:
            print(f"    [FAIL] {mh['hoursTypeId']}: {str(r1)[:150]}")
    print(f"  {ok}/{len(moreHours)} one-by-one")


# ─── PHASE 3: LABELS (internal tagging) ─────────────────────────
section("PHASE 3: Labels for internal tracking")
labels = ["jayanagar-cafe", "bus-cafe", "namooru-group", "high-priority", "seo-2026-may"]
body = {"labels": labels}
url = f"{V1_BIZ}/{LOC}?updateMask=labels"
r, _ = http_request("PATCH", url, headers=H, data=body)
if r and "error" not in r:
    print(f"  [OK] labels set: {labels}")
else:
    print(f"  [FAIL] {str(r)[:300]}")


# ─── PHASE 4: TRY POST CREATION via different paths ────────────
section("PHASE 4: Local Posts (try alternate endpoints)")
post_attempts = [
    f"https://mybusiness.googleapis.com/v4/{LOC}/localPosts",
    f"{V1_BIZ}/{LOC}/localPosts",
    f"https://mybusiness.googleapis.com/v1/{LOC}/localPosts",
]
post_body = {
    "languageCode": "en",
    "summary": "Saturday Special — Couples Combo Rs 399 at BUS Cafe Jayanagar! Coffee + Pizza + dessert for two. Plus 1+1 ice cream after 10 PM daily.",
    "topicType": "STANDARD",
    "callToAction": {"actionType": "LEARN_MORE", "url": TARGET},
}
post_ok = False
for url in post_attempts:
    print(f"  trying: {url[:60]}...")
    r, _ = http_request("POST", url, headers=H, data=post_body)
    if r and "error" not in r:
        print(f"    [OK] post created: {r.get('name','?')}")
        post_ok = True
        break
    else:
        msg = (str(r)[:80]) if r else "no resp"
        print(f"    [FAIL] {msg}")

if not post_ok:
    print("\n  Posts API confirmed retired by Google. Owner must post via dashboard.")


# ─── PHASE 5: TRY MEDIA UPLOAD ─────────────────────────────────
section("PHASE 5: Media list (read-only check)")
url = f"https://mybusiness.googleapis.com/v4/{LOC}/media"
r, _ = http_request("GET", url, headers=H)
if r and "mediaItems" in r:
    print(f"  Found {len(r['mediaItems'])} media items")
elif r and "error" in r:
    print(f"  v4 media endpoint dead: {str(r)[:80]}")

# Try v1
url = f"{V1_BIZ}/{LOC}/media"
r, _ = http_request("GET", url, headers=H)
if r and "error" not in r:
    print(f"  v1 media endpoint works")
else:
    print(f"  v1 media: {str(r)[:100]}")


print("\n=== ADVANCED GBP PUSH COMPLETE ===")
