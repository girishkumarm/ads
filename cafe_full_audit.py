#!/usr/bin/env python3
"""BUS Cafe (Jayanagar + BTM) — full audit across both ad accounts.
Pulls all enabled campaigns and surface-level performance."""
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

cfg = load_config()
CAFE_CID = cfg["google_ads"]["cafe_customer_id"]
PRIMARY_CID = cfg["google_ads"]["customer_id"]


def list_campaigns(cid, label):
    print(f"\n{'='*85}")
    print(f"{label} (customer {cid})")
    print(f"{'='*85}")
    saved_cid = cfg["google_ads"]["customer_id"]
    cfg["google_ads"]["customer_id"] = cid
    try:
        q = """SELECT campaign.id, campaign.name, campaign.status,
                      campaign.advertising_channel_type,
                      campaign.bidding_strategy_type,
                      campaign_budget.amount_micros,
                      metrics.clicks, metrics.impressions, metrics.cost_micros,
                      metrics.conversions
               FROM campaign
               WHERE segments.date BETWEEN '2026-04-01' AND '2026-04-30'
                 AND campaign.status != 'REMOVED'"""
        camps = {}
        for r in google_gaql(cfg, q):
            cid_ = r["campaign"]["id"]
            if cid_ not in camps:
                camps[cid_] = {
                    "id": cid_, "name": r["campaign"]["name"],
                    "status": r["campaign"].get("status",""),
                    "type": r["campaign"].get("advertisingChannelType",""),
                    "bidding": r["campaign"].get("biddingStrategyType",""),
                    "budget": int(r.get("campaignBudget",{}).get("amountMicros",0))/1e6,
                    "clicks":0,"impr":0,"cost":0,"conv":0,
                }
            m = r.get("metrics",{})
            camps[cid_]["clicks"] += int(m.get("clicks",0))
            camps[cid_]["impr"]   += int(m.get("impressions",0))
            camps[cid_]["cost"]   += int(m.get("costMicros",0))/1e6
            camps[cid_]["conv"]   += float(m.get("conversions",0))
        rows = sorted(camps.values(), key=lambda x: x["cost"], reverse=True)
        if not rows:
            print("  (no April activity)")
            return
        print(f"{'ID':<14} {'Name':<35} {'Status':<8} {'Bid':<22} {'Bud':>5} {'Impr':>7} {'Clk':>5} {'Conv':>5} {'Cost':>7} {'CPA':>6}")
        for r in rows:
            cpa = r["cost"]/r["conv"] if r["conv"] else 0
            cpa_str = f"{cpa:.0f}" if r["conv"] else "—"
            print(f"{r['id']:<14} {r['name'][:34]:<35} {r['status']:<8} {r['bidding'][:21]:<22} "
                  f"{r['budget']:>5.0f} {r['impr']:>7} {r['clicks']:>5} {r['conv']:>5.0f} "
                  f"{r['cost']:>7.0f} {cpa_str:>6}")
    finally:
        cfg["google_ads"]["customer_id"] = saved_cid


list_campaigns(PRIMARY_CID, "PRIMARY ACCOUNT (Jayanagar cafe lives here)")
list_campaigns(CAFE_CID,    "BTM CAFE ACCOUNT")
