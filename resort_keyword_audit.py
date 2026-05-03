#!/usr/bin/env python3
"""Resort campaign 21740834372 — full enabled keyword list + Google Ads search volumes
(KeywordPlanIdeaService / GenerateKeywordHistoricalMetrics).
Read-only audit. Resort authority = APPROVAL ONLY."""
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

cfg = load_config()
cl = _get_google_ads_client(cfg)


def list_enabled_keywords():
    q = f"""SELECT ad_group.id, ad_group.name,
                   ad_group_criterion.criterion_id,
                   ad_group_criterion.keyword.text,
                   ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status,
                   ad_group_criterion.quality_info.quality_score,
                   metrics.clicks, metrics.impressions, metrics.cost_micros,
                   metrics.conversions
            FROM keyword_view
            WHERE campaign.id = {CAMP_ID}
              AND ad_group_criterion.status = 'ENABLED'
              AND ad_group.status = 'ENABLED'
              AND segments.date DURING LAST_30_DAYS"""
    out = []
    for r in google_gaql(cfg, q):
        kw = r["adGroupCriterion"].get("keyword", {})
        m = r.get("metrics", {})
        qi = r["adGroupCriterion"].get("qualityInfo", {})
        out.append({
            "ag": r["adGroup"]["name"],
            "text": kw.get("text", ""),
            "match": kw.get("matchType", ""),
            "qs": qi.get("qualityScore"),
            "clicks": int(m.get("clicks", 0)),
            "impr": int(m.get("impressions", 0)),
            "cost": int(m.get("costMicros", 0)) / 1e6,
            "conv": float(m.get("conversions", 0)),
        })
    # dedupe (one row per kw_text+match — sum metrics if same kw across ad groups)
    agg = {}
    for o in out:
        k = (o["text"], o["match"])
        if k not in agg:
            agg[k] = {"text": o["text"], "match": o["match"], "ags": [],
                      "qs": o["qs"], "clicks": 0, "impr": 0, "cost": 0.0, "conv": 0.0}
        agg[k]["ags"].append(o["ag"])
        agg[k]["clicks"] += o["clicks"]
        agg[k]["impr"] += o["impr"]
        agg[k]["cost"] += o["cost"]
        agg[k]["conv"] += o["conv"]
        if o["qs"]: agg[k]["qs"] = o["qs"]
    return list(agg.values())


def get_historical_volumes(keyword_texts):
    """Use KeywordPlanIdeaService.generateKeywordHistoricalMetrics for India / English."""
    svc = cl.get_service("KeywordPlanIdeaService")
    # India = 2356 (geo target constant), Bangalore = 1007752
    geo_constants = ["geoTargetConstants/2356"]  # all-India for breadth
    req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
    req.customer_id = CUSTOMER_ID
    req.language = "languageConstants/1000"  # English
    req.geo_target_constants.extend(geo_constants)
    req.include_adult_keywords = False
    req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    # API max 10,000 keywords per request
    req.keywords.extend(keyword_texts[:10000])
    try:
        resp = svc.generate_keyword_historical_metrics(request=req)
    except Exception as e:
        print(f"[ERR] historical metrics failed: {str(e)[:500]}")
        return {}
    vol_map = {}
    for r in resp.results:
        text = r.text.lower()
        m = r.keyword_metrics
        vol_map[text] = {
            "avg_monthly": getattr(m, "avg_monthly_searches", 0) or 0,
            "competition": str(m.competition).split(".")[-1] if m.competition else "UNKNOWN",
            "comp_index": getattr(m, "competition_index", None),
            "low_top": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
            "high_top": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
        }
        # also map close_variants
        for v in r.close_variants:
            vol_map.setdefault(v.lower(), vol_map[text])
    return vol_map


def main():
    kws = list_enabled_keywords()
    print(f"=== Resort campaign {CAMP_ID} — {len(kws)} unique enabled keywords (last 30d perf) ===\n")

    texts = [k["text"] for k in kws]
    print(f"Fetching Google search volumes for {len(texts)} keywords (India, English)...\n")
    vol = get_historical_volumes(texts)

    # merge
    for k in kws:
        v = vol.get(k["text"].lower(), {})
        k["monthly"] = v.get("avg_monthly", 0)
        k["comp"] = v.get("competition", "—")
        k["low_top"] = v.get("low_top", 0)
        k["high_top"] = v.get("high_top", 0)

    # sort by impressions desc
    kws.sort(key=lambda x: x["impr"], reverse=True)

    hdr = f"{'Keyword':<40} {'Match':<8} {'QS':>3} {'Clk':>5} {'Impr':>6} {'Conv':>5} {'Cost':>7} {'MoSearch':>10} {'Comp':<10} {'CPC₹L-H':<14}"
    print(hdr)
    print("-" * len(hdr))
    for k in kws:
        qs = str(k["qs"]) if k["qs"] is not None else "-"
        cpc = f"{k['low_top']:.0f}-{k['high_top']:.0f}" if k.get("high_top") else "—"
        print(f"{k['text'][:39]:<40} {k['match']:<8} {qs:>3} "
              f"{k['clicks']:>5} {k['impr']:>6} {k['conv']:>5.0f} {k['cost']:>7.0f} "
              f"{k['monthly']:>10,} {k['comp']:<10} {cpc:<14}")

    # summary buckets
    print("\n=== Summary ===")
    high_vol = [k for k in kws if k["monthly"] >= 1000]
    mid_vol = [k for k in kws if 100 <= k["monthly"] < 1000]
    low_vol = [k for k in kws if 0 < k["monthly"] < 100]
    no_vol = [k for k in kws if k["monthly"] == 0]
    print(f"  ≥1,000 monthly searches : {len(high_vol)} kw  →  {sum(k['impr'] for k in high_vol)} impr last 30d")
    print(f"   100-999 monthly searches: {len(mid_vol)} kw  →  {sum(k['impr'] for k in mid_vol)} impr last 30d")
    print(f"   1-99   monthly searches: {len(low_vol)} kw  →  {sum(k['impr'] for k in low_vol)} impr last 30d")
    print(f"   0      / unknown       : {len(no_vol)} kw  →  {sum(k['impr'] for k in no_vol)} impr last 30d")


if __name__ == "__main__":
    main()
