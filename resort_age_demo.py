#!/usr/bin/env python3
"""Resort campaign 21740834372 — age + gender demographic performance.
Identifies age groups that click but don't convert (waste segments)."""
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
cfg = load_config()


def fmt_age(a):
    m = {
        "AGE_RANGE_18_24":"18-24",
        "AGE_RANGE_25_34":"25-34",
        "AGE_RANGE_35_44":"35-44",
        "AGE_RANGE_45_54":"45-54",
        "AGE_RANGE_55_64":"55-64",
        "AGE_RANGE_65_UP":"65+",
        "AGE_RANGE_UNDETERMINED":"Unknown",
    }
    return m.get(a, a)


def report_window(label, days_clause):
    print(f"\n{'='*80}")
    print(f"RESORT CAMPAIGN — AGE BREAKDOWN  ({label})")
    print(f"{'='*80}")

    # AGE
    q = f"""SELECT ad_group_criterion.age_range.type,
                   ad_group_criterion.bid_modifier,
                   metrics.clicks, metrics.impressions, metrics.cost_micros,
                   metrics.conversions, metrics.conversions_value
            FROM age_range_view
            WHERE campaign.id = {CAMP_ID}
              AND segments.date DURING {days_clause}"""
    rows = []
    for r in google_gaql(cfg, q):
        m = r.get("metrics", {})
        clicks = int(m.get("clicks", 0))
        impr = int(m.get("impressions", 0))
        cost = int(m.get("costMicros", 0)) / 1e6
        conv = float(m.get("conversions", 0))
        rows.append({
            "age": fmt_age(r["adGroupCriterion"]["ageRange"]["type"]),
            "bm": r["adGroupCriterion"].get("bidModifier", 1.0),
            "clicks": clicks,
            "impr": impr,
            "cost": cost,
            "conv": conv,
            "ctr": (clicks/impr*100) if impr else 0,
            "cvr": (conv/clicks*100) if clicks else 0,
            "cpa": (cost/conv) if conv else 0,
        })
    # aggregate by age (multiple ad groups -> sum)
    agg = {}
    for r in rows:
        a = r["age"]
        if a not in agg:
            agg[a] = {"age": a, "bm": r["bm"], "clicks":0, "impr":0, "cost":0, "conv":0}
        agg[a]["clicks"] += r["clicks"]
        agg[a]["impr"]   += r["impr"]
        agg[a]["cost"]   += r["cost"]
        agg[a]["conv"]   += r["conv"]
    out = list(agg.values())
    for r in out:
        r["ctr"] = (r["clicks"]/r["impr"]*100) if r["impr"] else 0
        r["cvr"] = (r["conv"]/r["clicks"]*100) if r["clicks"] else 0
        r["cpa"] = (r["cost"]/r["conv"]) if r["conv"] else 0
    out.sort(key=lambda x: x["clicks"], reverse=True)

    tot_clk = sum(r["clicks"] for r in out)
    tot_conv = sum(r["conv"] for r in out)
    tot_cost = sum(r["cost"] for r in out)

    print(f"{'Age':<10} {'Mod':>6} {'Impr':>8} {'Clicks':>7} {'CTR':>6} {'Conv':>6} "
          f"{'CVR':>6} {'Cost ₹':>9} {'CPA ₹':>9} {'%Clicks':>8} {'Verdict'}")
    print("-" * 100)
    for r in out:
        bm = f"×{r['bm']:.2f}" if r["bm"] and r["bm"] != 1 else "—"
        verdict = ""
        if r["conv"] == 0 and r["clicks"] >= 50:
            verdict = "🚨 0 conv — CUT BID"
        elif r["clicks"] >= 50 and r["cvr"] < 5:
            verdict = "🟡 low CVR — reduce"
        elif r["cvr"] >= 15 and r["clicks"] >= 20:
            verdict = "🟢 strong — boost bid"
        elif r["clicks"] < 20:
            verdict = "—"
        pct_clicks = (r["clicks"]/tot_clk*100) if tot_clk else 0
        cpa_str = f"{r['cpa']:.0f}" if r["conv"] else "—"
        print(f"{r['age']:<10} {bm:>6} {r['impr']:>8} {r['clicks']:>7} "
              f"{r['ctr']:>5.1f}% {r['conv']:>6.0f} {r['cvr']:>5.1f}% "
              f"{r['cost']:>9.0f} {cpa_str:>9} {pct_clicks:>7.1f}% {verdict}")
    print("-" * 100)
    print(f"{'TOTAL':<10} {'':>6} {sum(r['impr'] for r in out):>8} {tot_clk:>7} "
          f"{(tot_clk/sum(r['impr'] for r in out)*100 if sum(r['impr'] for r in out) else 0):>5.1f}% "
          f"{tot_conv:>6.0f} {(tot_conv/tot_clk*100 if tot_clk else 0):>5.1f}% "
          f"{tot_cost:>9.0f} {(tot_cost/tot_conv if tot_conv else 0):>9.0f}")

    # GENDER
    print(f"\n--- GENDER ({label}) ---")
    qg = f"""SELECT ad_group_criterion.gender.type,
                   ad_group_criterion.bid_modifier,
                   metrics.clicks, metrics.impressions, metrics.cost_micros,
                   metrics.conversions
            FROM gender_view
            WHERE campaign.id = {CAMP_ID}
              AND segments.date DURING {days_clause}"""
    g_agg = {}
    for r in google_gaql(cfg, qg):
        m = r.get("metrics", {})
        gen = r["adGroupCriterion"]["gender"]["type"].replace("GENDER_", "").replace("UNDETERMINED","Unknown")
        if gen not in g_agg:
            g_agg[gen] = {"gen": gen, "bm": r["adGroupCriterion"].get("bidModifier", 1.0),
                          "clicks":0, "impr":0, "cost":0, "conv":0}
        g_agg[gen]["clicks"] += int(m.get("clicks", 0))
        g_agg[gen]["impr"]   += int(m.get("impressions", 0))
        g_agg[gen]["cost"]   += int(m.get("costMicros", 0)) / 1e6
        g_agg[gen]["conv"]   += float(m.get("conversions", 0))
    print(f"{'Gender':<10} {'Mod':>6} {'Impr':>8} {'Clicks':>7} {'CTR':>6} {'Conv':>6} "
          f"{'CVR':>6} {'Cost ₹':>9} {'CPA ₹':>9}")
    for r in g_agg.values():
        bm = f"×{r['bm']:.2f}" if r["bm"] and r["bm"] != 1 else "—"
        ctr = (r["clicks"]/r["impr"]*100) if r["impr"] else 0
        cvr = (r["conv"]/r["clicks"]*100) if r["clicks"] else 0
        cpa = (r["cost"]/r["conv"]) if r["conv"] else 0
        cpa_str = f"{cpa:.0f}" if r["conv"] else "—"
        print(f"{r['gen']:<10} {bm:>6} {r['impr']:>8} {r['clicks']:>7} "
              f"{ctr:>5.1f}% {r['conv']:>6.0f} {cvr:>5.1f}% "
              f"{r['cost']:>9.0f} {cpa_str:>9}")


# Two windows so we can see if patterns are stable
report_window("LAST 30 DAYS", "LAST_30_DAYS")
report_window("LAST 7 DAYS",  "LAST_7_DAYS")
