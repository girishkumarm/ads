#!/usr/bin/env python3
"""Resort campaign 21740834372 — April 2026 optimization (approved 2026-05-03).

Phase A: 12 strategic negatives (8 competitor brand PHRASE + 4 wrong-geo EXACT)
Phase B: Pause 7 wasteful keywords (high CPA / 0 conv / dup)
Phase C: Device bid mod Desktop ×0.75
Phase D: Add Fri/Sat 8-9h ×0.60 throttle (matching Mon-Thu/Sun)
Phase E: Age mods (+15% 35-44, +10% 45-54, +20% 55-64)

Skipped (would not help under MAX_CONVERSIONS bidding):
  - Keyword-level bid changes (auto-bidding ignores them)
  - Full hour-level schedule rewrite (algorithm auto-tunes hours under target CPA)

State saved to .resort_april_state.json for revert.
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

cfg = load_config()
cl = _get_google_ads_client(cfg)
state = {"timestamp": str(datetime.datetime.now()), "phases": {}}


# ─── PHASE A: NEGATIVES ─────────────────────────────────
NEG_PHRASE = [   # block any search containing these competitor brand fragments
    "areca home stay",
    "the dome retreats",
    "vistar resorts",
    "nestinn",
    "amore collective",
    "club mahindra",
    "white mist by nava",
    "rainbow retreat",
]
NEG_EXACT = [    # block these exact non-target geo / generic queries
    "resort electronic city",
    "resorts near electronic city",
    "resort in nandi hills bangalore",
    "near by resort bangalore",
]


def phase_a_negatives():
    print("\n" + "="*75)
    print("PHASE A: ADD 12 STRATEGIC NEGATIVES")
    print("="*75)

    # check existing negatives so we don't duplicate
    q = f"""SELECT campaign_criterion.keyword.text,
                   campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.negative = TRUE
              AND campaign_criterion.type = 'KEYWORD'"""
    existing = set()
    for r in google_gaql(cfg, q):
        k = r["campaignCriterion"]["keyword"]
        existing.add((k["text"].lower(), k["matchType"]))

    svc = cl.get_service("CampaignCriterionService")
    ops = []
    plan = []

    for t in NEG_PHRASE:
        if (t.lower(), "PHRASE") in existing:
            print(f"  [skip] PHRASE neg '{t}' already exists")
            continue
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c.negative = True
        c.keyword.text = t
        c.keyword.match_type = cl.enums.KeywordMatchTypeEnum.PHRASE
        ops.append(op)
        plan.append(("PHRASE", t))

    for t in NEG_EXACT:
        if (t.lower(), "EXACT") in existing:
            print(f"  [skip] EXACT neg '{t}' already exists")
            continue
        op = cl.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
        c.negative = True
        c.keyword.text = t
        c.keyword.match_type = cl.enums.KeywordMatchTypeEnum.EXACT
        ops.append(op)
        plan.append(("EXACT", t))

    print(f"\n  Adding {len(ops)} new negatives:")
    for m, t in plan:
        print(f"    NEG [{m:<6}] {t}")

    if not ops:
        return []

    added = []
    try:
        resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
        for i, r in enumerate(resp.results):
            added.append({"rn": r.resource_name, "match": plan[i][0], "text": plan[i][1]})
        print(f"\n  [OK] {len(added)} negatives added")
    except Exception as e:
        print(f"\n  [WARN] batch failed, going one-by-one: {str(e)[:200]}")
        for i, op in enumerate(ops):
            try:
                r = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[op])
                added.append({"rn": r.results[0].resource_name, "match": plan[i][0], "text": plan[i][1]})
            except Exception as e2:
                print(f"    [skip] '{plan[i][1]}': {str(e2)[:120]}")
        print(f"\n  [OK] {len(added)}/{len(ops)} negatives added (one-by-one)")
    return added


# ─── PHASE B: PAUSE WASTEFUL KEYWORDS ────────────────────
PAUSE_KW = [
    ("bangalore getaway resorts",         "PHRASE"),  # ₹920 CPA
    ("weekend getaway bangalore",         "PHRASE"),  # ₹728 CPA, replaced by EXACT
    ("best resort in kanakapura",         "PHRASE"),  # ₹2903 CPA, QS=4 dup
    ("night stay in kanakapura",          "PHRASE"),  # ₹1889 CPA
    ("best stay for couples in bangalore","PHRASE"),  # 0 conv, ₹354
    ("camping resort bangalore",          "PHRASE"),  # 0 conv, ₹194
    ("glamping near bangalore",           "PHRASE"),  # 0 conv, ₹208
]

def phase_b_pause():
    print("\n" + "="*75)
    print("PHASE B: PAUSE 7 WASTEFUL KEYWORDS")
    print("="*75)

    q = f"""SELECT ad_group.name,
                   ad_group_criterion.resource_name,
                   ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status,
                   ad_group_criterion.negative
            FROM keyword_view
            WHERE campaign.id = {CAMP_ID}
              AND ad_group_criterion.status = 'ENABLED'"""
    pause_set = set((t.lower(), m) for t, m in PAUSE_KW)
    targets = []
    for r in google_gaql(cfg, q):
        c = r["adGroupCriterion"]
        if c.get("negative"): continue
        k = c.get("keyword", {})
        key = (k.get("text","").lower(), k.get("matchType",""))
        if key in pause_set:
            targets.append({"rn": c["resourceName"], "text": k["text"], "match": k["matchType"], "ag": r["adGroup"]["name"]})

    print(f"\n  Found {len(targets)} matching enabled keywords:")
    for t in targets:
        print(f"    PAUSE [{t['match']:<6}] {t['text']:<42} (ag: {t['ag']})")

    if not targets:
        return []

    svc = cl.get_service("AdGroupCriterionService")
    paused = []
    for t in targets:
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = t["rn"]
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.PAUSED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
            paused.append({"rn": t["rn"], "text": t["text"], "match": t["match"]})
            print(f"    [OK] paused '{t['text']}'")
        except Exception as e:
            print(f"    [FAIL] '{t['text']}': {str(e)[:200]}")
    print(f"\n  [OK] {len(paused)}/{len(targets)} paused")
    return paused


# ─── PHASE C: DESKTOP BID -25% ───────────────────────────
def phase_c_device():
    print("\n" + "="*75)
    print("PHASE C: DEVICE — DESKTOP ×0.75 (was ×1.00)")
    print("="*75)

    q = f"""SELECT campaign_criterion.resource_name,
                   campaign_criterion.device.type,
                   campaign_criterion.bid_modifier
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.type = 'DEVICE'"""
    desktop_rn = None; current = 1.0
    for r in google_gaql(cfg, q):
        c = r["campaignCriterion"]
        if c.get("device",{}).get("type") == "DESKTOP":
            desktop_rn = c["resourceName"]
            current = c.get("bidModifier", 1.0)
            break

    if not desktop_rn:
        print("  [WARN] No DESKTOP criterion found — skipping (campaign uses default)")
        return None

    if abs(current - 0.75) < 0.001:
        print(f"  [skip] Desktop already ×0.75")
        return None

    svc = cl.get_service("CampaignCriterionService")
    op = cl.get_type("CampaignCriterionOperation")
    op.update.resource_name = desktop_rn
    op.update.bid_modifier = 0.75
    op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
    try:
        svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] Desktop ×{current:.2f} → ×0.75")
        return {"rn": desktop_rn, "old": current, "new": 0.75}
    except Exception as e:
        print(f"  [FAIL] {str(e)[:200]}")
        return None


# ─── PHASE D: FRI/SAT 8-9h ×0.60 MORNING THROTTLE ─────────
def phase_d_fri_sat_throttle():
    print("\n" + "="*75)
    print("PHASE D: ADD FRI/SAT 8-9h ×0.60 MORNING THROTTLE")
    print("="*75)

    # Check what's already there
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
    # Identify Fri / Sat 8-22h ×1.00 — we need to split off the 8-9h slice as ×0.60
    svc = cl.get_service("CampaignCriterionService")
    plan_ops = []
    plan_log = []
    state_to_save = {"removed": [], "added": []}

    for day in ["FRIDAY", "SATURDAY"]:
        # Look for the ×1.00 8-22h block on this day
        target = next((s for s in existing if s["day"] == day and s["start"] == 8 and s["end"] == 22 and abs(s["bm"]-1.0)<0.01), None)
        if not target:
            print(f"  [skip] {day} 8-22h ×1.00 not found")
            continue
        # 1) Remove the existing 8-22h
        rm_op = cl.get_type("CampaignCriterionOperation")
        rm_op.remove = target["rn"]
        plan_ops.append(rm_op)
        plan_log.append(f"REMOVE {day} 8-22h ×1.00")
        state_to_save["removed"].append(target)

        # 2) Add 8-9h ×0.60
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
        state_to_save["added"].append({"day": day, "start": 8, "end": 9, "bm": 0.60})

        # 3) Add 9-22h ×1.00
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
        state_to_save["added"].append({"day": day, "start": 9, "end": 22, "bm": 1.00})

    print(f"\n  Plan ({len(plan_ops)} ops):")
    for log in plan_log:
        print(f"    {log}")

    if not plan_ops:
        return state_to_save

    try:
        svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=plan_ops)
        print(f"\n  [OK] schedule updated")
    except Exception as e:
        print(f"\n  [FAIL] schedule: {str(e)[:300]}")
    return state_to_save


# ─── PHASE E: AGE BID MODS ────────────────────────────────
AGE_TARGETS = {
    "AGE_RANGE_35_44": 1.15,  # was ×0.85
    "AGE_RANGE_45_54": 1.10,  # was ×0.85
    "AGE_RANGE_55_64": 1.20,  # was —
}


def phase_e_age():
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
    plan_log = []
    saved = []
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
                saved.append({"rn": r["rn"], "old": r["bm"], "new": target_bm, "age": age})
                print(f"  [OK] {age:<20} '{r['ag'][:25]}'  ×{r['bm']:.2f} → ×{target_bm:.2f}")
            except Exception as e:
                print(f"  [FAIL] {age} in '{r['ag']}': {str(e)[:150]}")

    return saved


def main():
    print(f"=== Resort April 2026 optimization — {datetime.datetime.now()} ===")
    state["phases"]["A_negatives"] = phase_a_negatives()
    state["phases"]["B_paused"]    = phase_b_pause()
    state["phases"]["C_device"]    = phase_c_device()
    state["phases"]["D_schedule"]  = phase_d_fri_sat_throttle()
    state["phases"]["E_age"]       = phase_e_age()

    with open("/Users/girishkumar/Documents/ads/.resort_april_state.json", "w") as f:
        json.dump(state, f, indent=2, default=str)

    print("\n" + "="*75)
    print("=== ALL DONE — state saved to .resort_april_state.json (for revert) ===")
    print("="*75)


if __name__ == "__main__":
    main()
