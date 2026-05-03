#!/usr/bin/env python3
"""Phase 3 ONLY — add 7 verified candidate keywords as EXACT match.
Phase 1 paused 10 zero-vol/junk positives (the 27 'failures' were NEGATIVES — left as-is).
Phase 2 verified 7 of 8 candidates (overnight stay near bangalore = 40/mo, skipped).
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

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"

# 7 verified candidates from Phase 2 (overnight stay 40/mo dropped)
TO_ADD = [
    ("resorts near bangalore",            27_100),
    ("weekend getaway from bangalore",    12_100),
    ("day outing resort bangalore",       14_800),
    ("resort near bangalore for couples", 1_000),
    ("day outing near bangalore",         390),
    ("kanakapura resort price",           320),
    ("private pool villa near bangalore", 140),
]

cfg = load_config()
cl = _get_google_ads_client(cfg)

# Find best ad group (most clicks last 30d, ENABLED, NOT negative)
def get_target_ag():
    q = f"""SELECT ad_group.id, ad_group.name,
                   metrics.clicks, metrics.impressions
            FROM ad_group
            WHERE campaign.id = {CAMP_ID}
              AND ad_group.status = 'ENABLED'
              AND segments.date DURING LAST_30_DAYS"""
    rows = list(google_gaql(cfg, q))
    agg = {}
    for r in rows:
        aid = r["adGroup"]["id"]
        m = r.get("metrics",{})
        if aid not in agg:
            agg[aid] = {"id": aid, "name": r["adGroup"]["name"], "clicks": 0, "impr": 0}
        agg[aid]["clicks"] += int(m.get("clicks", 0))
        agg[aid]["impr"]   += int(m.get("impressions", 0))
    sorted_ags = sorted(agg.values(), key=lambda x: x["clicks"], reverse=True)
    return sorted_ags

# Existing positive keywords to avoid duplicates
def get_existing_positives():
    q = f"""SELECT ad_group.id, ad_group.name,
                   ad_group_criterion.criterion_id,
                   ad_group_criterion.resource_name,
                   ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status,
                   ad_group_criterion.negative
            FROM keyword_view
            WHERE campaign.id = {CAMP_ID}"""
    out = {}
    for r in google_gaql(cfg, q):
        c = r["adGroupCriterion"]
        if c.get("negative"):
            continue
        kw = c.get("keyword", {})
        text = kw.get("text", "").lower()
        match = kw.get("matchType", "")
        if match != "EXACT":
            continue
        out[text] = {
            "rn": c["resourceName"],
            "status": c.get("status", ""),
            "ag": r["adGroup"]["name"],
        }
    return out


def main():
    ags = get_target_ag()
    if not ags:
        print("[ERR] No enabled ad groups")
        return
    target = ags[0]
    print(f"Target ad group: '{target['name']}' (id={target['id']}) — top performer\n")

    existing = get_existing_positives()
    svc = cl.get_service("AdGroupCriterionService")
    add_ops = []
    enable_ops = []
    add_plan = []
    enable_plan = []

    for text, mo in TO_ADD:
        e = existing.get(text.lower())
        if e:
            if e["status"] == "ENABLED":
                print(f"  [skip] '{text}' EXACT already ENABLED in '{e['ag']}'")
                continue
            elif e["status"] in ("PAUSED", "REMOVED"):
                print(f"  [enable] '{text}' EXACT exists as {e['status']} in '{e['ag']}' → re-enabling")
                op = cl.get_type("AdGroupCriterionOperation")
                op.update.resource_name = e["rn"]
                op.update.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
                op.update_mask.CopyFrom(FieldMask(paths=["status"]))
                enable_ops.append(op)
                enable_plan.append((text, mo))
                continue
        # Brand new
        op = cl.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{target['id']}"
        c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = text
        c.keyword.match_type = cl.enums.KeywordMatchTypeEnum.EXACT
        add_ops.append(op)
        add_plan.append((text, mo))

    print(f"\nADD plan ({len(add_plan)}):")
    for t, mo in add_plan:
        print(f"  ADD [EXACT] {t:<42} ({mo:,}/mo)")
    print(f"\nRE-ENABLE plan ({len(enable_plan)}):")
    for t, mo in enable_plan:
        print(f"  RE-ENABLE [EXACT] {t:<42} ({mo:,}/mo)")

    # Execute
    if enable_ops:
        try:
            r = svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=enable_ops)
            print(f"\n[OK] Re-enabled {len(r.results)}")
        except Exception as e:
            print(f"\n[WARN] Batch re-enable failed, going one-by-one")
            for i, op in enumerate(enable_ops):
                try:
                    svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
                except Exception as e2:
                    print(f"  [skip re-enable] '{enable_plan[i][0]}': {str(e2)[:120]}")

    if add_ops:
        try:
            r = svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=add_ops)
            print(f"\n[OK] Added {len(r.results)} new EXACT keywords")
        except Exception as e:
            print(f"\n[WARN] Batch add failed, going one-by-one: {str(e)[:200]}")
            ok = 0
            for i, op in enumerate(add_ops):
                try:
                    svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
                    ok += 1
                    print(f"  [OK] '{add_plan[i][0]}'")
                except Exception as e2:
                    print(f"  [FAIL] '{add_plan[i][0]}': {str(e2)[:200]}")
            print(f"\n[OK] {ok}/{len(add_ops)} added (one-by-one)")


if __name__ == "__main__":
    main()
