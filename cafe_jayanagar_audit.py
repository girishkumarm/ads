#!/usr/bin/env python3
"""Jayanagar Cafe Search 23778954613 — full April 2026 audit.
Goal: scale the ₹18-CPA winner. Find more keywords, hours, days, devices."""
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

CAMP_ID = "23778954613"
DR = "segments.date BETWEEN '2026-04-01' AND '2026-04-30'"
cfg = load_config()


def section(t):
    print(f"\n{'='*80}\n{t}\n{'='*80}")


# 1. Impression share (ARE WE LIMITED BY BIDS OR BUDGET?)
section("1. IMPRESSION SHARE — APRIL")
q = f"""SELECT metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share,
               metrics.search_top_impression_share,
               metrics.search_absolute_top_impression_share
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    print(f"  Search impression share          : {m.get('searchImpressionShare', 0)*100:.1f}%")
    print(f"  Lost to BUDGET                   : {m.get('searchBudgetLostImpressionShare', 0)*100:.1f}%")
    print(f"  Lost to RANK (bid/QS)            : {m.get('searchRankLostImpressionShare', 0)*100:.1f}%")
    print(f"  Top of page IS                   : {m.get('searchTopImpressionShare', 0)*100:.1f}%")
    print(f"  Absolute top of page IS          : {m.get('searchAbsoluteTopImpressionShare', 0)*100:.1f}%")
    break


# 2. Keywords
section("2. KEYWORDS — APRIL (sorted by spend)")
q = f"""SELECT ad_group.name,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.negative,
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
    impr = int(m.get("impressions",0))
    if impr == 0: continue
    key = (k.get("text",""), k.get("matchType",""))
    if key not in agg:
        agg[key] = {"text":k.get("text",""), "match":k.get("matchType",""),
                    "qs":c.get("qualityInfo",{}).get("qualityScore"),
                    "ag":r["adGroup"]["name"], "status":c.get("status",""),
                    "clicks":0,"impr":0,"cost":0,"conv":0}
    agg[key]["clicks"] += int(m.get("clicks",0))
    agg[key]["impr"]   += impr
    agg[key]["cost"]   += int(m.get("costMicros",0))/1e6
    agg[key]["conv"]   += float(m.get("conversions",0))
kws = sorted(agg.values(), key=lambda x: x["cost"], reverse=True)
print(f"{'Keyword':<35} {'Match':<7} {'QS':>3} {'Status':<8} {'Impr':>6} {'Clk':>5} {'Conv':>5} {'Cost ₹':>7} {'CPA ₹':>6} {'CVR':>6}")
for k in kws:
    qs = str(k["qs"]) if k["qs"] is not None else "-"
    cpa = f"{k['cost']/k['conv']:.0f}" if k["conv"] else "—"
    cvr = k["conv"]/k["clicks"]*100 if k["clicks"] else 0
    print(f"{k['text'][:34]:<35} {k['match']:<7} {qs:>3} {k['status']:<8} "
          f"{k['impr']:>6} {k['clicks']:>5} {k['conv']:>5.0f} {k['cost']:>7.0f} {cpa:>6} {cvr:>5.1f}%")


# 3. Search terms — what's actually triggering ads
section("3. SEARCH TERMS — APRIL (top by cost)")
q = f"""SELECT search_term_view.search_term, search_term_view.status,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {CAMP_ID} AND {DR}"""
terms = []
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    cost = int(m.get("costMicros",0))/1e6
    if cost == 0: continue
    terms.append({
        "term": r["searchTermView"]["searchTerm"],
        "status": r["searchTermView"].get("status",""),
        "clicks": int(m.get("clicks",0)),
        "impr": int(m.get("impressions",0)),
        "cost": cost,
        "conv": float(m.get("conversions",0)),
    })
terms.sort(key=lambda x: x["cost"], reverse=True)
print(f"{'Search term':<55} {'Clk':>4} {'Conv':>5} {'Cost ₹':>7} {'Status':<14}")
for t in terms[:30]:
    print(f"{t['term'][:54]:<55} {t['clicks']:>4} {t['conv']:>5.0f} {t['cost']:>7.0f} {t['status']:<14}")

# Wasters
zero_conv = [t for t in terms if t["conv"]==0 and t["clicks"]>=2]
print(f"\nTotal zero-conv search terms (≥2 clicks): {len(zero_conv)}")
print(f"Total zero-conv waste: ₹{sum(t['cost'] for t in zero_conv):.0f}")


# 4. Device
section("4. DEVICE — APRIL")
q = f"""SELECT segments.device, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
print(f"{'Device':<10} {'Impr':>6} {'Clk':>5} {'CTR':>6} {'Conv':>5} {'CVR':>6} {'Cost ₹':>7} {'CPA ₹':>6}")
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    clk = int(m.get("clicks",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    ctr = clk/impr*100 if impr else 0
    cvr = conv/clk*100 if clk else 0
    cpa = cost/conv if conv else 0
    cpa_str = f"{cpa:.0f}" if conv else "—"
    print(f"{r['segments']['device']:<10} {impr:>6} {clk:>5} {ctr:>5.1f}% "
          f"{conv:>5.0f} {cvr:>5.1f}% {cost:>7.0f} {cpa_str:>6}")


# 5. Hour-of-day
section("5. HOUR-OF-DAY — APRIL")
q = f"""SELECT segments.hour, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
hours = []
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    clk = int(m.get("clicks",0))
    conv = float(m.get("conversions",0))
    cost = int(m.get("costMicros",0))/1e6
    hours.append({"h":r["segments"]["hour"],"impr":impr,"clk":clk,"cost":cost,"conv":conv})
hours.sort(key=lambda x: x["h"])
print(f"{'Hr':<4} {'Impr':>5} {'Clk':>4} {'CTR':>5} {'Conv':>5} {'CVR':>6} {'Cost ₹':>7} {'CPA ₹':>6}")
for h in hours:
    cpa = f"{h['cost']/h['conv']:.0f}" if h["conv"] else "—"
    cvr = h["conv"]/h["clk"]*100 if h["clk"] else 0
    print(f"{h['h']:>2}h  {h['impr']:>5} {h['clk']:>4} {(h['clk']/h['impr']*100):>4.0f}% "
          f"{h['conv']:>5.0f} {cvr:>5.1f}% {h['cost']:>7.0f} {cpa:>6}")


# 6. Day of week
section("6. DAY-OF-WEEK — APRIL")
q = f"""SELECT segments.day_of_week, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DR}"""
order = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]
dows = []
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    dows.append({"d":r["segments"]["dayOfWeek"],"impr":impr,
                 "clk":int(m.get("clicks",0)),
                 "cost":int(m.get("costMicros",0))/1e6,
                 "conv":float(m.get("conversions",0))})
dows.sort(key=lambda x: order.index(x["d"]) if x["d"] in order else 7)
print(f"{'Day':<10} {'Impr':>6} {'Clk':>5} {'Conv':>5} {'CVR':>6} {'Cost ₹':>7} {'CPA ₹':>6}")
for d in dows:
    cpa = f"{d['cost']/d['conv']:.0f}" if d["conv"] else "—"
    cvr = d["conv"]/d["clk"]*100 if d["clk"] else 0
    print(f"{d['d']:<10} {d['impr']:>6} {d['clk']:>5} {d['conv']:>5.0f} {cvr:>5.1f}% {d['cost']:>7.0f} {cpa:>6}")


# 7. Pincode (location)
section("7. PINCODE PERF — APRIL")
q = f"""SELECT campaign.id, segments.geo_target_postal_code,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM user_location_view WHERE campaign.id = {CAMP_ID} AND {DR}"""
pin_rows = []
for r in google_gaql(cfg, q):
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    pin_rows.append({"gid":r["segments"]["geoTargetPostalCode"].split("/")[-1],
                     "impr":impr,"clk":int(m.get("clicks",0)),
                     "cost":int(m.get("costMicros",0))/1e6,
                     "conv":float(m.get("conversions",0))})
# resolve names
ids = list(set(r["gid"] for r in pin_rows))
name_map = {}
for i in range(0, len(ids), 10):
    chunk = ids[i:i+10]
    in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
    rq = f"""SELECT geo_target_constant.id, geo_target_constant.name
            FROM geo_target_constant
            WHERE geo_target_constant.resource_name IN ({in_clause})"""
    for r in google_gaql(cfg, rq):
        gtc = r["geoTargetConstant"]
        name_map[str(gtc["id"])] = gtc.get("name","")
for r in pin_rows:
    r["pin"] = name_map.get(r["gid"], r["gid"])
pin_rows.sort(key=lambda x: x["cost"], reverse=True)
print(f"{'Pin':<8} {'Impr':>5} {'Clk':>4} {'Conv':>4} {'Cost ₹':>6} {'CPA ₹':>6}")
for r in pin_rows[:20]:
    cpa = f"{r['cost']/r['conv']:.0f}" if r["conv"] else "—"
    print(f"{r['pin']:<8} {r['impr']:>5} {r['clk']:>4} {r['conv']:>4.0f} {r['cost']:>6.0f} {cpa:>6}")


# 8. Age
section("8. AGE — APRIL")
q = f"""SELECT ad_group_criterion.age_range.type,
               ad_group_criterion.bid_modifier,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM age_range_view
        WHERE campaign.id = {CAMP_ID} AND {DR}"""
age_agg = {}
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    age = c["ageRange"]["type"]
    if age not in age_agg:
        age_agg[age] = {"bm": c.get("bidModifier",1.0),"clk":0,"impr":0,"cost":0,"conv":0}
    m = r.get("metrics",{})
    age_agg[age]["clk"]   += int(m.get("clicks",0))
    age_agg[age]["impr"]  += int(m.get("impressions",0))
    age_agg[age]["cost"]  += int(m.get("costMicros",0))/1e6
    age_agg[age]["conv"]  += float(m.get("conversions",0))
print(f"{'Age':<10} {'Mod':>5} {'Impr':>6} {'Clk':>5} {'Conv':>5} {'CVR':>6} {'Cost ₹':>7} {'CPA ₹':>6}")
order_age = ["AGE_RANGE_18_24","AGE_RANGE_25_34","AGE_RANGE_35_44","AGE_RANGE_45_54","AGE_RANGE_55_64","AGE_RANGE_65_UP","AGE_RANGE_UNDETERMINED"]
for a in order_age:
    if a not in age_agg: continue
    v = age_agg[a]
    cvr = v["conv"]/v["clk"]*100 if v["clk"] else 0
    cpa = f"{v['cost']/v['conv']:.0f}" if v["conv"] else "—"
    bm = f"×{v['bm']:.2f}" if v['bm'] != 1 else "—"
    print(f"{a.replace('AGE_RANGE_',''):<10} {bm:>5} {v['impr']:>6} {v['clk']:>5} {v['conv']:>5.0f} "
          f"{cvr:>5.1f}% {v['cost']:>7.0f} {cpa:>6}")
