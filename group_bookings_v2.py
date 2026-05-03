#!/usr/bin/env python3
"""Group Bookings v2 — verified keywords only + ₹500/day cap + corporate balance.

Per user 2026-05-03:
  1. Drop all zero-vol keywords (kept only 4 of 25)
  2. Add 10 new Keyword-Planner-verified high-volume keywords
  3. Cap budget at ₹500/day → create separate campaign
  4. Update RSA: balance Wedding + Corporate + Group emphasis
  5. Final URL → /events (not /weddings)
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
from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
OLD_AG_ID = "196256288356"   # existing Group Bookings AG in main resort campaign
OLD_CAMP_ID = "21740834372"  # main resort campaign (Ecostay - Kanakapura)
TARGET_URL = "https://namooru.com/events/?utm_source=google&utm_medium=cpc&utm_campaign=resort_events"

# Keep (Keyword Planner ≥ 100/mo India)
VERIFIED_KW = [
    # Existing kept (4)
    ("wedding venue bangalore",         "EXACT", 3600),
    ("wedding resort bangalore",        "EXACT", 1300),
    ("destination wedding bangalore",   "EXACT", 590),
    ("birthday party resort bangalore", "EXACT", 140),
    # New high-volume (10)
    ("destination wedding venues",      "PHRASE", 2900),
    ("marriage hall bangalore",         "EXACT", 1900),
    ("banquet hall bangalore",          "EXACT", 1900),
    ("function hall bangalore",         "EXACT", 1000),
    ("engagement venue bangalore",      "EXACT", 480),
    ("outdoor wedding venue bangalore", "EXACT", 480),
    ("team outing bangalore",           "EXACT", 260),
    ("team outing places bangalore",    "EXACT", 260),
    ("team building activities bangalore","EXACT", 210),
    ("corporate day outing bangalore",  "EXACT", 210),
]

cfg = load_config()
cl = _get_google_ads_client(cfg)
state = {"timestamp": str(datetime.datetime.now()), "actions": []}


# ─── PHASE 1: PAUSE OLD AG (we're moving to a new campaign) ────────
print("="*78)
print("PHASE 1: Pause OLD Group Bookings AG (will replace with new campaign)")
print("="*78)
ag_svc = cl.get_service("AdGroupService")
op = cl.get_type("AdGroupOperation")
op.update.resource_name = f"customers/{CUSTOMER_ID}/adGroups/{OLD_AG_ID}"
op.update.status = cl.enums.AdGroupStatusEnum.PAUSED
op.update_mask.CopyFrom(FieldMask(paths=["status"]))
try:
    ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[op])
    print(f"  [OK] AG {OLD_AG_ID} paused")
    state["actions"].append({"action":"pause_old_ag","ag_id":OLD_AG_ID})
except Exception as e:
    print(f"  [FAIL] {str(e)[:200]}")


# ─── PHASE 2: CREATE NEW BUDGET ₹500/day ─────────────────────────
print("\n" + "="*78)
print("PHASE 2: Create new campaign budget ₹500/day")
print("="*78)
budget_svc = cl.get_service("CampaignBudgetService")
op = cl.get_type("CampaignBudgetOperation")
b = op.create
b.name = f"Group Bookings Events Rs500day {datetime.datetime.now().strftime('%Y%m%d-%H%M')}"
b.amount_micros = 500 * 1_000_000
b.delivery_method = cl.enums.BudgetDeliveryMethodEnum.STANDARD
b.explicitly_shared = False
try:
    r = budget_svc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[op])
    BUDGET_RN = r.results[0].resource_name
    print(f"  [OK] budget created: {BUDGET_RN}")
    state["actions"].append({"action":"create_budget","rn":BUDGET_RN,"amount":500})
except Exception as e:
    print(f"  [FAIL] {str(e)[:300]}")
    raise


# ─── PHASE 3: CREATE NEW CAMPAIGN ─────────────────────────────────
print("\n" + "="*78)
print("PHASE 3: Create campaign 'Resort - Group Bookings & Events'")
print("="*78)
camp_svc = cl.get_service("CampaignService")
op = cl.get_type("CampaignOperation")
c = op.create
c.name = "Resort - Group Bookings & Events"
c.advertising_channel_type = cl.enums.AdvertisingChannelTypeEnum.SEARCH
c.status = cl.enums.CampaignStatusEnum.ENABLED  # PAUSE first if you prefer
c.campaign_budget = BUDGET_RN
c.maximize_conversions.target_cpa_micros = 500 * 1_000_000  # target ₹500 CPA = lead value
c.network_settings.target_google_search = True
c.network_settings.target_search_network = True
c.network_settings.target_partner_search_network = False
c.network_settings.target_content_network = False
c.geo_target_type_setting.positive_geo_target_type = cl.enums.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST
c.geo_target_type_setting.negative_geo_target_type = cl.enums.NegativeGeoTargetTypeEnum.PRESENCE
c.contains_eu_political_advertising = cl.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
try:
    r = camp_svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
    NEW_CAMP_RN = r.results[0].resource_name
    NEW_CAMP_ID = NEW_CAMP_RN.split("/")[-1]
    print(f"  [OK] campaign: {NEW_CAMP_RN} (id={NEW_CAMP_ID})")
    state["actions"].append({"action":"create_campaign","rn":NEW_CAMP_RN,"id":NEW_CAMP_ID})
except Exception as e:
    print(f"  [FAIL] {str(e)[:600]}")
    raise


# ─── PHASE 3.5: GEO TARGET = INDIA (will refine later) ────────────
print("\n" + "="*78)
print("PHASE 3.5: Set geo target to India + Karnataka")
print("="*78)
crit_svc = cl.get_service("CampaignCriterionService")
ops = []
for geo_id in ["2356", "20174"]:  # India, Karnataka
    op = cl.get_type("CampaignCriterionOperation")
    cc = op.create
    cc.campaign = NEW_CAMP_RN
    cc.location.geo_target_constant = f"geoTargetConstants/{geo_id}"
    ops.append(op)
try:
    r = crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"  [OK] {len(r.results)} geo targets added")
except Exception as e:
    print(f"  [WARN] {str(e)[:300]}")


# ─── PHASE 4: CREATE AD GROUP ─────────────────────────────────────
print("\n" + "="*78)
print("PHASE 4: Create Ad Group + Keywords + RSA")
print("="*78)
op = cl.get_type("AdGroupOperation")
new = op.create
new.name = "Group Bookings & Events — Verified Keywords"
new.campaign = NEW_CAMP_RN
new.status = cl.enums.AdGroupStatusEnum.ENABLED
new.type_ = cl.enums.AdGroupTypeEnum.SEARCH_STANDARD
new.cpc_bid_micros = 30 * 1_000_000  # signal only (MAX_CONV ignores)
try:
    r = ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[op])
    NEW_AG_RN = r.results[0].resource_name
    NEW_AG_ID = NEW_AG_RN.split("/")[-1]
    print(f"  [OK] AG: {NEW_AG_RN} (id={NEW_AG_ID})")
    state["actions"].append({"action":"create_ag","rn":NEW_AG_RN,"id":NEW_AG_ID})
except Exception as e:
    print(f"  [FAIL] {str(e)[:600]}")
    raise


# ─── PHASE 4.5: ADD KEYWORDS ──────────────────────────────────────
agc_svc = cl.get_service("AdGroupCriterionService")
ops = []
for text, match, vol in VERIFIED_KW:
    op = cl.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = NEW_AG_RN
    c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
    c.keyword.text = text
    c.keyword.match_type = getattr(cl.enums.KeywordMatchTypeEnum, match)
    ops.append(op)
try:
    r = agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"  [OK] {len(r.results)} verified keywords added")
    for text, match, vol in VERIFIED_KW:
        print(f"    + [{match:<6}] {text:<40} ({vol}/mo)")
except Exception as e:
    print(f"  [WARN] batch failed, retrying one-by-one")
    for i, op in enumerate(ops):
        try:
            agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
        except Exception as e2:
            print(f"    [FAIL] '{VERIFIED_KW[i][0]}': {str(e2)[:120]}")


# ─── PHASE 5: NEGATIVES (block individual intent at AG level) ─────
NEG_AG = [
    ("couples",      "PHRASE"),
    ("honeymoon",    "PHRASE"),
    ("staycation",   "PHRASE"),
    ("day outing",   "PHRASE"),
    ("for couple",   "PHRASE"),
    ("for 2",        "PHRASE"),
    ("solo",         "PHRASE"),
    ("1 night stay", "PHRASE"),
]
print("\n" + "="*78)
print("PHASE 5: AG-level negatives (block individual intent)")
print("="*78)
for text, match in NEG_AG:
    op = cl.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = NEW_AG_RN
    c.negative = True
    c.keyword.text = text
    c.keyword.match_type = getattr(cl.enums.KeywordMatchTypeEnum, match)
    try:
        agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] NEG {text}")
    except Exception as e:
        print(f"  [FAIL] {text}: {str(e)[:120]}")


# ─── PHASE 6: CREATE RSA — balanced corporate/wedding/group ───────
print("\n" + "="*78)
print("PHASE 6: Create RSA (balanced for wedding + corporate + group)")
print("="*78)
ad_svc = cl.get_service("AdGroupAdService")
op = cl.get_type("AdGroupAdOperation")
ad = op.create
ad.ad_group = NEW_AG_RN
ad.status = cl.enums.AdGroupAdStatusEnum.ENABLED
rsa = ad.ad.responsive_search_ad

HEADLINES = [
    "Wedding Venue Bangalore",         # 23 — top kw
    "Banquet Hall Bangalore",          # 22 — top kw
    "Marriage Hall Bangalore",         # 23 — top kw
    "Destination Wedding Venue",       # 25
    "Corporate Offsite Venue",         # 23
    "Team Outing Resort Bangalore",    # 28
    "Group Bookings 50-300 Pax",       # 25
    "Function Hall Bangalore",         # 23
    "Team Building Activities",        # 24
    "Engagement & Reception Venue",    # 27
    "60 Km from Bangalore - Resort",   # 28
    "Free Site Visit Available",       # 24
    "GST Invoice for Corporates",      # 26
    "Custom Group Packages",           # 21
    "Book Direct - Best Rates",        # 24
]
DESCRIPTIONS = [
    "Premium 2-acre venue 60 km from BLR. Weddings, offsites, big events 50-300 pax.",  # 80
    "Banquet hall + open mandap + cottages. In-house catering, decor, AV - turnkey.",   # 78
    "Corporate offsites, team outings, big-day events. GST invoice. Free site visit.",  # 80
    "Wedding, reception, engagement, birthday, corporate. From Rs 1,999/head.",         # 73
]
for h in HEADLINES:
    rsa.headlines.add().text = h
for d in DESCRIPTIONS:
    rsa.descriptions.add().text = d
ad.ad.final_urls.append(TARGET_URL)
rsa.path1 = "events"
rsa.path2 = "bangalore"
try:
    r = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
    NEW_AD_ID = r.results[0].resource_name.split("/")[-1].split("~")[1]
    print(f"  [OK] RSA: AD {NEW_AD_ID}")
    state["actions"].append({"action":"create_rsa","ad_id":NEW_AD_ID})
except Exception as e:
    print(f"  [FAIL] {str(e)[:600]}")


# ─── PHASE 7: AG-LEVEL CALLOUTS ──────────────────────────────────
print("\n" + "="*78)
print("PHASE 7: AG-level callouts")
print("="*78)
a_svc = cl.get_service("AssetService")
aga_svc = cl.get_service("AdGroupAssetService")
CALLOUTS = [
    "100-300 Guest Capacity",
    "Wedding & Corporate Setup",
    "Banquet & Open Lawn",
    "In-House Catering",
    "GST Invoice for Corporates",
    "Free Site Visit",
    "Group Discount 10%+",
    "Team Building Activities",
]
for text in CALLOUTS:
    try:
        op = cl.get_type("AssetOperation")
        op.create.callout_asset.callout_text = text
        r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
        rn = r.results[0].resource_name
        op2 = cl.get_type("AdGroupAssetOperation")
        op2.create.ad_group = NEW_AG_RN
        op2.create.asset = rn
        op2.create.field_type = cl.enums.AssetFieldTypeEnum.CALLOUT
        aga_svc.mutate_ad_group_assets(customer_id=CUSTOMER_ID, operations=[op2])
        print(f"  [OK] '{text}'")
    except Exception as e:
        print(f"  [FAIL] '{text}': {str(e)[:120]}")


# ─── SAVE STATE ─────────────────────────────────────────────────
with open("/Users/girishkumar/Documents/ads/.group_bookings_v2_state.json","w") as f:
    json.dump(state, f, indent=2)

print("\n=== DONE ===")
print(f"  New campaign id : {NEW_CAMP_ID}")
print(f"  New AG id       : {NEW_AG_ID}")
print(f"  Budget          : ₹500/day")
print(f"  Target CPA      : ₹500 (lead form value)")
print(f"  Final URL       : {TARGET_URL}")
print(f"  14 verified keywords (all ≥ 140/mo Keyword Planner volume)")
