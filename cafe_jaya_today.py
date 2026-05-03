#!/usr/bin/env python3
"""Jayanagar Cafe Search 23778954613 — today's performance + impression-loss diagnosis."""
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
cfg = load_config()


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# 1. Today + last 7 days totals
section("1. JAYANAGAR — RECENT PERFORMANCE")
for label, dr in [("TODAY","TODAY"), ("YESTERDAY","YESTERDAY"), ("LAST 7 DAYS","LAST_7_DAYS"), ("LAST 30 DAYS","LAST_30_DAYS")]:
    q = f"""SELECT metrics.clicks, metrics.impressions, metrics.cost_micros,
                   metrics.conversions, metrics.average_cpc,
                   metrics.search_impression_share,
                   metrics.search_budget_lost_impression_share,
                   metrics.search_rank_lost_impression_share,
                   metrics.search_top_impression_share
            FROM campaign WHERE campaign.id = {CAMP_ID}
              AND segments.date DURING {dr}"""
    rows = list(google_gaql(cfg, q))
    if not rows:
        print(f"  {label:<14} : no data")
        continue
    m = rows[0].get("metrics", {})
    impr = int(m.get("impressions",0))
    clk = int(m.get("clicks",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    cpa = cost/conv if conv else 0
    is_ = m.get("searchImpressionShare", 0)*100
    bud = m.get("searchBudgetLostImpressionShare", 0)*100
    rank = m.get("searchRankLostImpressionShare", 0)*100
    print(f"  {label:<14} | impr {impr:>5} | clk {clk:>4} | conv {conv:>4.0f} | "
          f"cost ₹{cost:>5.0f} | CPA ₹{cpa:>4.0f} | "
          f"IS {is_:>4.1f}% lost-bud {bud:>4.1f}% lost-rank {rank:>4.1f}%")


# 2. Today by hour
section("2. TODAY — BY HOUR")
q = f"""SELECT segments.hour, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING TODAY"""
hours = sorted([{"h":r["segments"]["hour"],
                 "impr":int(r["metrics"].get("impressions",0)),
                 "clk":int(r["metrics"].get("clicks",0)),
                 "cost":int(r["metrics"].get("costMicros",0))/1e6,
                 "conv":float(r["metrics"].get("conversions",0))}
                for r in google_gaql(cfg, q) if int(r["metrics"].get("impressions",0))],
               key=lambda x: x["h"])
if not hours:
    print("  No impressions today yet.")
else:
    print(f"  {'Hr':<4} {'Impr':>5} {'Clk':>4} {'Conv':>4} {'Cost ₹':>7}")
    for h in hours:
        print(f"  {h['h']:>2}h  {h['impr']:>5} {h['clk']:>4} {h['conv']:>4.0f} {h['cost']:>7.0f}")


# 3. Budget pacing — yesterday + today
section("3. BUDGET PACING")
q = f"""SELECT campaign_budget.amount_micros, campaign_budget.delivery_method,
               campaign_budget.recommended_budget_amount_micros,
               campaign_budget.has_recommended_budget
        FROM campaign_budget
        WHERE campaign_budget.id IN (
            SELECT campaign.campaign_budget FROM campaign WHERE campaign.id = {CAMP_ID}
        )"""
# simpler — get budget from campaign view
q2 = f"""SELECT campaign_budget.amount_micros, campaign_budget.delivery_method
         FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q2):
    cb = r.get("campaignBudget",{})
    amt = int(cb.get("amountMicros",0))/1e6
    print(f"  Daily budget   : ₹{amt:.0f}")
    print(f"  Delivery method: {cb.get('deliveryMethod','—')}")
    break


# 4. Per-day last 7 days (see trend)
section("4. LAST 7 DAYS — DAILY BREAKDOWN")
q = f"""SELECT segments.date, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions,
               metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_7_DAYS"""
rows = sorted([r for r in google_gaql(cfg, q)], key=lambda x: x["segments"]["date"])
print(f"  {'Date':<12} {'Impr':>5} {'Clk':>4} {'Conv':>4} {'Cost ₹':>6} {'IS%':>5} {'Bud%':>5} {'Rank%':>5}")
for r in rows:
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    is_ = m.get("searchImpressionShare", 0)*100
    bud = m.get("searchBudgetLostImpressionShare", 0)*100
    rnk = m.get("searchRankLostImpressionShare", 0)*100
    print(f"  {r['segments']['date']:<12} {impr:>5} {int(m.get('clicks',0)):>4} "
          f"{float(m.get('conversions',0)):>4.0f} "
          f"{int(m.get('costMicros',0))/1e6:>6.0f} "
          f"{is_:>4.1f}% {bud:>4.1f}% {rnk:>4.1f}%")


# 5. Today by keyword (see what's serving)
section("5. TODAY — BY KEYWORD (top 20 by impressions)")
q = f"""SELECT ad_group.name, ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.quality_info.quality_score,
               metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING TODAY"""
rows = []
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"): continue
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    rows.append({
        "text": c["keyword"]["text"],
        "match": c["keyword"]["matchType"],
        "qs": c.get("qualityInfo",{}).get("qualityScore"),
        "status": c.get("status",""),
        "impr": impr,
        "clk": int(m.get("clicks",0)),
        "conv": float(m.get("conversions",0)),
        "cost": int(m.get("costMicros",0))/1e6,
    })
rows.sort(key=lambda x: x["impr"], reverse=True)
if not rows:
    print("  No keyword data for today yet.")
else:
    print(f"  {'Keyword':<35} {'Match':<6} {'QS':>3} {'Status':<8} {'Impr':>5} {'Clk':>4} {'Conv':>4} {'Cost ₹':>6}")
    for r in rows[:20]:
        qs = str(r["qs"]) if r["qs"] is not None else "-"
        print(f"  {r['text'][:34]:<35} {r['match']:<6} {qs:>3} {r['status']:<8} "
              f"{r['impr']:>5} {r['clk']:>4} {r['conv']:>4.0f} {r['cost']:>6.0f}")


# 6. Today's search impression share by AG
section("6. CURRENT IMPRESSION-LOSS BREAKDOWN (LAST 7 DAYS BY AD GROUP)")
q = f"""SELECT ad_group.name, ad_group.id,
               metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share,
               metrics.impressions, metrics.clicks, metrics.cost_micros
        FROM ad_group
        WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_7_DAYS
          AND ad_group.status = 'ENABLED'"""
agg = {}
for r in google_gaql(cfg, q):
    aid = r["adGroup"]["id"]
    m = r.get("metrics",{})
    if aid not in agg:
        agg[aid] = {"name": r["adGroup"]["name"], "impr":0,"clk":0,"cost":0,
                    "is": m.get("searchImpressionShare",0),
                    "bud": m.get("searchBudgetLostImpressionShare",0),
                    "rank": m.get("searchRankLostImpressionShare",0)}
    agg[aid]["impr"] += int(m.get("impressions",0))
    agg[aid]["clk"] += int(m.get("clicks",0))
    agg[aid]["cost"] += int(m.get("costMicros",0))/1e6
print(f"  {'Ad Group':<40} {'Impr':>5} {'Clk':>4} {'Cost ₹':>7} {'IS%':>5} {'Bud%':>5} {'Rank%':>5}")
for a in sorted(agg.values(), key=lambda x: -x["impr"]):
    print(f"  {a['name'][:39]:<40} {a['impr']:>5} {a['clk']:>4} {a['cost']:>7.0f} "
          f"{a['is']*100:>4.1f}% {a['bud']*100:>4.1f}% {a['rank']*100:>4.1f}%")


# 7. Hour-of-day TODAY vs typical (last 30d)
section("7. TIME RIGHT NOW (server-side IST)")
import datetime
ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
print(f"  IST now: {ist_now.strftime('%Y-%m-%d %H:%M')}")
print(f"  Day of week: {ist_now.strftime('%A')}")
