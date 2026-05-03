#!/usr/bin/env python3
"""
Resort campaign 21740834372 — keyword cleanup approved 2026-05-03 by Girish.

Phase 1: PAUSE 36 dead/junk keywords (25 BROAD landmines + 10 zero-vol dups + 1 honeymoon)
Phase 2: Verify 8 candidate keywords via Keyword Planner
Phase 3: Add verified candidates as EXACT match to best-performing ad group

User instruction: "exact wherever required, i dont want to have any issues"
=> Default to EXACT for tight intent control. PHRASE only if naturally variable.
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
from google.protobuf.field_mask_pb2 import FieldMask
import json, datetime

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"

# ─── 36 keywords to PAUSE (case-insensitive match on text) ─────────────
DEAD_BROAD = [
    "photos","images","ooty","goa","kerala","free","coorg","jobs","internship",
    "career","under","review","budget","wedding","discount","rating","cheap",
    "affordable","cheapest","function hall","low price","low cost",
    "under 500","under 1000","under 2000","honeymoon",
]
DEAD_ZERO_VOL = [
    "night stay in kanakapura","eco stay kanakapura","couples resort near bangalore",
    "kanakapura nature resort","stay in kanakapura resort","kanakapura stay resort",
    "family resort kanakapura","nature resort near kanakapura",
    "resort with bonfire near bangalore","cottages in kanakapura",
]
PAUSE_LIST = set([t.lower() for t in DEAD_BROAD + DEAD_ZERO_VOL])

# ─── 8 candidate keywords to verify + add ─────────────────────────────
# All EXACT for safety (user explicit request)
CANDIDATES = [
    ("resorts near bangalore",            "EXACT"),
    ("weekend getaway from bangalore",    "EXACT"),
    ("day outing near bangalore",         "EXACT"),
    ("kanakapura resort price",           "EXACT"),
    ("resort near bangalore for couples", "EXACT"),
    ("overnight stay near bangalore",     "EXACT"),
    ("day outing resort bangalore",       "EXACT"),
    ("private pool villa near bangalore", "EXACT"),
]

cfg = load_config()
cl = _get_google_ads_client(cfg)


# ─────────────────────────────────────────────────
# PHASE 1: pause dead keywords
# ─────────────────────────────────────────────────
def phase_1_pause():
    print("=" * 75)
    print("PHASE 1: PAUSE 36 dead/junk keywords")
    print("=" * 75)

    q = f"""SELECT ad_group.id, ad_group.name,
                   ad_group_criterion.criterion_id,
                   ad_group_criterion.resource_name,
                   ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status
            FROM keyword_view
            WHERE campaign.id = {CAMP_ID}
              AND ad_group_criterion.status = 'ENABLED'"""
    targets = []
    for r in google_gaql(cfg, q):
        kw = r["adGroupCriterion"].get("keyword", {})
        text = kw.get("text", "")
        if text.lower() in PAUSE_LIST:
            targets.append({
                "rn": r["adGroupCriterion"]["resourceName"],
                "text": text,
                "match": kw.get("matchType", ""),
                "ag": r["adGroup"]["name"],
            })

    print(f"\nFound {len(targets)} matching keywords to pause:\n")
    for t in targets:
        print(f"  PAUSE [{t['match']:<7}] {t['text']:<42} (ag: {t['ag']})")

    if not targets:
        print("  Nothing to pause.")
        return

    svc = cl.get_service("AdGroupCriterionService")
    ops = []
    for t in targets:
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = t["rn"]
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.PAUSED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        ops.append(op)

    try:
        resp = svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
        print(f"\n[OK] {len(resp.results)} keywords paused")
    except Exception as e:
        msg = str(e)
        # Try one-by-one if batch fails
        print(f"\n[WARN] Batch failed, retrying one-by-one: {msg[:200]}")
        ok = 0
        for op in ops:
            try:
                svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
                ok += 1
            except Exception as e2:
                print(f"  [skip] {str(e2)[:150]}")
        print(f"\n[OK] {ok}/{len(ops)} keywords paused (one-by-one)")


# ─────────────────────────────────────────────────
# PHASE 2: verify candidate volumes
# ─────────────────────────────────────────────────
def phase_2_verify():
    print("\n" + "=" * 75)
    print("PHASE 2: Verify candidate keyword volumes (Keyword Planner, India)")
    print("=" * 75 + "\n")

    svc = cl.get_service("KeywordPlanIdeaService")
    req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = CUSTOMER_ID
    req.language = "languageConstants/1000"
    req.geo_target_constants.append("geoTargetConstants/2356")  # India
    req.include_adult_keywords = False
    req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    req.keywords.extend([t for t,_ in CANDIDATES])
    resp = svc.generate_keyword_historical_metrics(request=req)

    vol_map = {}
    for r in resp.results:
        m = r.keyword_metrics
        vol_map[r.text.lower()] = {
            "monthly": getattr(m, "avg_monthly_searches", 0) or 0,
            "comp": str(m.competition).split(".")[-1] if m.competition else "—",
            "low": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
            "high": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
        }

    print(f"{'Candidate':<40} {'Match':<6} {'Mo/India':>10} {'Comp':<7} {'CPC ₹':<10} {'Decision'}")
    print("-" * 90)
    verified = []
    for text, match in CANDIDATES:
        v = vol_map.get(text.lower(), {})
        mo = v.get("monthly", 0)
        if mo >= 100:
            decision = "✅ ADD"
            verified.append((text, match, mo, v))
        else:
            decision = f"❌ skip (only {mo}/mo)"
        cpc = f"{v.get('low',0):.0f}-{v.get('high',0):.0f}" if v else "—"
        print(f"{text:<40} {match:<6} {mo:>10,} {v.get('comp','—'):<7} {cpc:<10} {decision}")

    return verified


# ─────────────────────────────────────────────────
# PHASE 3: add verified keywords as EXACT
# ─────────────────────────────────────────────────
def get_target_ad_group():
    """Pick best-performing enabled ad group (most clicks last 30d)."""
    q = f"""SELECT ad_group.id, ad_group.name, ad_group.cpc_bid_micros,
                   metrics.clicks, metrics.impressions, metrics.conversions
            FROM ad_group
            WHERE campaign.id = {CAMP_ID}
              AND ad_group.status = 'ENABLED'
              AND segments.date DURING LAST_30_DAYS"""
    ags = []
    for r in google_gaql(cfg, q):
        ags.append({
            "id": r["adGroup"]["id"],
            "name": r["adGroup"]["name"],
            "cpc": int(r["adGroup"].get("cpcBidMicros", 0)),
            "clicks": int(r.get("metrics",{}).get("clicks", 0)),
            "impr": int(r.get("metrics",{}).get("impressions", 0)),
        })
    # aggregate (one row per ag)
    agg = {}
    for a in ags:
        if a["id"] not in agg:
            agg[a["id"]] = a
        else:
            agg[a["id"]]["clicks"] += a["clicks"]
            agg[a["id"]]["impr"] += a["impr"]
    sorted_ags = sorted(agg.values(), key=lambda x: x["clicks"], reverse=True)
    return sorted_ags


def phase_3_add(verified):
    print("\n" + "=" * 75)
    print("PHASE 3: Add verified keywords as EXACT")
    print("=" * 75)

    if not verified:
        print("\n[--] No verified candidates to add")
        return

    ags = get_target_ad_group()
    print(f"\nEnabled ad groups in campaign (last 30d):")
    for a in ags[:5]:
        print(f"  AG {a['id']}  '{a['name']}'  clicks={a['clicks']}  impr={a['impr']}")

    if not ags:
        print("\n[ERR] No enabled ad groups — abort")
        return
    target = ags[0]
    print(f"\nTarget ad group: '{target['name']}' (id={target['id']})  — top performer\n")

    # Check if any of these keywords already exist anywhere on the campaign
    existing_q = f"""SELECT ad_group.id, ad_group.name,
                            ad_group_criterion.keyword.text,
                            ad_group_criterion.keyword.match_type,
                            ad_group_criterion.status
                     FROM keyword_view
                     WHERE campaign.id = {CAMP_ID}"""
    existing = set()
    for r in google_gaql(cfg, existing_q):
        kw = r["adGroupCriterion"].get("keyword", {})
        existing.add((kw.get("text","").lower(), kw.get("matchType","")))

    svc = cl.get_service("AdGroupCriterionService")
    ops = []
    plan = []
    for text, match, mo, v in verified:
        key = (text.lower(), match)
        if key in existing:
            print(f"  [skip] '{text}' ({match}) already exists on campaign")
            continue
        op = cl.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{target['id']}"
        c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = text
        c.keyword.match_type = cl.enums.KeywordMatchTypeEnum[match]
        ops.append(op)
        plan.append((text, match, mo))

    print(f"\nAdding {len(ops)} new keywords:")
    for text, match, mo in plan:
        print(f"  ADD [{match:<5}] {text:<42} ({mo:,}/mo)")

    if not ops:
        print("\n  Nothing new to add.")
        return

    try:
        resp = svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
        print(f"\n[OK] {len(resp.results)} keywords added")
    except Exception as e:
        msg = str(e)
        print(f"\n[WARN] Batch add failed, retrying one-by-one: {msg[:200]}")
        ok = 0
        for i, op in enumerate(ops):
            try:
                svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
                ok += 1
            except Exception as e2:
                print(f"  [skip] '{plan[i][0]}': {str(e2)[:150]}")
        print(f"\n[OK] {ok}/{len(ops)} keywords added (one-by-one)")


def main():
    print(f"=== Resort keyword cleanup — {datetime.datetime.now()} ===\n")
    phase_1_pause()
    verified = phase_2_verify()
    phase_3_add(verified)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
