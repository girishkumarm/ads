#!/usr/bin/env python3
"""Pull Keyword Planner volumes for all ENABLED Jayanagar cafe keywords.
India + Bangalore geo. Flag low-volume / dead keywords."""
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
CAMP_ID = "23778954613"
cfg = load_config()
cl = _get_google_ads_client(cfg)

# 1. Pull all enabled positive keywords on Jayanagar cafe
print("Pulling enabled keywords from Jayanagar Cafe Search 23778954613...")
q = f"""SELECT ad_group.id, ad_group.name,
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
print(f"Found {len(kws)} unique enabled keywords\n")


# 2. Keyword Planner volumes — India + Bangalore geos
print("Querying Keyword Planner for India volumes...")
svc = cl.get_service("KeywordPlanIdeaService")
def get_volumes(geo_id):
    req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = CUSTOMER_ID
    req.language = "languageConstants/1000"
    req.geo_target_constants.append(f"geoTargetConstants/{geo_id}")
    req.include_adult_keywords = False
    req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    req.keywords.extend([k["text"] for k in kws])
    try:
        r = svc.generate_keyword_historical_metrics(request=req)
        out = {}
        for x in r.results:
            m = x.keyword_metrics
            out[x.text.lower()] = {
                "monthly": getattr(m, "avg_monthly_searches", 0) or 0,
                "comp": str(m.competition).split(".")[-1] if m.competition else "—",
                "low": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
                "high": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
            }
        return out
    except Exception as e:
        print(f"  [ERR] {geo_id}: {str(e)[:200]}")
        return {}

india = get_volumes("2356")  # India
karnataka = get_volumes("20174")  # Karnataka

# Merge
for k in kws:
    v_in = india.get(k["text"].lower(), {})
    v_ka = karnataka.get(k["text"].lower(), {})
    k["india"] = v_in.get("monthly", 0)
    k["kar"] = v_ka.get("monthly", 0)
    k["comp"] = v_in.get("comp", "—")
    k["low"] = v_in.get("low", 0)
    k["high"] = v_in.get("high", 0)

# Sort by India volume desc
kws.sort(key=lambda x: -x["india"])


# 3. Print verdict per keyword
print(f"\n{'='*100}")
print(f"  Jayanagar Cafe — {len(kws)} ENABLED keywords (sorted by India search volume)")
print(f"{'='*100}")
print(f"  {'Keyword':<38} {'Match':<7} {'QS':>3} {'India/mo':>9} {'Kar':>5} {'Clk30d':>6} {'Conv':>5} {'CPC ₹':<10} {'Verdict'}")
print("  " + "-"*100)

keep, weak, drop = [], [], []
for k in kws:
    qs = str(k["qs"]) if k["qs"] is not None else "-"
    cpc = f"{k['low']:.0f}-{k['high']:.0f}" if k["high"] else "—"
    if k["india"] >= 200:
        verdict = "✅ KEEP"; keep.append(k)
    elif k["india"] >= 50:
        verdict = "🟡 weak"; weak.append(k)
    elif k["clicks"] >= 5 or k["conv"] >= 1:
        verdict = "🟡 close-variant works"; weak.append(k)
    else:
        verdict = "🔴 DROP — 0 vol, no traffic"; drop.append(k)
    print(f"  {k['text'][:37]:<38} {k['match']:<7} {qs:>3} {k['india']:>9,} {k['kar']:>5,} {k['clicks']:>6} {k['conv']:>5.0f} {cpc:<10} {verdict}")


print(f"\n{'='*100}")
print(f"  SUMMARY")
print(f"{'='*100}")
print(f"  ✅ KEEP (≥200/mo India):   {len(keep):>3}")
print(f"  🟡 WEAK (50-199 OR has traffic): {len(weak):>3}")
print(f"  🔴 DROP (0 vol, no clicks): {len(drop):>3}")
print(f"  TOTAL: {len(kws)}")

print(f"\n  Total addressable monthly volume (India): {sum(k['india'] for k in keep):,}")
print(f"  Last 30d real traffic: {sum(k['clicks'] for k in kws)} clicks, {sum(k['conv'] for k in kws):.0f} conversions")
