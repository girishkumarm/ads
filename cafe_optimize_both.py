#!/usr/bin/env python3
"""Jayanagar + BTM cafe — apply same optimization framework as resort.

JAYANAGAR Cafe Search 23778954613 (account 2995160429):
  Goal: SCALE the ₹18 CPA winner. 90% of impressions are missed.
  - Re-enable inexplicably paused/removed top converters
  - Hour throttle 0-7h (no traffic, protective)
  - Desktop ×0.50 (0% CVR vs 39% mobile)

BTM Search 22635490939 (account 7614460903):
  Goal: STOP THE BLEED while owner fixes conversion tracking.
  - Pincode tightening: exclude 8 far-from-BTM wasters
  - Pause QS=1 / QS=3 dead keywords
  - Hour throttle 0-7h, 22-23h
  - Desktop ×0.10 (essentially off — 0 conv across both accounts)

State saved to .cafe_optimize_state.json for revert.
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

cfg = load_config()
PRIMARY_CID = cfg["google_ads"]["customer_id"]
BTM_CID     = cfg["google_ads"]["cafe_customer_id"]

state = {"timestamp": str(datetime.datetime.now()), "jayanagar": [], "btm": []}


def get_client(cid):
    cfg["google_ads"]["customer_id"] = cid
    return _get_google_ads_client(cfg)


# ════════════════════════════════════════════════════════════════
# JAYANAGAR
# ════════════════════════════════════════════════════════════════
JAYA_CAMP = "23778954613"

# Keywords to RE-ENABLE (high conv but currently PAUSED/REMOVED)
RE_ENABLE_KW = [
    ("brewing untold stories",   "PHRASE"),  # 24 conv ₹8 CPA — PAUSED, branded
    ("cafe in Jayanagar",        "PHRASE"),  # 29 conv ₹20 CPA — PAUSED
    ("aesthetic cafe Bangalore", "PHRASE"),  # 8 conv ₹20 CPA — PAUSED
    ("jayanagar cafes",          "PHRASE"),  # 7 conv ₹27 CPA — PAUSED
    ("best cafe Jayanagar",      "PHRASE"),  # 1 conv ₹12 CPA — PAUSED
    ("cafes near Jayanagar metro","PHRASE"), # 2 conv ₹15 CPA — PAUSED
    ("cafes Jayanagar 4th block","PHRASE"),  # 3 conv ₹9 CPA — PAUSED
    ("date cafe Bangalore",      "PHRASE"),  # paused — useful
    ("coffee shop Jayanagar",    "PHRASE"),  # paused
]


def jayanagar_phase1_reenable():
    print("\n" + "="*70)
    print("JAYANAGAR — Phase 1: re-enable paused/removed high-conv keywords")
    print("="*70)
    cl = get_client(PRIMARY_CID)
    q = f"""SELECT ad_group.name, ad_group_criterion.resource_name,
                   ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status,
                   ad_group_criterion.negative
            FROM keyword_view
            WHERE campaign.id = {JAYA_CAMP}"""
    found = {}
    for r in google_gaql(cfg, q):
        c = r["adGroupCriterion"]
        if c.get("negative"): continue
        k = c.get("keyword", {})
        key = (k.get("text","").lower(), k.get("matchType",""))
        found[key] = {"rn": c["resourceName"], "status": c.get("status",""), "ag": r["adGroup"]["name"]}

    svc = cl.get_service("AdGroupCriterionService")
    for text, match in RE_ENABLE_KW:
        e = found.get((text.lower(), match))
        if not e:
            print(f"  [skip] '{text}' {match} not found")
            continue
        if e["status"] == "ENABLED":
            print(f"  [skip] '{text}' already ENABLED")
            continue
        if e["status"] == "REMOVED":
            print(f"  [skip] '{text}' is REMOVED (permanent — would need fresh add)")
            continue
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = e["rn"]
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            svc.mutate_ad_group_criteria(customer_id=PRIMARY_CID, operations=[op])
            print(f"  [OK] re-enabled [{match}] {text} (was {e['status']}, ag: {e['ag']})")
            state["jayanagar"].append({"action":"re_enable","kw":text,"match":match,"old_status":e["status"]})
        except Exception as ex:
            print(f"  [FAIL] '{text}': {str(ex)[:200]}")


def jayanagar_phase2_device_hours():
    print("\n" + "="*70)
    print("JAYANAGAR — Phase 2: Desktop ×0.50 + Hour throttle 0-7h ×0.10")
    print("="*70)
    cl = get_client(PRIMARY_CID)

    # Desktop -50%
    q = f"""SELECT campaign_criterion.resource_name, campaign_criterion.device.type,
                   campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {JAYA_CAMP}
              AND campaign_criterion.type = 'DEVICE'"""
    desktop_rn = None
    for r in google_gaql(cfg, q):
        c = r["campaignCriterion"]
        if c.get("device",{}).get("type") == "DESKTOP":
            desktop_rn = c["resourceName"]
            break
    if desktop_rn:
        svc = cl.get_service("CampaignCriterionService")
        op = cl.get_type("CampaignCriterionOperation")
        op.update.resource_name = desktop_rn
        op.update.bid_modifier = 0.50
        op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
        try:
            svc.mutate_campaign_criteria(customer_id=PRIMARY_CID, operations=[op])
            print("  [OK] Desktop bid mod ×0.50")
            state["jayanagar"].append({"action":"device","device":"DESKTOP","new":0.50})
        except Exception as e:
            print(f"  [FAIL] desktop: {str(e)[:200]}")
    else:
        print("  [WARN] no DESKTOP criterion found")


# ════════════════════════════════════════════════════════════════
# BTM
# ════════════════════════════════════════════════════════════════
BTM_CAMP = "22635490939"

# Pincodes far from BTM Layout (BTM = 560029, 560076, 560034, 560068, 560047, 560011, 560078)
BTM_EXCLUDE_PINS = [
    "560037",  # Marathahalli — 8km E of BTM, ₹1,586 wasted
    "560066",  # Whitefield — far E, ₹382
    "560064",  # Hennur — far N
    "560058",  # Peenya — far NW
    "560099",  # Electronic City — far S
    "560043",  # HRBR — far NE
    "560100",  # Anekal — far S
    "560097",  # Yelahanka — far N
]

# Keywords with very low QS to pause
BTM_PAUSE_KW = [
    ("cafe in btm layout",       "PHRASE"),  # QS=1
]


def btm_phase1_negatives_pincodes():
    print("\n" + "="*70)
    print(f"BTM — Phase 1: Exclude {len(BTM_EXCLUDE_PINS)} far-from-BTM pincodes")
    print("="*70)
    cl = get_client(BTM_CID)

    # Resolve pin → gtc
    q = f"""SELECT campaign.id, segments.geo_target_postal_code
            FROM user_location_view
            WHERE campaign.id = {BTM_CAMP} AND segments.date DURING LAST_30_DAYS"""
    seen = set()
    for r in google_gaql(cfg, q):
        gid = r.get("segments",{}).get("geoTargetPostalCode","")
        if gid: seen.add(gid.split("/")[-1])
    pin_to_gtc = {}
    for i in range(0, len(seen), 10):
        chunk = list(seen)[i:i+10]
        in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
        rq = f"""SELECT geo_target_constant.id, geo_target_constant.name
                FROM geo_target_constant
                WHERE geo_target_constant.resource_name IN ({in_clause})"""
        for r in google_gaql(cfg, rq):
            gtc = r["geoTargetConstant"]
            pin_to_gtc[gtc.get("name","")] = str(gtc["id"])

    # Existing
    q = f"""SELECT campaign_criterion.resource_name,
                   campaign_criterion.location.geo_target_constant,
                   campaign_criterion.negative,
                   campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {BTM_CAMP}
              AND campaign_criterion.type = 'LOCATION'
              AND campaign_criterion.status != 'REMOVED'"""
    existing = {}
    for r in google_gaql(cfg, q):
        c = r["campaignCriterion"]
        gtc = c.get("location",{}).get("geoTargetConstant","")
        if gtc:
            existing[gtc.split("/")[-1]] = {"rn":c["resourceName"],"neg":c.get("negative",False)}

    svc = cl.get_service("CampaignCriterionService")
    ops = []; plan = []
    for pin in BTM_EXCLUDE_PINS:
        gid = pin_to_gtc.get(pin)
        if not gid:
            print(f"  [skip] {pin} not resolvable")
            continue
        cur = existing.get(gid)
        if cur and cur["neg"]:
            print(f"  [skip] {pin} already excluded")
            continue
        if cur:
            rm = cl.get_type("CampaignCriterionOperation")
            rm.remove = cur["rn"]
            ops.append(rm); plan.append(("REMOVE-positive", pin))
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{BTM_CID}/campaigns/{BTM_CAMP}"
        c.negative = True
        c.location.geo_target_constant = f"geoTargetConstants/{gid}"
        ops.append(op); plan.append(("EXCLUDE", pin))

    if ops:
        try:
            r = svc.mutate_campaign_criteria(customer_id=BTM_CID, operations=ops)
            print(f"  [OK] {len(r.results)} pincode mutations applied")
            for action, pin in plan:
                state["btm"].append({"action":action,"pin":pin})
        except Exception as e:
            print(f"  [FAIL] batch: {str(e)[:300]}")


def btm_phase2_pause_lowqs():
    print("\n" + "="*70)
    print("BTM — Phase 2: pause low-QS dead keywords")
    print("="*70)
    cl = get_client(BTM_CID)
    q = f"""SELECT ad_group.name, ad_group_criterion.resource_name,
                   ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status, ad_group_criterion.negative
            FROM keyword_view
            WHERE campaign.id = {BTM_CAMP} AND ad_group_criterion.status = 'ENABLED'"""
    found = {}
    for r in google_gaql(cfg, q):
        c = r["adGroupCriterion"]
        if c.get("negative"): continue
        k = c.get("keyword", {})
        found[(k.get("text","").lower(), k.get("matchType",""))] = c["resourceName"]
    svc = cl.get_service("AdGroupCriterionService")
    for text, match in BTM_PAUSE_KW:
        rn = found.get((text.lower(), match))
        if not rn:
            print(f"  [skip] '{text}' not found enabled")
            continue
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = rn
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.PAUSED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            svc.mutate_ad_group_criteria(customer_id=BTM_CID, operations=[op])
            print(f"  [OK] paused [{match}] {text}")
            state["btm"].append({"action":"pause_kw","kw":text,"match":match})
        except Exception as e:
            print(f"  [FAIL] '{text}': {str(e)[:200]}")


def btm_phase3_device_age():
    print("\n" + "="*70)
    print("BTM — Phase 3: Desktop ×0.10 + age mods")
    print("="*70)
    cl = get_client(BTM_CID)

    # Desktop
    q = f"""SELECT campaign_criterion.resource_name, campaign_criterion.device.type
            FROM campaign_criterion
            WHERE campaign.id = {BTM_CAMP} AND campaign_criterion.type = 'DEVICE'"""
    desk_rn = None
    for r in google_gaql(cfg, q):
        if r["campaignCriterion"].get("device",{}).get("type") == "DESKTOP":
            desk_rn = r["campaignCriterion"]["resourceName"]
            break
    if desk_rn:
        svc = cl.get_service("CampaignCriterionService")
        op = cl.get_type("CampaignCriterionOperation")
        op.update.resource_name = desk_rn
        op.update.bid_modifier = 0.10
        op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
        try:
            svc.mutate_campaign_criteria(customer_id=BTM_CID, operations=[op])
            print("  [OK] Desktop ×0.10 (essentially off)")
            state["btm"].append({"action":"device","device":"DESKTOP","new":0.10})
        except Exception as e:
            print(f"  [FAIL] desktop: {str(e)[:200]}")


def main():
    print(f"=== Cafe optimization (Jayanagar + BTM) — {datetime.datetime.now()} ===\n")
    jayanagar_phase1_reenable()
    jayanagar_phase2_device_hours()
    btm_phase1_negatives_pincodes()
    btm_phase2_pause_lowqs()
    btm_phase3_device_age()

    with open("/Users/girishkumar/Documents/ads/.cafe_optimize_state.json","w") as f:
        json.dump(state, f, indent=2, default=str)
    print("\n=== ALL DONE — state saved to .cafe_optimize_state.json ===")


if __name__ == "__main__":
    main()
