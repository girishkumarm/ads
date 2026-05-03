#!/usr/bin/env python3
"""Resort campaign — full April 2026 efficiency audit.
Goal: find waste + identify low-CPA scaling opportunities + high-CPA cuts."""
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

CAMP_ID = "21740834372"
DATE_RANGE = "segments.date BETWEEN '2026-04-01' AND '2026-04-30'"
cfg = load_config()


def aggregate_metrics(rows):
    clk = sum(r.get("clicks",0) for r in rows)
    impr = sum(r.get("impressions",0) for r in rows)
    cost = sum(r.get("cost_micros",0) for r in rows)/1e6
    conv = sum(r.get("conversions",0) for r in rows)
    return {"clicks":clk,"impressions":impr,"cost":cost,"conversions":conv,
            "ctr": clk/impr*100 if impr else 0,
            "cvr": conv/clk*100 if clk else 0,
            "cpa": cost/conv if conv else 0,
            "cpc": cost/clk if clk else 0}


def section(title):
    print(f"\n{'='*80}\n{title}\n{'='*80}")


# ─────────────────────────────────────────────────
# 1. CAMPAIGN OVERVIEW
# ─────────────────────────────────────────────────
section("1. APRIL 2026 — CAMPAIGN TOTAL")
q = f"""SELECT metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions, metrics.average_cpc
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
totals = []
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    totals.append({
        "clicks": int(m.get("clicks",0)),
        "impressions": int(m.get("impressions",0)),
        "cost_micros": int(m.get("costMicros",0)),
        "conversions": float(m.get("conversions",0)),
    })
t = aggregate_metrics(totals)
print(f"  Impressions  : {t['impressions']:,}")
print(f"  Clicks       : {t['clicks']:,}  CTR {t['ctr']:.1f}%")
print(f"  Conversions  : {t['conversions']:.0f}  CVR {t['cvr']:.2f}%")
print(f"  Cost         : ₹{t['cost']:,.0f}")
print(f"  Avg CPC      : ₹{t['cpc']:.0f}")
print(f"  CPA          : ₹{t['cpa']:.0f}")


# ─────────────────────────────────────────────────
# 2. KEYWORD-LEVEL CPA — winners + losers
# ─────────────────────────────────────────────────
section("2. KEYWORDS — APRIL 2026 (sorted by spend)")
q = f"""SELECT ad_group.name,
               ad_group_criterion.criterion_id,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.negative,
               ad_group_criterion.quality_info.quality_score,
               metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
kw = []
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"): continue
    k = c.get("keyword", {})
    m = r.get("metrics", {})
    clk = int(m.get("clicks",0))
    impr = int(m.get("impressions",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    if impr == 0: continue
    kw.append({
        "ag": r["adGroup"]["name"],
        "text": k.get("text",""),
        "match": k.get("matchType",""),
        "qs": c.get("qualityInfo",{}).get("qualityScore"),
        "clicks": clk, "impr": impr, "cost": cost, "conv": conv,
        "cvr": conv/clk*100 if clk else 0,
        "cpa": cost/conv if conv else 0,
    })

# aggregate same kw across multiple AGs
agg = {}
for k in kw:
    key = (k["text"], k["match"])
    if key not in agg:
        agg[key] = {"text":k["text"],"match":k["match"],"qs":k["qs"],
                    "clicks":0,"impr":0,"cost":0,"conv":0,"ags":set()}
    agg[key]["clicks"] += k["clicks"]
    agg[key]["impr"]   += k["impr"]
    agg[key]["cost"]   += k["cost"]
    agg[key]["conv"]   += k["conv"]
    agg[key]["ags"].add(k["ag"])
    if k["qs"]: agg[key]["qs"] = k["qs"]
kws = []
for k in agg.values():
    k["cvr"] = k["conv"]/k["clicks"]*100 if k["clicks"] else 0
    k["cpa"] = k["cost"]/k["conv"] if k["conv"] else 0
    kws.append(k)
kws.sort(key=lambda x: x["cost"], reverse=True)

print(f"{'Keyword':<40} {'Match':<7} {'QS':>3} {'Impr':>6} {'Clk':>5} "
      f"{'Conv':>5} {'Cost ₹':>7} {'CPA ₹':>7} {'CVR':>6} {'Verdict'}")
print("-"*120)
for k in kws[:40]:
    qs = str(k["qs"]) if k["qs"] is not None else "-"
    cpa = f"{k['cpa']:.0f}" if k["conv"] else "—"
    verdict = ""
    avg_cpa = t["cpa"]
    if k["clicks"] >= 10 and k["conv"] == 0:
        verdict = f"🚨 0 conv ₹{k['cost']:.0f} wasted"
    elif k["conv"] >= 3 and k["cpa"] < avg_cpa * 0.7:
        verdict = "🟢 SCALE — low CPA"
    elif k["conv"] >= 3 and k["cpa"] > avg_cpa * 1.5:
        verdict = "🟡 high CPA — reduce bid"
    elif k["clicks"] >= 5 and k["conv"] == 0:
        verdict = "🟡 watch — 0 conv"
    print(f"{k['text'][:39]:<40} {k['match']:<7} {qs:>3} {k['impr']:>6} "
          f"{k['clicks']:>5} {k['conv']:>5.0f} {k['cost']:>7.0f} {cpa:>7} "
          f"{k['cvr']:>5.1f}% {verdict}")

# Summary buckets
high_cpa = [k for k in kws if k["conv"]>=3 and k["cpa"]>t["cpa"]*1.5]
low_cpa  = [k for k in kws if k["conv"]>=3 and k["cpa"]<t["cpa"]*0.7]
zero_conv = [k for k in kws if k["clicks"]>=10 and k["conv"]==0]

print(f"\n=== Keyword waste/opportunity buckets ===")
print(f"  🚨 ZERO CONV (≥10 clicks, no conversions) : {len(zero_conv)} kw  — ₹{sum(k['cost'] for k in zero_conv):.0f} wasted")
print(f"  🟡 HIGH CPA  (>1.5× campaign avg ₹{t['cpa']:.0f}) : {len(high_cpa)} kw  — ₹{sum(k['cost'] for k in high_cpa):.0f} spent")
print(f"  🟢 LOW CPA   (<0.7× campaign avg)         : {len(low_cpa)} kw  — ₹{sum(k['cost'] for k in low_cpa):.0f} spent  ★ scale these")


# ─────────────────────────────────────────────────
# 3. SEARCH TERMS — what queries actually triggered ads
# ─────────────────────────────────────────────────
section("3. SEARCH TERMS — APRIL — wasteful searches that triggered ads")
q = f"""SELECT search_term_view.search_term,
               search_term_view.status,
               metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
terms = []
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    clk = int(m.get("clicks",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    if clk == 0: continue
    terms.append({
        "term": r["searchTermView"]["searchTerm"],
        "status": r["searchTermView"].get("status",""),
        "clicks": clk, "cost": cost, "conv": conv,
        "cpa": cost/conv if conv else 0,
    })
# top wasters: highest cost with 0 conv
zero_conv_terms = sorted([t for t in terms if t["conv"]==0 and t["clicks"]>=2],
                         key=lambda x: x["cost"], reverse=True)[:25]
print(f"Top 25 search terms with 0 conversions but ≥2 clicks (April):\n")
print(f"{'Search term':<55} {'Clk':>4} {'Cost ₹':>7} {'Status':<25}")
print("-"*100)
total_waste = 0
for tt in zero_conv_terms:
    total_waste += tt["cost"]
    print(f"{tt['term'][:54]:<55} {tt['clicks']:>4} {tt['cost']:>7.0f} {tt['status']:<25}")
print(f"\n  TOTAL WASTE on these 25 search terms: ₹{total_waste:.0f}")


# ─────────────────────────────────────────────────
# 4. DEVICE BREAKDOWN
# ─────────────────────────────────────────────────
section("4. DEVICE — APRIL")
q = f"""SELECT segments.device,
               metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
print(f"{'Device':<12} {'Impr':>7} {'Clicks':>7} {'CTR':>6} {'Conv':>5} {'CVR':>6} {'Cost ₹':>9} {'CPA ₹':>9}")
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    clk = int(m.get("clicks",0))
    impr = int(m.get("impressions",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    if not impr: continue
    ctr = clk/impr*100
    cvr = conv/clk*100 if clk else 0
    cpa = cost/conv if conv else 0
    cpa_str = f"{cpa:.0f}" if conv else "—"
    print(f"{r['segments']['device']:<12} {impr:>7} {clk:>7} {ctr:>5.1f}% "
          f"{conv:>5.0f} {cvr:>5.1f}% {cost:>9.0f} {cpa_str:>9}")


# ─────────────────────────────────────────────────
# 5. HOUR-OF-DAY
# ─────────────────────────────────────────────────
section("5. HOUR-OF-DAY — APRIL (top spenders by hour)")
q = f"""SELECT segments.hour,
               metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
hours = []
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    clk = int(m.get("clicks",0))
    impr = int(m.get("impressions",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    if not impr: continue
    hours.append({"h":r["segments"]["hour"],"impr":impr,"clk":clk,"cost":cost,"conv":conv,
                  "cpa": cost/conv if conv else 0,
                  "cvr": conv/clk*100 if clk else 0})
hours.sort(key=lambda x: x["h"])
print(f"{'Hr':<4} {'Impr':>6} {'Clk':>5} {'CTR':>6} {'Conv':>5} {'CVR':>6} {'Cost ₹':>8} {'CPA ₹':>8}")
for h in hours:
    ctr = h["clk"]/h["impr"]*100
    cpa = f"{h['cpa']:.0f}" if h["conv"] else "—"
    print(f"{h['h']:>2}h  {h['impr']:>6} {h['clk']:>5} {ctr:>5.1f}% {h['conv']:>5.0f} {h['cvr']:>5.1f}% {h['cost']:>8.0f} {cpa:>8}")


# ─────────────────────────────────────────────────
# 6. DAY-OF-WEEK
# ─────────────────────────────────────────────────
section("6. DAY-OF-WEEK — APRIL")
q = f"""SELECT segments.day_of_week,
               metrics.clicks, metrics.impressions, metrics.cost_micros,
               metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID} AND {DATE_RANGE}"""
dows = []
for r in google_gaql(cfg, q):
    m = r.get("metrics", {})
    clk = int(m.get("clicks",0))
    impr = int(m.get("impressions",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    if not impr: continue
    dows.append({"d":r["segments"]["dayOfWeek"],"impr":impr,"clk":clk,"cost":cost,"conv":conv,
                 "cpa":cost/conv if conv else 0,
                 "cvr":conv/clk*100 if clk else 0})
order = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]
dows.sort(key=lambda x: order.index(x["d"]) if x["d"] in order else 7)
print(f"{'Day':<10} {'Impr':>7} {'Clk':>5} {'CTR':>6} {'Conv':>5} {'CVR':>6} {'Cost ₹':>9} {'CPA ₹':>8}")
for d in dows:
    ctr = d["clk"]/d["impr"]*100
    cpa = f"{d['cpa']:.0f}" if d["conv"] else "—"
    print(f"{d['d']:<10} {d['impr']:>7} {d['clk']:>5} {ctr:>5.1f}% {d['conv']:>5.0f} {d['cvr']:>5.1f}% {d['cost']:>9.0f} {cpa:>8}")


# ─────────────────────────────────────────────────
# 7. MATCH-TYPE EFFICIENCY
# ─────────────────────────────────────────────────
section("7. MATCH TYPE — APRIL")
mt_agg = {}
for k in kws:
    if k["match"] not in mt_agg:
        mt_agg[k["match"]] = {"clicks":0,"impr":0,"cost":0,"conv":0,"count":0}
    mt_agg[k["match"]]["clicks"] += k["clicks"]
    mt_agg[k["match"]]["impr"]   += k["impr"]
    mt_agg[k["match"]]["cost"]   += k["cost"]
    mt_agg[k["match"]]["conv"]   += k["conv"]
    mt_agg[k["match"]]["count"]  += 1
print(f"{'Match':<8} {'#Kw':>4} {'Impr':>7} {'Clk':>6} {'Conv':>5} {'CVR':>6} {'Cost ₹':>8} {'CPA ₹':>8}")
for m, v in mt_agg.items():
    cvr = v["conv"]/v["clicks"]*100 if v["clicks"] else 0
    cpa = v["cost"]/v["conv"] if v["conv"] else 0
    cpa_str = f"{cpa:.0f}" if v["conv"] else "—"
    print(f"{m:<8} {v['count']:>4} {v['impr']:>7} {v['clicks']:>6} {v['conv']:>5.0f} {cvr:>5.1f}% {v['cost']:>8.0f} {cpa_str:>8}")
