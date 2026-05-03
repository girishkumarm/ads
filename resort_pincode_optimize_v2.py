#!/usr/bin/env python3
"""Resort campaign — pincode optimization v2 (approved 2026-05-03 by Girish).

Tier 1 — EXCLUDE 3 zero-conv pincodes that didn't respond to BM ×0.50:
  560006, 560110, 560057

Tier 2 — BID DOWN 7 high-CPA / far pincodes:
  560004 (Basavanagudi) ×0.70 → ×0.40
  560068 (Bommanahalli)  add → ×0.65
  560091 (N.Bangalore)   add → ×0.65
  560043 (HRBR/NE)       add → ×0.70
  560103 (Whitefield ext) add → ×0.70
  560008 (Cantonment NE) add → ×0.75
  560022 (Vidyaranyapura) add → ×0.75

Tier 3 — BID UP 3 strong unboosted converters:
  560007 (Frazer Town)   add → ×1.40
  560061 (Rajajinagar)   add → ×1.30
  560048 (Banashankari)  add → ×1.20

State saved to .resort_pincode_v2_state.json for revert.
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
CAMP_ID = "21740834372"

EXCLUDE_PINS = ["560006", "560110", "560057"]

BID_CHANGES = [
    # (pincode, new_bm)
    ("560004", 0.40),
    ("560068", 0.65),
    ("560091", 0.65),
    ("560043", 0.70),
    ("560103", 0.70),
    ("560008", 0.75),
    ("560022", 0.75),
    ("560007", 1.40),
    ("560061", 1.30),
    ("560048", 1.20),
]

cfg = load_config()
cl = _get_google_ads_client(cfg)
state = {"timestamp": str(datetime.datetime.now()), "actions": []}


def lookup_geo_constants(pincodes):
    """Resolve pincode strings → geoTargetConstant IDs using user_location_view.
    Falls back to wider search if not found."""
    q = f"""SELECT campaign.id, segments.geo_target_postal_code
            FROM user_location_view
            WHERE campaign.id = {CAMP_ID} AND segments.date DURING LAST_30_DAYS"""
    seen = set()
    for r in google_gaql(cfg, q):
        gid = r.get("segments",{}).get("geoTargetPostalCode","")
        if gid:
            seen.add(gid.split("/")[-1])

    pin_to_gtc = {}
    ids_list = list(seen)
    for i in range(0, len(ids_list), 10):
        chunk = ids_list[i:i+10]
        in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
        rq = f"""SELECT geo_target_constant.id, geo_target_constant.name
                FROM geo_target_constant
                WHERE geo_target_constant.resource_name IN ({in_clause})"""
        for r in google_gaql(cfg, rq):
            gtc = r["geoTargetConstant"]
            pin_to_gtc[gtc.get("name","")] = str(gtc["id"])
    return pin_to_gtc


def get_existing_loc_criteria():
    q = f"""SELECT campaign_criterion.resource_name,
                   campaign_criterion.location.geo_target_constant,
                   campaign_criterion.negative,
                   campaign_criterion.bid_modifier,
                   campaign_criterion.status
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.type = 'LOCATION'
              AND campaign_criterion.status != 'REMOVED'"""
    out = {}
    for r in google_gaql(cfg, q):
        c = r["campaignCriterion"]
        gtc = c.get("location",{}).get("geoTargetConstant","")
        if not gtc: continue
        gid = gtc.split("/")[-1]
        out[gid] = {
            "rn": c["resourceName"],
            "negative": c.get("negative", False),
            "bm": c.get("bidModifier", 1.0),
        }
    return out


def main():
    print(f"=== Resort pincode optimize v2 — {datetime.datetime.now()} ===\n")

    # 1) Resolve all pincodes
    all_pins = list(set(EXCLUDE_PINS + [p for p,_ in BID_CHANGES]))
    print(f"Resolving {len(all_pins)} pincodes → geoTargetConstant IDs...")
    pin_to_gtc = lookup_geo_constants(all_pins)
    missing = [p for p in all_pins if p not in pin_to_gtc]
    if missing:
        print(f"  [WARN] not found in last 30d data: {missing}")
    print(f"  Resolved: {len(pin_to_gtc)}/{len(all_pins)}\n")

    # 2) Pull existing criteria
    existing = get_existing_loc_criteria()
    print(f"Existing location criteria: {len(existing)}\n")

    svc = cl.get_service("CampaignCriterionService")
    ops = []
    plan = []  # (action, pin, gid, old_bm)

    # ─── Tier 1: EXCLUDE ─────────────────────────────────
    print("="*70)
    print("TIER 1: EXCLUDE 3 pincodes")
    print("="*70)
    for pin in EXCLUDE_PINS:
        gid = pin_to_gtc.get(pin)
        if not gid:
            print(f"  [skip] {pin} not resolvable")
            continue
        cur = existing.get(gid)
        if cur and cur["negative"]:
            print(f"  [skip] {pin} already excluded")
            continue
        if cur:
            # Exists as positive — must remove first
            print(f"  REMOVE existing positive {pin} (was bm ×{cur['bm']:.2f})")
            rm = cl.get_type("CampaignCriterionOperation")
            rm.remove = cur["rn"]
            ops.append(rm)
            plan.append(("REMOVE-positive", pin, gid, cur["bm"]))
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c.negative = True
        c.location.geo_target_constant = f"geoTargetConstants/{gid}"
        ops.append(op)
        plan.append(("EXCLUDE", pin, gid, None))
        print(f"  EXCLUDE {pin}")

    # ─── Tier 2 + 3: BID CHANGES ────────────────────────
    print("\n" + "="*70)
    print("TIER 2+3: BID MODIFIER CHANGES (10 pincodes)")
    print("="*70)
    for pin, target_bm in BID_CHANGES:
        gid = pin_to_gtc.get(pin)
        if not gid:
            print(f"  [skip] {pin} not resolvable")
            continue
        cur = existing.get(gid)
        if cur and cur["negative"]:
            print(f"  [skip] {pin} is already excluded — won't add bid mod")
            continue
        if cur:
            if abs(cur["bm"] - target_bm) < 0.001:
                print(f"  [skip] {pin} already at ×{target_bm:.2f}")
                continue
            op = cl.get_type("CampaignCriterionOperation")
            up = op.update
            up.resource_name = cur["rn"]
            up.bid_modifier = target_bm
            op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
            ops.append(op)
            label = "+" if target_bm > 1 else "-"
            pct = abs(int((target_bm-1.0)*100))
            print(f"  UPDATE {pin}  ×{cur['bm']:.2f} → ×{target_bm:.2f}  ({label}{pct}%)")
            plan.append((f"UPDATE-bm", pin, gid, cur["bm"]))
        else:
            op = cl.get_type("CampaignCriterionOperation")
            c = op.create
            c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
            c.location.geo_target_constant = f"geoTargetConstants/{gid}"
            c.bid_modifier = target_bm
            ops.append(op)
            label = "+" if target_bm > 1 else "-"
            pct = abs(int((target_bm-1.0)*100))
            print(f"  ADD    {pin}  → ×{target_bm:.2f}  ({label}{pct}%)")
            plan.append(("ADD-positive", pin, gid, None))

    if not ops:
        print("\n[--] Nothing to do.")
        return

    print(f"\n=== Executing {len(ops)} mutations ===")
    try:
        resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
        print(f"[OK] {len(resp.results)} mutations applied")
        # Save state
        for i, r in enumerate(resp.results):
            state["actions"].append({
                "action": plan[i][0], "pin": plan[i][1], "gid": plan[i][2],
                "old_bm": plan[i][3], "new_rn": r.resource_name,
            })
    except Exception as e:
        print(f"[ERR] batch failed: {str(e)[:500]}")
        # one-by-one fallback
        ok = 0
        for i, op in enumerate(ops):
            try:
                r = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[op])
                ok += 1
                state["actions"].append({
                    "action": plan[i][0], "pin": plan[i][1], "gid": plan[i][2],
                    "old_bm": plan[i][3], "new_rn": r.results[0].resource_name,
                })
            except Exception as e2:
                print(f"  [skip] {plan[i][1]}: {str(e2)[:150]}")
        print(f"\n[OK] {ok}/{len(ops)} mutations applied")

    # save state
    with open("/Users/girishkumar/Documents/ads/.resort_pincode_v2_state.json", "w") as f:
        json.dump(state, f, indent=2, default=str)
    print(f"\n[OK] state saved to .resort_pincode_v2_state.json")


if __name__ == "__main__":
    main()
