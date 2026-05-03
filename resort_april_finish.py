#!/usr/bin/env python3
"""Finish Phase D (Fri/Sat 8-9h throttle) + Phase E (age mods).
Phase A (12 negatives), B (1 pause), C (Desktop ×0.75) already done."""
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

cfg = load_config()
cl = _get_google_ads_client(cfg)


# ─── PHASE D: FRI/SAT 8-9h ×0.60 ─────────────────
def phase_d():
    print("\n" + "="*75)
    print("PHASE D: ADD FRI/SAT 8-9h ×0.60 MORNING THROTTLE")
    print("="*75)
    q = f"""SELECT campaign_criterion.resource_name,
                   campaign_criterion.ad_schedule.day_of_week,
                   campaign_criterion.ad_schedule.start_hour,
                   campaign_criterion.ad_schedule.end_hour,
                   campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.type = 'AD_SCHEDULE'"""
    existing = []
    for r in google_gaql(cfg, q):
        s = r["campaignCriterion"].get("adSchedule", {})
        existing.append({
            "rn": r["campaignCriterion"]["resourceName"],
            "day": s.get("dayOfWeek",""),
            "start": s.get("startHour", 0),
            "end": s.get("endHour", 0),
            "bm": r["campaignCriterion"].get("bidModifier", 1.0),
        })

    svc = cl.get_service("CampaignCriterionService")
    plan_ops = []
    plan_log = []

    for day in ["FRIDAY", "SATURDAY"]:
        target = next((s for s in existing if s["day"] == day and s["start"] == 8 and s["end"] == 22 and abs(s["bm"]-1.0)<0.01), None)
        if not target:
            print(f"  [skip] {day} 8-22h ×1.00 not found")
            continue
        rm = cl.get_type("CampaignCriterionOperation")
        rm.remove = target["rn"]
        plan_ops.append(rm)
        plan_log.append(f"REMOVE {day} 8-22h ×1.00")

        ad1 = cl.get_type("CampaignCriterionOperation")
        c1 = ad1.create
        c1.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c1.bid_modifier = 0.60
        c1.ad_schedule.day_of_week = getattr(cl.enums.DayOfWeekEnum, day)
        c1.ad_schedule.start_hour = 8
        c1.ad_schedule.end_hour = 9
        c1.ad_schedule.start_minute = cl.enums.MinuteOfHourEnum.ZERO
        c1.ad_schedule.end_minute = cl.enums.MinuteOfHourEnum.ZERO
        plan_ops.append(ad1)
        plan_log.append(f"ADD {day} 8-9h ×0.60")

        ad2 = cl.get_type("CampaignCriterionOperation")
        c2 = ad2.create
        c2.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c2.bid_modifier = 1.00
        c2.ad_schedule.day_of_week = getattr(cl.enums.DayOfWeekEnum, day)
        c2.ad_schedule.start_hour = 9
        c2.ad_schedule.end_hour = 22
        c2.ad_schedule.start_minute = cl.enums.MinuteOfHourEnum.ZERO
        c2.ad_schedule.end_minute = cl.enums.MinuteOfHourEnum.ZERO
        plan_ops.append(ad2)
        plan_log.append(f"ADD {day} 9-22h ×1.00")

    print(f"\n  Plan ({len(plan_ops)} ops):")
    for log in plan_log:
        print(f"    {log}")
    if not plan_ops:
        return
    try:
        svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=plan_ops)
        print(f"  [OK] schedule updated")
    except Exception as e:
        print(f"  [FAIL] schedule: {str(e)[:300]}")


# ─── PHASE E: AGE BID MODS ────────────────────────────────
AGE_TARGETS = {
    "AGE_RANGE_35_44": 1.15,
    "AGE_RANGE_45_54": 1.10,
    "AGE_RANGE_55_64": 1.20,
}

def phase_e():
    print("\n" + "="*75)
    print("PHASE E: AGE BID MODS")
    print("="*75)
    q = f"""SELECT ad_group.id, ad_group.name,
                   ad_group_criterion.resource_name,
                   ad_group_criterion.age_range.type,
                   ad_group_criterion.bid_modifier,
                   ad_group_criterion.status
            FROM age_range_view
            WHERE campaign.id = {CAMP_ID}
              AND ad_group_criterion.status = 'ENABLED'"""
    rows = []
    for r in google_gaql(cfg, q):
        c = r["adGroupCriterion"]
        rows.append({
            "rn": c["resourceName"],
            "age": c["ageRange"]["type"],
            "bm": c.get("bidModifier", 1.0),
            "ag": r["adGroup"]["name"],
        })
    svc = cl.get_service("AdGroupCriterionService")
    ok_count = 0
    for age, target_bm in AGE_TARGETS.items():
        for r in rows:
            if r["age"] != age: continue
            if abs(r["bm"] - target_bm) < 0.001:
                print(f"  [skip] {age} in '{r['ag']}' already ×{target_bm:.2f}")
                continue
            op = cl.get_type("AdGroupCriterionOperation")
            op.update.resource_name = r["rn"]
            op.update.bid_modifier = target_bm
            op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
            try:
                svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
                ok_count += 1
                print(f"  [OK] {age:<20} '{r['ag'][:25]}'  ×{r['bm']:.2f} → ×{target_bm:.2f}")
            except Exception as e:
                print(f"  [FAIL] {age} in '{r['ag']}': {str(e)[:150]}")
    print(f"\n  [OK] {ok_count} age mods updated")


phase_d()
phase_e()
print("\n=== Phase D+E complete ===")
