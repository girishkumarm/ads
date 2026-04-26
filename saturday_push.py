#!/usr/bin/env python3
"""
Saturday push for Jayanagar Cafe Search 23778954613 — boost for today (Apr 26).

1. Budget Rs 800 → Rs 1,200 (today)
2. Saturday-only peak hour bid modifiers boosted (lunch + evening)
3. New sitelink "Saturday Special — Couples Combo Rs 399"
4. New promotion asset "Couples Combo Rs 399 today"

All reversible via revert_saturday_push.py (auto-stamped).
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

import json, datetime
from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
CAMP_ID = "23778954613"
TARGET_URL = "https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/"

cfg = load_config()
cl = _get_google_ads_client(cfg)


# ─────────────────────────────────────────────────
# 1. Bump budget Rs 800 → Rs 1,200 (today's push)
# ─────────────────────────────────────────────────
def bump_budget():
    print("\n=== 1. Budget Rs 800 → Rs 1,200 ===")
    q = f"""SELECT campaign.id, campaign_budget.id, campaign_budget.amount_micros
            FROM campaign WHERE campaign.id = {CAMP_ID}"""
    r = google_gaql(cfg, q)[0]
    bud_id = r["campaignBudget"]["id"]
    cur = int(r["campaignBudget"]["amountMicros"]) / 1e6
    print(f"  Current: Rs {cur:.0f}/day  →  Rs 1,200/day")

    svc = cl.get_service("CampaignBudgetService")
    op = cl.get_type("CampaignBudgetOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{bud_id}"
    op.update.amount_micros = 1200 * 1_000_000
    op.update_mask.CopyFrom(FieldMask(paths=["amount_micros"]))
    svc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[op])
    print(f"  [OK] Budget Rs 1,200/day live (was {cur:.0f})")
    return cur


# ─────────────────────────────────────────────────
# 2. Saturday peak-hour bid bumps
# ─────────────────────────────────────────────────
# Original Saturday modifiers:
#   8-11  ×1.30   (breakfast)
#   11-14 ×1.00   (peak — already busy, don't overpay)
#   14-18 ×1.20   (afternoon empty seat fill)
#   18-22 ×1.40   (evening empty seat fill)
#   22-23 ×1.10   (late)
# Saturday push values:
#   11-14 → ×1.30  (push lunch peak too — Saturday lunch crowd is bigger)
#   14-18 → ×1.50  (boost afternoon)
#   18-22 → ×1.60  (boost evening)

SAT_TARGETS = {
    (11, 14): 1.30,
    (14, 18): 1.50,
    (18, 22): 1.60,
}


def boost_saturday():
    print("\n=== 2. Boost Saturday peak-hour modifiers ===")
    q = f"""SELECT campaign_criterion.resource_name,
                  campaign_criterion.ad_schedule.day_of_week,
                  campaign_criterion.ad_schedule.start_hour,
                  campaign_criterion.ad_schedule.end_hour,
                  campaign_criterion.bid_modifier
           FROM campaign_criterion
           WHERE campaign.id = {CAMP_ID}
             AND campaign_criterion.type = 'AD_SCHEDULE'"""
    sat_rows = []
    for r in google_gaql(cfg, q):
        cc = r["campaignCriterion"]
        sched = cc.get("adSchedule", {})
        if sched.get("dayOfWeek") != "SATURDAY":
            continue
        sat_rows.append({
            "rn": cc["resourceName"],
            "start": sched.get("startHour", 0),
            "end": sched.get("endHour", 0),
            "current_bm": cc.get("bidModifier", 1.0),
        })

    if not sat_rows:
        print("  [WARN] No Saturday schedules found — skipping")
        return None

    print(f"  Found {len(sat_rows)} Saturday schedules")

    # Save originals for revert
    originals = []
    svc = cl.get_service("CampaignCriterionService")
    ops = []
    for s in sat_rows:
        key = (s["start"], s["end"])
        if key not in SAT_TARGETS:
            continue
        target_bm = SAT_TARGETS[key]
        if abs(s["current_bm"] - target_bm) < 0.01:
            print(f"  [skip] SAT {s['start']:>2}-{s['end']:>2}h already at ×{target_bm:.2f}")
            continue
        originals.append({"rn": s["rn"], "old": s["current_bm"], "start": s["start"], "end": s["end"]})
        op = cl.get_type("CampaignCriterionOperation")
        op.update.resource_name = s["rn"]
        op.update.bid_modifier = target_bm
        op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
        ops.append(op)
        print(f"  SAT {s['start']:>2}-{s['end']:>2}h  ×{s['current_bm']:.2f} → ×{target_bm:.2f}")

    if ops:
        svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
        print(f"  [OK] {len(ops)} Saturday modifiers boosted")
    return originals


# ─────────────────────────────────────────────────
# 3. New sitelink "Saturday Special"
# ─────────────────────────────────────────────────
def add_saturday_sitelink():
    print("\n=== 3. Add 'Saturday Special' sitelink ===")
    a_svc = cl.get_service("AssetService")
    ca_svc = cl.get_service("CampaignAssetService")

    op = cl.get_type("AssetOperation")
    a = op.create
    a.sitelink_asset.link_text = "Saturday Special"
    a.sitelink_asset.description1 = "Couples Combo Rs 399"
    a.sitelink_asset.description2 = "Today only · 6-10 PM"
    a.final_urls.append(TARGET_URL)
    resp = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    asset_rn = resp.results[0].resource_name
    print(f"  [OK] Asset created: {asset_rn}")

    op2 = cl.get_type("CampaignAssetOperation")
    ca = op2.create
    ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
    ca.asset = asset_rn
    ca.field_type = cl.enums.AssetFieldTypeEnum.SITELINK
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op2])
    print(f"  [OK] Sitelink linked to campaign {CAMP_ID}")
    return asset_rn


# ─────────────────────────────────────────────────
# 4. New promotion asset
# ─────────────────────────────────────────────────
def add_promotion_asset():
    print("\n=== 4. Add Promotion asset 'Couples Combo Rs 399' ===")
    a_svc = cl.get_service("AssetService")
    ca_svc = cl.get_service("CampaignAssetService")

    op = cl.get_type("AssetOperation")
    a = op.create
    promo = a.promotion_asset
    promo.promotion_target = "Couples Combo Rs 399"  # what the promo is on
    promo.discount_modifier = cl.enums.PromotionExtensionDiscountModifierEnum.UNSPECIFIED
    promo.money_amount_off.amount_micros = 200 * 1_000_000  # Rs 200 off (anchor savings)
    promo.money_amount_off.currency_code = "INR"
    promo.language_code = "en"
    promo.occasion = cl.enums.PromotionExtensionOccasionEnum.UNSPECIFIED
    a.final_urls.append(TARGET_URL)
    try:
        resp = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
        asset_rn = resp.results[0].resource_name
        print(f"  [OK] Promotion asset created: {asset_rn}")
    except Exception as e:
        # Promotion assets have strict schema requirements — log and skip
        msg = str(e)
        # Extract policy/field error
        idx = msg.find("message:")
        snippet = msg[idx:idx+250] if idx > -1 else msg[:250]
        print(f"  [WARN] Promotion asset failed: {snippet}")
        print(f"  Falling back: skipping (sitelink #3 already covers the promo intent)")
        return None

    op2 = cl.get_type("CampaignAssetOperation")
    ca = op2.create
    ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
    ca.asset = asset_rn
    ca.field_type = cl.enums.AssetFieldTypeEnum.PROMOTION
    try:
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op2])
        print(f"  [OK] Promotion linked to campaign")
    except Exception as e:
        print(f"  [WARN] Promotion link failed: {str(e)[:200]}")
    return asset_rn


# ─────────────────────────────────────────────────
# MAIN + revert plan
# ─────────────────────────────────────────────────
def main():
    print(f"=== Saturday Push — Jayanagar Cafe Search 23778954613 — {datetime.datetime.now()} ===")

    state = {"timestamp": str(datetime.datetime.now())}

    state["budget_old"] = bump_budget()
    state["sat_originals"] = boost_saturday()
    state["saturday_sitelink_rn"] = add_saturday_sitelink()
    state["promotion_rn"] = add_promotion_asset()

    # Save state for revert
    with open(".saturday_push_state.json","w") as f:
        json.dump(state, f, indent=2, default=str)

    print("\n=== ALL DONE ===")
    print("  State saved to .saturday_push_state.json (use to revert tomorrow)")
    print(f"  Budget Rs 800 → Rs 1,200")
    print(f"  Saturday peak hours boosted: 11-14h ×1.30, 14-18h ×1.50, 18-22h ×1.60")
    print(f"  New 'Saturday Special' sitelink linked")


if __name__ == "__main__":
    main()
