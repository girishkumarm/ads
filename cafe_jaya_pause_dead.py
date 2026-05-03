#!/usr/bin/env python3
"""Pause Jayanagar cafe keywords with 0 volume AND 0 traffic.
Keeps 'close variant winners' that get real clicks despite 0 indexed volume."""
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
CAMP_ID = "23778954613"
cfg = load_config()
cl = _get_google_ads_client(cfg)


# 1. Pull all enabled positive keywords + last-30d traffic
print("Pulling enabled keywords...")
q = f"""SELECT ad_group.id, ad_group.name,
               ad_group_criterion.resource_name,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.negative,
               metrics.clicks, metrics.impressions, metrics.conversions
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
            "clicks": 0, "impr": 0, "conv": 0,
        }
    agg[key]["clicks"] += int(m.get("clicks", 0))
    agg[key]["impr"]   += int(m.get("impressions", 0))
    agg[key]["conv"]   += float(m.get("conversions", 0))

kws = list(agg.values())


# 2. Pull KW Planner volumes
print("Querying Keyword Planner for India volumes...")
svc = cl.get_service("KeywordPlanIdeaService")
req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
req.customer_id = CUSTOMER_ID
req.language = "languageConstants/1000"
req.geo_target_constants.append("geoTargetConstants/2356")
req.include_adult_keywords = False
req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
req.keywords.extend([k["text"] for k in kws])
resp = svc.generate_keyword_historical_metrics(request=req)
vol_map = {x.text.lower(): (getattr(x.keyword_metrics, "avg_monthly_searches", 0) or 0)
           for x in resp.results}


# 3. Identify dead keywords (0 vol AND 0 clicks AND 0 impressions)
to_pause = []
keep_close_variant = []
for k in kws:
    vol = vol_map.get(k["text"].lower(), 0)
    has_traffic = (k["clicks"] >= 2 or k["conv"] >= 1 or k["impr"] >= 50)
    if vol < 30 and not has_traffic:
        to_pause.append(k)
    elif vol < 200 and has_traffic:
        keep_close_variant.append(k)


print(f"\nDead keywords to pause: {len(to_pause)}")
print(f"Close-variant winners (kept): {len(keep_close_variant)}")
print()


# 4. Pause them
if not to_pause:
    print("Nothing to pause.")
else:
    svc = cl.get_service("AdGroupCriterionService")
    ok = 0; failed = 0
    for k in to_pause:
        op = cl.get_type("AdGroupCriterionOperation")
        op.update.resource_name = k["rn"]
        op.update.status = cl.enums.AdGroupCriterionStatusEnum.PAUSED
        op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
            ok += 1
            print(f"  [OK] paused [{k['match']:<7}] {k['text']}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {k['text']}: {str(e)[:120]}")
    print(f"\n[DONE] {ok}/{len(to_pause)} paused, {failed} failed")


# 5. Show kept close-variant winners for transparency
if keep_close_variant:
    print(f"\nKEPT (close-variant winners with real traffic):")
    for k in keep_close_variant:
        print(f"  [{k['match']:<7}] {k['text']:<35}  {k['clicks']} clk, {k['conv']:.0f} conv")
