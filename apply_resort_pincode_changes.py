#!/usr/bin/env python3
"""
Resort campaign 21740834372 — pincode optimization based on 30-day user_location_view.

Per user approval 2026-04-26:
  1. EXCLUDE 14 pure-waste pincodes (≥5 clicks, 0 prim, 0 all conv in 30d)
  2. BID -50% on 5 zero-primary pincodes (engaged but no directions)
  3. BID -30% on 1 high-CPA pincode (560004 Basavangudi, Rs 1,550 CPA vs Rs 248 avg)
  4. BID +30% on 5 top performers (lowest CPA, highest volume)

Bid modifiers require the pincode to be added as a POSITIVE targeted location.
Exclusions use negative campaign_criterion with location.geo_target_constant.
"""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""

from ads_api import load_config, _get_google_ads_client, google_gaql

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"

# 14 pure-waste pincodes — EXCLUDE
EXCLUDE_PINS = [
    "560114", "560010", "560036", "560062", "560056",
    "560027", "560023", "560005", "560094", "560059",
    "560075", "560084", "560082", "560033",
]

# 5 zero-primary pincodes — bid -50%
BID_DOWN_50_PINS = ["560073", "560006", "560110", "560054", "560057"]

# 1 high-CPA pincode — bid -30%
BID_DOWN_30_PINS = ["560004"]

# 5 top performers — bid +30%
BID_UP_30_PINS = ["560040", "560100", "560058", "560078", "560076"]

cfg = load_config()
cl = _get_google_ads_client(cfg)


def lookup_geo_constants(pincodes):
    """Resolve pincode strings → geoTargetConstant IDs via user_location_view 30d data
    (which already maps the physical pin user IDs we observed)."""
    q = f"""SELECT campaign.id, segments.geo_target_postal_code
            FROM user_location_view
            WHERE campaign.id = {CAMP_ID} AND segments.date DURING LAST_30_DAYS"""
    seen_ids = set()
    for r in google_gaql(cfg, q):
        gid_full = r.get("segments",{}).get("geoTargetPostalCode","")
        if gid_full:
            seen_ids.add(gid_full.split("/")[-1])

    # Now fetch geo_target_constant for those IDs to get the pincode names
    pin_to_gtc = {}
    ids_list = list(seen_ids)
    for i in range(0, len(ids_list), 10):
        chunk = ids_list[i:i+10]
        in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
        rq = f"""SELECT geo_target_constant.id, geo_target_constant.name
                FROM geo_target_constant
                WHERE geo_target_constant.resource_name IN ({in_clause})"""
        for r in google_gaql(cfg, rq):
            gtc = r["geoTargetConstant"]
            pin_to_gtc[gtc.get("name","")] = str(gtc["id"])

    # Match requested pincodes
    resolved = {}
    for p in pincodes:
        if p in pin_to_gtc:
            resolved[p] = pin_to_gtc[p]
        else:
            print(f"  [WARN] No GTC found for pincode {p} — will skip")
    return resolved


def get_existing_location_criteria():
    """Return dict of geo_target_constant_id → criterion_resource_name for resort campaign."""
    q = f"""SELECT campaign_criterion.resource_name,
                   campaign_criterion.location.geo_target_constant,
                   campaign_criterion.negative,
                   campaign_criterion.bid_modifier,
                   campaign_criterion.status
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.type = 'LOCATION'
              AND campaign_criterion.status != 'REMOVED'"""
    existing = {}
    for r in google_gaql(cfg, q):
        cc = r["campaignCriterion"]
        gtc = cc.get("location",{}).get("geoTargetConstant","")
        if gtc:
            gid = gtc.split("/")[-1]
            existing[gid] = {
                "rn": cc["resourceName"],
                "negative": cc.get("negative", False),
                "bid_modifier": cc.get("bidModifier", 1.0),
            }
    return existing


def apply_changes():
    svc = cl.get_service("CampaignCriterionService")

    all_pins = EXCLUDE_PINS + BID_DOWN_50_PINS + BID_DOWN_30_PINS + BID_UP_30_PINS
    print(f"=== Resolving {len(all_pins)} pincode → geoTargetConstant IDs ===")
    pin_to_gtc = lookup_geo_constants(all_pins)
    print(f"  Resolved {len(pin_to_gtc)} of {len(all_pins)}")

    print(f"\n=== Pulling existing location criteria on resort campaign ===")
    existing = get_existing_location_criteria()
    print(f"  {len(existing)} existing location criteria")

    ops = []
    plan = []  # (action, pin, gid)

    # 1. Exclusions
    for pin in EXCLUDE_PINS:
        gid = pin_to_gtc.get(pin)
        if not gid:
            continue
        if gid in existing and existing[gid]["negative"]:
            print(f"  [skip] {pin} already excluded")
            continue
        if gid in existing:
            # exists as positive — must remove first then add as negative
            print(f"  [warn] {pin} exists as positive target (bid_mod={existing[gid]['bid_modifier']}) — removing first")
            rm = cl.get_type("CampaignCriterionOperation")
            rm.remove = existing[gid]["rn"]
            ops.append(rm)
            plan.append(("REMOVE-existing", pin, gid))
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c.negative = True
        c.location.geo_target_constant = f"geoTargetConstants/{gid}"
        ops.append(op)
        plan.append(("EXCLUDE", pin, gid))

    # 2-4. Bid modifier targets
    bid_changes = (
        [(p, 0.5, "−50%") for p in BID_DOWN_50_PINS] +
        [(p, 0.7, "−30%") for p in BID_DOWN_30_PINS] +
        [(p, 1.3, "+30%") for p in BID_UP_30_PINS]
    )
    for pin, mod, label in bid_changes:
        gid = pin_to_gtc.get(pin)
        if not gid:
            continue
        if gid in existing:
            cur = existing[gid]
            if cur["negative"]:
                print(f"  [skip] {pin} is already excluded — won't add bid modifier")
                continue
            if abs(cur["bid_modifier"] - mod) < 0.001:
                print(f"  [skip] {pin} already at bid_modifier={mod}")
                continue
            # update existing
            from google.protobuf.field_mask_pb2 import FieldMask
            op = cl.get_type("CampaignCriterionOperation")
            up = op.update
            up.resource_name = cur["rn"]
            up.bid_modifier = mod
            op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
            ops.append(op)
            plan.append((f"UPDATE bid_mod {label}", pin, gid))
            continue
        # create as new positive target with bid modifier
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c.location.geo_target_constant = f"geoTargetConstants/{gid}"
        c.bid_modifier = mod
        ops.append(op)
        plan.append((f"ADD bid_mod {label}", pin, gid))

    print(f"\n=== Plan: {len(plan)} mutations ===")
    for action, pin, gid in plan:
        print(f"  {action:<28} pin={pin}  gtc={gid}")

    if not ops:
        print("\n[--] Nothing to do")
        return

    # Execute
    try:
        resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
        print(f"\n[OK] {len(resp.results)} mutations applied")
    except Exception as e:
        print(f"\n[ERR] mutate failed:\n{str(e)[:1500]}")


if __name__ == "__main__":
    apply_changes()
