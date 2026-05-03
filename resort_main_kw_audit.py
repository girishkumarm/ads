#!/usr/bin/env python3
"""KW Planner audit on main resort campaign 21740834372 (Ecostay - Kanakapura).
Pause 0-vol + 0-traffic keywords; keep close-variant winners."""
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
CAMP_ID = "21740834372"  # Main resort campaign
cfg = load_config()
cl = _get_google_ads_client(cfg)


# 1. Pull all enabled positive keywords + last-30d traffic
print("Pulling enabled keywords from Ecostay - Kanakapura...")
q = f"""SELECT ad_group.id, ad_group.name,
               ad_group_criterion.resource_name,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.negative,
               ad_group_criterion.quality_info.quality_score,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_criterion.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND segments.date DURING LAST_30_DAYS"""

agg = {}
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"): continue
    k = c.get("keyword", {})
    text = k.get("text", "")
    match = k.get("matchType", "")
    key = (text.lower(), match)
    m = r.get("metrics", {})
    if key not in agg:
        agg[key] = {
            "rn": c["resourceName"],
            "text": text, "match": match,
            "ag": r["adGroup"]["name"],
            "qs": c.get("qualityInfo", {}).get("qualityScore"),
            "clicks": 0, "impr": 0, "cost": 0, "conv": 0,
        }
    agg[key]["clicks"] += int(m.get("clicks", 0))
    agg[key]["impr"]   += int(m.get("impressions", 0))
    agg[key]["cost"]   += int(m.get("costMicros", 0)) / 1e6
    agg[key]["conv"]   += float(m.get("conversions", 0))

kws = list(agg.values())
print(f"Found {len(kws)} unique enabled keywords")


# 2. Pull KW Planner volumes (India)
print("\nQuerying Keyword Planner — India volumes...")
svc = cl.get_service("KeywordPlanIdeaService")
req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
req.customer_id = CUSTOMER_ID
req.language = "languageConstants/1000"
req.geo_target_constants.append("geoTargetConstants/2356")
req.include_adult_keywords = False
req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
req.keywords.extend([k["text"] for k in kws])
resp = svc.generate_keyword_historical_metrics(request=req)

vol_map = {}
for x in resp.results:
    m = x.keyword_metrics
    vol_map[x.text.lower()] = {
        "monthly": getattr(m, "avg_monthly_searches", 0) or 0,
        "comp": str(m.competition).split(".")[-1] if m.competition else "—",
        "low": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
        "high": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
    }


# 3. Classify
keep, weak_with_traffic, dead = [], [], []
for k in kws:
    v = vol_map.get(k["text"].lower(), {})
    vol = v.get("monthly", 0)
    has_traffic = (k["clicks"] >= 2 or k["conv"] >= 1 or k["impr"] >= 50)
    k["india"] = vol
    k["comp"] = v.get("comp", "—")
    k["low"] = v.get("low", 0)
    k["high"] = v.get("high", 0)
    if vol >= 200:
        keep.append(k)
    elif has_traffic:
        weak_with_traffic.append(k)
    else:
        dead.append(k)


# 4. Display
kws_sorted = sorted(kws, key=lambda x: -x["india"])
print(f"\n{'='*100}")
print(f"  Resort campaign — {len(kws)} ENABLED keywords (sorted by India search volume)")
print(f"{'='*100}")
print(f"  {'Keyword':<40} {'Match':<7} {'QS':>3} {'India/mo':>9} {'Clk':>4} {'Conv':>5} {'CPC ₹':<10} {'Verdict'}")
print("  " + "-"*100)
for k in kws_sorted:
    qs = str(k["qs"]) if k["qs"] is not None else "-"
    cpc = f"{k['low']:.0f}-{k['high']:.0f}" if k["high"] else "—"
    has_traffic = (k["clicks"] >= 2 or k["conv"] >= 1 or k["impr"] >= 50)
    if k["india"] >= 200:
        verdict = "✅ KEEP"
    elif has_traffic:
        verdict = "🟡 KEEP (close-variant)"
    else:
        verdict = "🔴 PAUSE"
    print(f"  {k['text'][:39]:<40} {k['match']:<7} {qs:>3} {k['india']:>9,} {k['clicks']:>4} {k['conv']:>5.0f} {cpc:<10} {verdict}")


print(f"\n{'='*100}")
print(f"  SUMMARY")
print(f"{'='*100}")
print(f"  ✅ KEEP (≥200/mo):                   {len(keep):>3}")
print(f"  🟡 KEEP (close-variant w/ traffic):   {len(weak_with_traffic):>3}")
print(f"  🔴 PAUSE (0 vol + 0 traffic):         {len(dead):>3}")
print(f"  TOTAL: {len(kws)}")

if dead:
    print(f"\n  Will pause {len(dead)} dead keywords:")
    for k in dead:
        print(f"    [{k['match']:<7}] {k['text']}")


# 5. Pause the dead ones
if dead:
    print(f"\nPausing {len(dead)} dead keywords...")
    svc = cl.get_service("AdGroupCriterionService")
    ok = 0; failed = 0
    for k in dead:
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = k["rn"]
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.PAUSED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
            ok += 1
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {k['text']}: {str(e)[:120]}")
    print(f"\n[DONE] {ok}/{len(dead)} paused, {failed} failed")
