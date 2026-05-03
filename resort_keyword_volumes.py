#!/usr/bin/env python3
"""Resort keywords — Google Ads Keyword Planner (Keyword Research) volumes.
Pulls 12-month avg + month-by-month + Bangalore-specific volume."""
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
CAMP_ID = "21740834372"

GEO_INDIA = "geoTargetConstants/2356"
GEO_BANGALORE = "geoTargetConstants/1007752"
GEO_KARNATAKA = "geoTargetConstants/20174"  # Karnataka state

cfg = load_config()
cl = _get_google_ads_client(cfg)


def get_kw_list():
    q = f"""SELECT ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type
            FROM keyword_view
            WHERE campaign.id = {CAMP_ID}
              AND ad_group_criterion.status = 'ENABLED'"""
    seen = set()
    for r in google_gaql(cfg, q):
        kw = r["adGroupCriterion"].get("keyword", {})
        t = kw.get("text", "")
        if t and t not in seen:
            seen.add(t)
    return sorted(seen)


def fetch_volumes(keyword_texts, geo_constant, geo_label):
    svc = cl.get_service("KeywordPlanIdeaService")
    req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = CUSTOMER_ID
    req.language = "languageConstants/1000"
    req.geo_target_constants.append(geo_constant)
    req.include_adult_keywords = False
    req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    req.keywords.extend(keyword_texts)
    try:
        resp = svc.generate_keyword_historical_metrics(request=req)
    except Exception as e:
        print(f"[ERR] {geo_label}: {str(e)[:300]}")
        return {}
    out = {}
    for r in resp.results:
        m = r.keyword_metrics
        # 12-month monthly breakdown
        months = []
        for ms in (m.monthly_search_volumes or []):
            months.append({
                "year": ms.year,
                "month": ms.month,  # MonthOfYearEnum (1=JAN..)
                "searches": getattr(ms, "monthly_searches", 0) or 0,
            })
        out[r.text.lower()] = {
            "avg_monthly": getattr(m, "avg_monthly_searches", 0) or 0,
            "comp": str(m.competition).split(".")[-1] if m.competition else "—",
            "low": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
            "high": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
            "monthly": months,
        }
    return out


def month_name(m):
    # MonthOfYearEnum: 0=UNSPECIFIED, 1=JAN..12=DEC; some clients return 2..13 indexing
    names = ["?","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if isinstance(m, int) and 1 <= m <= 12:
        return names[m]
    s = str(m).split(".")[-1]
    return s[:3].title()


def main():
    keywords = get_kw_list()
    print(f"=== Pulling Keyword Planner volumes for {len(keywords)} resort keywords ===\n")

    print("Geo: Bangalore + Karnataka + India (3 separate Keyword Planner calls)\n")
    blr = fetch_volumes(keywords, GEO_BANGALORE, "Bangalore")
    kar = fetch_volumes(keywords, GEO_KARNATAKA, "Karnataka")
    ind = fetch_volumes(keywords, GEO_INDIA, "India")

    rows = []
    for k in keywords:
        kl = k.lower()
        b = blr.get(kl, {})
        ka = kar.get(kl, {})
        i = ind.get(kl, {})
        rows.append({
            "kw": k,
            "blr": b.get("avg_monthly", 0),
            "kar": ka.get("avg_monthly", 0),
            "ind": i.get("avg_monthly", 0),
            "comp": i.get("comp", "—"),
            "low": i.get("low", 0),
            "high": i.get("high", 0),
            "monthly_ind": i.get("monthly", []),
        })

    # sort by Bangalore volume desc, then India
    rows.sort(key=lambda r: (r["blr"], r["ind"]), reverse=True)

    print(f"{'Keyword':<42} {'BLR':>7} {'KAR':>8} {'IND':>9} {'Comp':<7} {'CPC ₹':<10}")
    print("-" * 90)
    for r in rows:
        print(f"{r['kw'][:41]:<42} {r['blr']:>7,} {r['kar']:>8,} {r['ind']:>9,} "
              f"{r['comp']:<7} {r['low']:.0f}-{r['high']:.0f}")

    # 12-month trend for top keywords
    print("\n=== Last-12-month India trend (top 10 by India volume) ===\n")
    top_by_ind = sorted(rows, key=lambda r: r["ind"], reverse=True)[:10]
    for r in top_by_ind:
        if not r["monthly_ind"]:
            continue
        trend = ""
        for m in r["monthly_ind"]:
            mname = month_name(m["month"])
            yy = str(m["year"])[-2:]
            trend += f"{mname}{yy}:{m['searches']:>6,}  "
        print(f"  {r['kw'][:38]:<38}")
        print(f"    {trend}")
        print()


if __name__ == "__main__":
    main()
