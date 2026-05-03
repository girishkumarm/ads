#!/usr/bin/env python3
"""BTM Search 22635490939 — full April audit (different ad account 7614460903).
Goal: diagnose 0-conversion disaster despite ₹30K spend."""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""

from ads_api import load_config, google_gaql

CAMP_ID = "22635490939"
DR = "segments.date BETWEEN '2026-04-01' AND '2026-04-30'"
cfg = load_config()
# Switch to BTM account
cfg["google_ads"]["customer_id"] = cfg["google_ads"]["cafe_customer_id"]


def section(t):
    print(f"\n{'='*80}\n{t}\n{'='*80}")


# Conversion tracking diagnostic FIRST
section("0. CONVERSION ACTIONS CONFIGURED ON BTM ACCOUNT")
q = """SELECT conversion_action.id, conversion_action.name, conversion_action.status,
              conversion_action.type, conversion_action.category,
              conversion_action.primary_for_goal,
              conversion_action.counting_type
       FROM conversion_action WHERE conversion_action.status != 'REMOVED'"""
for r in google_gaql(cfg, q):
    ca = r["conversionAction"]
    print(f"  {ca['id']:<14} {ca.get('name','')[:35]:<36} {ca.get('status',''):<10} "
          f"{ca.get('type',''):<22} {ca.get('category',''):<14} "
          f"primary={ca.get('primaryForGoal','?')}")


# Impression share
section("1. IMPRESSION SHARE — APRIL")
q = f"""SELECT metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    print(f"  Search IS: {m.get('searchImpressionShare', 0)*100:.1f}%   "
          f"Lost-Budget: {m.get('searchBudgetLostImpressionShare', 0)*100:.1f}%   "
          f"Lost-Rank: {m.get('searchRankLostImpressionShare', 0)*100:.1f}%")
    break


# Keywords
section("2. KEYWORDS — APRIL")
q = f"""SELECT ad_group.name,
               ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
               ad_group_criterion.status, ad_group_criterion.negative,
               ad_group_criterion.quality_info.quality_score,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID} AND {DR}"""
agg = {}
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"): continue
    k = c.get("keyword", {})
    m = r.get("metrics",{})
    if int(m.get("impressions",0)) == 0: continue
    key = (k.get("text",""), k.get("matchType",""))
    if key not in agg:
        agg[key] = {"text":k.get("text",""),"match":k.get("matchType",""),
                    "qs":c.get("qualityInfo",{}).get("qualityScore"),
                    "ag":r["adGroup"]["name"],"status":c.get("status",""),
                    "clicks":0,"impr":0,"cost":0,"conv":0}
    agg[key]["clicks"] += int(m.get("clicks",0))
    agg[key]["impr"]   += int(m.get("impressions",0))
    agg[key]["cost"]   += int(m.get("costMicros",0))/1e6
    agg[key]["conv"]   += float(m.get("conversions",0))
kws = sorted(agg.values(), key=lambda x: x["cost"], reverse=True)
print(f"{'Keyword':<35} {'Match':<7} {'QS':>3} {'Status':<8} {'Impr':>5} {'Clk':>5} {'Conv':>5} {'Cost ₹':>7} {'CTR':>5}")
for k in kws[:30]:
    qs = str(k["qs"]) if k["qs"] is not None else "-"
    ctr = k["clicks"]/k["impr"]*100 if k["impr"] else 0
    print(f"{k['text'][:34]:<35} {k['match']:<7} {qs:>3} {k['status']:<8} "
          f"{k['impr']:>5} {k['clicks']:>5} {k['conv']:>5.0f} {k['cost']:>7.0f} {ctr:>4.1f}%")


# Search terms
section("3. SEARCH TERMS — TOP 30 BY COST")
q = f"""SELECT search_term_view.search_term, search_term_view.status,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {CAMP_ID} AND {DR}"""
terms = []
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    cost = int(m.get("costMicros",0))/1e6
    if cost == 0: continue
    terms.append({"term":r["searchTermView"]["searchTerm"],
                  "status":r["searchTermView"].get("status",""),
                  "clicks":int(m.get("clicks",0)),
                  "cost":cost,
                  "conv":float(m.get("conversions",0))})
terms.sort(key=lambda x: x["cost"], reverse=True)
print(f"{'Search term':<55} {'Clk':>4} {'Cost ₹':>7} {'Status':<14}")
for t in terms[:30]:
    print(f"{t['term'][:54]:<55} {t['clicks']:>4} {t['cost']:>7.0f} {t['status']:<14}")
print(f"\nTotal April spend on listed terms: ₹{sum(t['cost'] for t in terms):.0f}")


# Device
section("4. DEVICE")
q = f"""SELECT segments.device, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
print(f"{'Device':<10} {'Impr':>6} {'Clk':>5} {'Conv':>5} {'Cost ₹':>7}")
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    if not int(m.get("impressions",0)): continue
    print(f"{r['segments']['device']:<10} {int(m.get('impressions',0)):>6} "
          f"{int(m.get('clicks',0)):>5} {float(m.get('conversions',0)):>5.0f} "
          f"{int(m.get('costMicros',0))/1e6:>7.0f}")


# Hours
section("5. HOUR-OF-DAY")
q = f"""SELECT segments.hour, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
hours = sorted([{"h":r["segments"]["hour"],
                 "impr":int(r["metrics"].get("impressions",0)),
                 "clk":int(r["metrics"].get("clicks",0)),
                 "cost":int(r["metrics"].get("costMicros",0))/1e6,
                 "conv":float(r["metrics"].get("conversions",0))}
                for r in google_gaql(cfg, q) if int(r["metrics"].get("impressions",0))],
               key=lambda x: x["h"])
print(f"{'Hr':<4} {'Impr':>5} {'Clk':>4} {'CTR':>5} {'Conv':>4} {'Cost ₹':>7}")
for h in hours:
    print(f"{h['h']:>2}h  {h['impr']:>5} {h['clk']:>4} "
          f"{h['clk']/h['impr']*100 if h['impr'] else 0:>4.0f}% "
          f"{h['conv']:>4.0f} {h['cost']:>7.0f}")


# Day-of-week
section("6. DAY-OF-WEEK")
q = f"""SELECT segments.day_of_week, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
order = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]
dows = sorted([{"d":r["segments"]["dayOfWeek"],
                "impr":int(r["metrics"].get("impressions",0)),
                "clk":int(r["metrics"].get("clicks",0)),
                "cost":int(r["metrics"].get("costMicros",0))/1e6,
                "conv":float(r["metrics"].get("conversions",0))}
               for r in google_gaql(cfg, q) if int(r["metrics"].get("impressions",0))],
              key=lambda x: order.index(x["d"]) if x["d"] in order else 7)
print(f"{'Day':<10} {'Impr':>6} {'Clk':>5} {'Conv':>4} {'Cost ₹':>7}")
for d in dows:
    print(f"{d['d']:<10} {d['impr']:>6} {d['clk']:>5} {d['conv']:>4.0f} {d['cost']:>7.0f}")


# Pincodes
section("7. PINCODE PERF — TOP 20")
q = f"""SELECT campaign.id, segments.geo_target_postal_code,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM user_location_view WHERE campaign.id = {CAMP_ID} AND {DR}"""
pin_rows = [{"gid":r["segments"]["geoTargetPostalCode"].split("/")[-1],
             "impr":int(r["metrics"].get("impressions",0)),
             "clk":int(r["metrics"].get("clicks",0)),
             "cost":int(r["metrics"].get("costMicros",0))/1e6,
             "conv":float(r["metrics"].get("conversions",0))}
            for r in google_gaql(cfg, q) if int(r["metrics"].get("impressions",0))]
ids = list(set(r["gid"] for r in pin_rows))
name_map = {}
for i in range(0, len(ids), 10):
    chunk = ids[i:i+10]
    in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
    rq = f"""SELECT geo_target_constant.id, geo_target_constant.name
            FROM geo_target_constant
            WHERE geo_target_constant.resource_name IN ({in_clause})"""
    for r in google_gaql(cfg, rq):
        name_map[str(r["geoTargetConstant"]["id"])] = r["geoTargetConstant"].get("name","")
for r in pin_rows:
    r["pin"] = name_map.get(r["gid"], r["gid"])
pin_rows.sort(key=lambda x: x["cost"], reverse=True)
print(f"{'Pin':<8} {'Impr':>5} {'Clk':>5} {'Conv':>4} {'Cost ₹':>7}")
for r in pin_rows[:20]:
    print(f"{r['pin']:<8} {r['impr']:>5} {r['clk']:>5} {r['conv']:>4.0f} {r['cost']:>7.0f}")
print(f"\nTotal pincodes seen: {len(pin_rows)}")
zero_conv = [r for r in pin_rows if r["conv"]==0 and r["clk"]>=3]
print(f"Zero-conv pincodes (≥3 clicks): {len(zero_conv)}, ₹{sum(r['cost'] for r in zero_conv):.0f} wasted")


# Age
section("8. AGE")
q = f"""SELECT ad_group_criterion.age_range.type, ad_group_criterion.bid_modifier,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM age_range_view
        WHERE campaign.id = {CAMP_ID} AND {DR}"""
age_agg = {}
for r in google_gaql(cfg, q):
    age = r["adGroupCriterion"]["ageRange"]["type"]
    if age not in age_agg:
        age_agg[age] = {"bm": r["adGroupCriterion"].get("bidModifier",1.0),
                        "clk":0,"impr":0,"cost":0,"conv":0}
    m = r.get("metrics",{})
    age_agg[age]["clk"]   += int(m.get("clicks",0))
    age_agg[age]["impr"]  += int(m.get("impressions",0))
    age_agg[age]["cost"]  += int(m.get("costMicros",0))/1e6
    age_agg[age]["conv"]  += float(m.get("conversions",0))
print(f"{'Age':<10} {'Mod':>5} {'Impr':>6} {'Clk':>5} {'Conv':>4} {'Cost ₹':>7}")
for a in ["AGE_RANGE_18_24","AGE_RANGE_25_34","AGE_RANGE_35_44","AGE_RANGE_45_54","AGE_RANGE_55_64","AGE_RANGE_65_UP","AGE_RANGE_UNDETERMINED"]:
    if a not in age_agg: continue
    v = age_agg[a]
    bm = f"×{v['bm']:.2f}" if v['bm'] != 1 else "—"
    print(f"{a.replace('AGE_RANGE_',''):<10} {bm:>5} {v['impr']:>6} {v['clk']:>5} {v['conv']:>4.0f} {v['cost']:>7.0f}")
