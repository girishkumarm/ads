#!/usr/bin/env python3
"""Jayanagar Cafe — emergency impression-boost diagnosis."""
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


# 1. EXACT bidding settings (may have a Target CPA cap strangling bids)
section("1. CAMPAIGN — exact bidding settings + budget")
q = f"""SELECT campaign.bidding_strategy_type, campaign.bidding_strategy,
               campaign.maximize_conversions.target_cpa_micros,
               campaign.maximize_conversions.cpc_bid_ceiling_micros,
               campaign.target_cpa.target_cpa_micros,
               campaign.target_cpa.cpc_bid_ceiling_micros,
               campaign.target_cpa.cpc_bid_floor_micros,
               campaign_budget.amount_micros, campaign_budget.delivery_method,
               campaign.serving_status, campaign.experiment_type,
               campaign.optimization_score
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q):
    c = r["campaign"]
    cb = r.get("campaignBudget",{})
    print(f"  Bidding strategy type: {c.get('biddingStrategyType','?')}")
    mc = c.get("maximizeConversions", {})
    if mc:
        tcpa = int(mc.get("targetCpaMicros",0))/1e6
        ceil = int(mc.get("cpcBidCeilingMicros",0))/1e6
        print(f"  MaxConv target CPA  : ₹{tcpa:.0f}{' (CAP — algorithm WILL NOT bid above this)' if tcpa else ' (none — algorithm bids freely)'}")
        print(f"  MaxConv CPC ceiling : ₹{ceil:.0f}{' (HARD CAP)' if ceil else ' (none)'}")
    tc = c.get("targetCpa", {})
    if tc:
        tcpa = int(tc.get("targetCpaMicros",0))/1e6
        print(f"  TargetCPA target    : ₹{tcpa:.0f}")
    print(f"  Budget         : ₹{int(cb.get('amountMicros',0))/1e6:.0f}/day  ({cb.get('deliveryMethod','?')})")
    print(f"  Serving status : {c.get('servingStatus','?')}")
    print(f"  Optimization   : {float(c.get('optimizationScore',0))*100:.0f}%")


# 2. Ad groups — bid + status + ad strength + paused-but-good ads
section("2. AD GROUPS — status & top ad in each")
q = f"""SELECT ad_group.id, ad_group.name, ad_group.status,
               ad_group.cpc_bid_micros, ad_group.target_cpa_micros
        FROM ad_group WHERE campaign.id = {CAMP_ID}
          AND ad_group.status != 'REMOVED'"""
ags = list(google_gaql(cfg, q))
print(f"  {'AG ID':<14} {'Name':<35} {'Status':<8} {'CPC bid':>10} {'TCPA':>8}")
for r in ags:
    a = r["adGroup"]
    cpc = int(a.get("cpcBidMicros",0))/1e6
    tcpa = int(a.get("targetCpaMicros",0))/1e6
    print(f"  {a['id']:<14} {a['name'][:34]:<35} {a.get('status',''):<8} ₹{cpc:>8.0f} ₹{tcpa:>6.0f}")


# 3. Find PAUSED ads with GOOD/EXCELLENT strength — these should be re-enabled
section("3. PAUSED ADS WITH GOOD/EXCELLENT STRENGTH (re-enable candidates)")
q = f"""SELECT ad_group.name, ad_group.id, ad_group_ad.ad.id,
               ad_group_ad.status, ad_group_ad.ad_strength,
               ad_group_ad.ad.responsive_search_ad.headlines
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status = 'PAUSED'
          AND ad_group_ad.ad_strength IN ('GOOD','EXCELLENT')"""
candidates = []
for r in google_gaql(cfg, q):
    a = r["adGroupAd"]
    h0 = (a["ad"].get("responsiveSearchAd",{}).get("headlines",[{}])[0] or {}).get("text","")
    candidates.append({
        "ag_id": r["adGroup"]["id"], "ag_name": r["adGroup"]["name"],
        "ad_id": a["ad"]["id"], "strength": a.get("adStrength",""),
        "h1": h0,
    })
if candidates:
    for c in candidates:
        print(f"  AG {c['ag_id']:<14} '{c['ag_name'][:25]:<26}'  AD {c['ad_id']}  {c['strength']:<10}  H1: {c['h1']}")
else:
    print("  None.")


# 4. Recent change events Apr 25-29 (BEFORE the crash)
section("4. CHANGE EVENTS APR 25-29 (looking for what broke things)")
q = f"""SELECT change_event.change_date_time, change_event.user_email,
               change_event.client_type, change_event.change_resource_type,
               change_event.resource_change_operation, change_event.changed_fields
        FROM change_event
        WHERE change_event.change_date_time >= '2026-04-25 00:00:00'
          AND change_event.change_date_time <= '2026-04-29 23:59:59'
          AND campaign.id = {CAMP_ID}
        ORDER BY change_event.change_date_time DESC
        LIMIT 30"""
try:
    rows = list(google_gaql(cfg, q))
    if not rows:
        print("  No changes Apr 25-29.")
    for r in rows:
        ce = r["changeEvent"]
        dt = ce.get("changeDateTime","")[:19]
        print(f"  {dt} {ce.get('resourceChangeOperation','?'):<7} {ce.get('changeResourceType',''):<22} "
              f"{ce.get('userEmail','')[:25]:<26} fields={ce.get('changedFields','')[:80]}")
except Exception as e:
    print(f"  [err] {str(e)[:200]}")


# 5. Currently active conversion actions on this campaign + recent attribution
section("5. RECENT CONVERSIONS BY DATE (last 14 days)")
q = f"""SELECT segments.date, segments.conversion_action_name,
               metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_14_DAYS
          AND metrics.conversions > 0"""
by_date = {}
for r in google_gaql(cfg, q):
    d = r["segments"]["date"]
    a = r["segments"].get("conversionActionName","?")
    by_date.setdefault(d, {})[a] = by_date.get(d, {}).get(a, 0) + float(r.get("metrics",{}).get("conversions",0))
for d in sorted(by_date.keys()):
    actions = by_date[d]
    total = sum(actions.values())
    print(f"  {d}: {total:>4.0f} conv  [{', '.join(f'{a}:{c:.0f}' for a,c in actions.items())}]")
