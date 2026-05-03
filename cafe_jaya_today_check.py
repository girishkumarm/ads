#!/usr/bin/env python3
"""Quick check on Jayanagar cafe — last 7 days post-fix recovery."""
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

print("=== Jayanagar Cafe — daily trend last 14d ===")
q = f"""SELECT segments.date, metrics.clicks, metrics.impressions,
               metrics.cost_micros, metrics.conversions,
               metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_14_DAYS"""
rows = sorted([r for r in google_gaql(cfg, q)], key=lambda x: x["segments"]["date"])
print(f"  {'Date':<12} {'Impr':>5} {'Clk':>4} {'Conv':>4} {'CPA':>5} {'Cost':>5} {'IS%':>5} {'Bud%':>5} {'Rank%':>5}")
for r in rows:
    m = r.get("metrics",{})
    impr = int(m.get("impressions",0))
    if not impr: continue
    clk = int(m.get("clicks",0))
    cost = int(m.get("costMicros",0))/1e6
    conv = float(m.get("conversions",0))
    cpa = cost/conv if conv else 0
    is_ = m.get("searchImpressionShare", 0)*100
    bud = m.get("searchBudgetLostImpressionShare", 0)*100
    rnk = m.get("searchRankLostImpressionShare", 0)*100
    cpa_str = f"{cpa:.0f}" if conv else "-"
    print(f"  {r['segments']['date']:<12} {impr:>5} {clk:>4} {conv:>4.0f} {cpa_str:>5} {cost:>5.0f} {is_:>4.0f}% {bud:>4.0f}% {rnk:>4.0f}%")

# Conversion totals
print("\n=== Lifetime conversion data ===")
q = f"""SELECT metrics.conversions, metrics.cost_micros
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_30_DAYS"""
totals = list(google_gaql(cfg, q))
for r in totals:
    m = r.get("metrics",{})
    print(f"  Last 30d: {float(m.get('conversions',0)):.0f} conv, ₹{int(m.get('costMicros',0))/1e6:.0f} cost")
    break
