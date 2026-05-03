#!/usr/bin/env python3
"""Resort campaign 21740834372 — create 'Group Bookings & Events' ad group.

Goal: target ONLY big-group bookings (weddings, corporate offsites, big
birthday parties, 50+ people events). Block couple/individual/staycation
intent at the AG level via negatives.

Phase 1: Create new ad group
Phase 2: Add 25 high-intent keywords (mix EXACT + PHRASE)
Phase 3: Add 8 AG-level negatives to block individual intent
Phase 4: Create RSA with group-focused copy + assets
Phase 5: Add 6 AG-level callouts
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

from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"
TARGET_URL = "https://namooru.com/?utm_source=google&utm_medium=cpc&utm_campaign=resort_group_bookings"

cfg = load_config()
cl = _get_google_ads_client(cfg)


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# ─── PHASE 1: CREATE NEW AD GROUP ──────────────────────────────
section("PHASE 1: Create new ad group 'Group Bookings & Events'")
ag_svc = cl.get_service("AdGroupService")
op = cl.get_type("AdGroupOperation")
new = op.create
new.name = "Group Bookings & Events"
new.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
new.status = cl.enums.AdGroupStatusEnum.ENABLED
new.type_ = cl.enums.AdGroupTypeEnum.SEARCH_STANDARD
# Even though MAX_CONV ignores keyword bids, set higher AG default
new.cpc_bid_micros = 35 * 1_000_000  # ₹35 — high priority signal

try:
    r = ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[op])
    AG_RN = r.results[0].resource_name
    AG_ID = AG_RN.split("/")[-1]
    print(f"  [OK] AG created: {AG_RN} (id={AG_ID})")
except Exception as e:
    print(f"  [FAIL] {str(e)[:400]}")
    raise


# ─── PHASE 2: ADD 25 GROUP-INTENT KEYWORDS ──────────────────────
section("PHASE 2: Add 25 group-intent keywords")
GROUP_KEYWORDS = [
    # High-intent EXACT
    ("wedding resort bangalore",            "EXACT"),
    ("destination wedding bangalore",       "EXACT"),
    ("wedding venue near bangalore",        "EXACT"),
    ("wedding venue bangalore",             "EXACT"),
    ("corporate offsite resort bangalore",  "EXACT"),
    ("corporate offsite venue bangalore",   "EXACT"),
    ("team outing resort bangalore",        "EXACT"),
    ("team outing places near bangalore",   "EXACT"),
    ("birthday party resort bangalore",     "EXACT"),
    ("group booking resort bangalore",      "EXACT"),
    ("reception venue bangalore",           "EXACT"),
    ("event venue near bangalore",          "EXACT"),
    # PHRASE for variants
    ("wedding resort kanakapura",           "PHRASE"),
    ("corporate offsite kanakapura",        "PHRASE"),
    ("marriage venue near bangalore",       "PHRASE"),
    ("private party venue bangalore",       "PHRASE"),
    ("birthday banquet hall bangalore",     "PHRASE"),
    ("destination wedding kanakapura",      "PHRASE"),
    ("company offsite bangalore",           "PHRASE"),
    ("corporate retreat resort",            "PHRASE"),
    ("group resort booking bangalore",      "PHRASE"),
    ("large group resort bangalore",        "PHRASE"),
    ("50 people resort booking",            "PHRASE"),
    ("100 people resort booking",           "PHRASE"),
    ("party venue near bangalore",          "PHRASE"),
]

agc_svc = cl.get_service("AdGroupCriterionService")
ops = []
for text, match in GROUP_KEYWORDS:
    op = cl.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = AG_RN
    c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
    c.keyword.text = text
    c.keyword.match_type = getattr(cl.enums.KeywordMatchTypeEnum, match)
    ops.append(op)

ok = 0
try:
    r = agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
    ok = len(r.results)
    print(f"  [OK] {ok} keywords added in batch")
except Exception as e:
    print(f"  [WARN] batch failed, retrying one-by-one")
    for i, op in enumerate(ops):
        try:
            agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
            ok += 1
            print(f"    [OK] [{GROUP_KEYWORDS[i][1]}] {GROUP_KEYWORDS[i][0]}")
        except Exception as e2:
            print(f"    [FAIL] '{GROUP_KEYWORDS[i][0]}': {str(e2)[:120]}")
print(f"\n  {ok}/{len(GROUP_KEYWORDS)} keywords live")


# ─── PHASE 3: AG-LEVEL NEGATIVE KEYWORDS ────────────────────────
section("PHASE 3: Add 10 AG-level negatives (block individual intent)")
# These block individual / couple / day-out / staycation searches
# from matching this AG's keywords, while leaving other AGs unaffected
NEG_AG = [
    ("couples",            "PHRASE"),
    ("honeymoon",          "PHRASE"),
    ("staycation",         "PHRASE"),
    ("day outing",         "PHRASE"),
    ("day out",            "PHRASE"),
    ("for couple",         "PHRASE"),
    ("for 2",              "PHRASE"),
    ("solo",               "PHRASE"),
    ("single",             "BROAD"),
    ("1 night stay",       "PHRASE"),
]
ops = []
for text, match in NEG_AG:
    op = cl.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = AG_RN
    c.negative = True
    c.keyword.text = text
    c.keyword.match_type = getattr(cl.enums.KeywordMatchTypeEnum, match)
    ops.append(op)
ok = 0
for i, op in enumerate(ops):
    try:
        agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
        ok += 1
        print(f"  [OK] NEG [{NEG_AG[i][1]}] {NEG_AG[i][0]}")
    except Exception as e:
        print(f"  [FAIL] {NEG_AG[i][0]}: {str(e)[:120]}")
print(f"\n  {ok}/{len(NEG_AG)} negatives applied")


# ─── PHASE 4: CREATE RSA WITH GROUP-FOCUSED COPY ────────────────
section("PHASE 4: Create RSA with group-focused copy")
ad_svc = cl.get_service("AdGroupAdService")
op = cl.get_type("AdGroupAdOperation")
ad = op.create
ad.ad_group = AG_RN
ad.status = cl.enums.AdGroupAdStatusEnum.ENABLED
rsa = ad.ad.responsive_search_ad

HEADLINES = [
    "Wedding Resort Bangalore",
    "Destination Wedding Venue",
    "Corporate Offsite Resort",
    "Team Outing Place 60 Km",
    "Group Booking 50-300 Guests",
    "Big Birthday Party Venue",
    "Reception Hall Near Bangalore",
    "35 Acres - Forest Resort",
    "Wedding Mandap & Banquet",
    "Bulk Booking Discounts",
    "Private Event Venue Hire",
    "Kanakapura Resort Bookings",
    "From Rs 2,499 Per Head",
    "100-300 Guests Capacity",
    "Custom Group Packages",
]
for h in HEADLINES:
    asset = rsa.headlines.add()
    asset.text = h
DESCRIPTIONS = [
    "Premium 35-acre eco resort hosts weddings, corporate offsites & big birthday parties. From Rs 2,499/head. Book direct.",
    "Banquet hall + open mandap + cottages for 100-300 guests. 60 km from Bangalore on Kanakapura Road.",
    "Group bookings for 50-300 guests. Custom packages, in-house catering, decor. Reserve your date today.",
    "Wedding venue, corporate offsite, big birthday hall - one stop. Direct booking saves more.",
]
for d in DESCRIPTIONS:
    asset = rsa.descriptions.add()
    asset.text = d
ad.ad.final_urls.append(TARGET_URL)
rsa.path1 = "groups"
rsa.path2 = "events"

try:
    r = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
    AD_ID = r.results[0].resource_name.split("/")[-1].split("~")[1]
    print(f"  [OK] RSA created: AD {AD_ID}")
    print(f"    {len(HEADLINES)} headlines, {len(DESCRIPTIONS)} descriptions")
except Exception as e:
    print(f"  [FAIL] RSA: {str(e)[:600]}")


# ─── PHASE 5: AG-LEVEL CALLOUTS ─────────────────────────────────
section("PHASE 5: Add 6 AG-level callouts")
a_svc = cl.get_service("AssetService")
aga_svc = cl.get_service("AdGroupAssetService")

CALLOUTS = [
    "100-300 Guest Capacity",
    "Wedding Mandap Setup",
    "Banquet & Open Lawn",
    "In-House Catering",
    "Group Discount 10%+",
    "Free Site Visit",
]
for text in CALLOUTS:
    try:
        op = cl.get_type("AssetOperation")
        op.create.callout_asset.callout_text = text
        r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
        rn = r.results[0].resource_name
        op2 = cl.get_type("AdGroupAssetOperation")
        op2.create.ad_group = AG_RN
        op2.create.asset = rn
        op2.create.field_type = cl.enums.AssetFieldTypeEnum.CALLOUT
        aga_svc.mutate_ad_group_assets(customer_id=CUSTOMER_ID, operations=[op2])
        print(f"  [OK] '{text}'")
    except Exception as e:
        print(f"  [FAIL] '{text}': {str(e)[:120]}")


# ─── SAVE STATE ─────────────────────────────────────────────────
state = {
    "ag_id": AG_ID, "ag_name": "Group Bookings & Events",
    "ag_resource_name": AG_RN,
    "campaign_id": CAMP_ID,
    "keywords": [k for k,_ in GROUP_KEYWORDS],
    "negatives": [n for n,_ in NEG_AG],
}
with open("/Users/girishkumar/Documents/ads/.resort_group_ag_state.json","w") as f:
    json.dump(state, f, indent=2)

print(f"\n=== AD GROUP CREATED — id {AG_ID} — state saved ===")
