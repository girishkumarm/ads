#!/usr/bin/env python3
"""Jayanagar Cafe — diagnose why traffic + conversions broke around Apr 27-29."""
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


# 1. Ad approval status + final URLs
section("1. RSA STATUS + FINAL URLS")
q = f"""SELECT ad_group.name, ad_group_ad.ad.id,
               ad_group_ad.status, ad_group_ad.policy_summary.review_status,
               ad_group_ad.policy_summary.approval_status,
               ad_group_ad.ad_strength,
               ad_group_ad.ad.final_urls,
               ad_group_ad.ad.responsive_search_ad.headlines
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status != 'REMOVED'"""
for r in google_gaql(cfg, q):
    a = r["adGroupAd"]
    ad = a["ad"]
    rsa = ad.get("responsiveSearchAd", {})
    h0 = rsa.get("headlines", [{}])[0].get("text","")
    print(f"\n  AG: {r['adGroup']['name']}")
    print(f"  AD: {ad['id']}  status={a.get('status','?')}  strength={a.get('adStrength','?')}")
    pol = a.get("policySummary", {})
    print(f"  Review: {pol.get('reviewStatus','?')}  Approval: {pol.get('approvalStatus','?')}")
    print(f"  Final URL: {ad.get('finalUrls',[''])[0] if ad.get('finalUrls') else '—'}")
    print(f"  H1: {h0}")


# 2. Recent change history (Apr 25 - May 3)
section("2. CHANGE HISTORY APR 26 - MAY 3")
q = f"""SELECT change_event.change_date_time, change_event.user_email,
               change_event.client_type, change_event.change_resource_type,
               change_event.change_resource_name,
               change_event.resource_change_operation,
               change_event.changed_fields
        FROM change_event
        WHERE change_event.change_date_time >= '2026-04-26 00:00:00'
          AND change_event.change_date_time <= '2026-05-03 23:59:59'
          AND campaign.id = {CAMP_ID}
        ORDER BY change_event.change_date_time DESC
        LIMIT 50"""
try:
    rows = list(google_gaql(cfg, q))
    if not rows:
        print("  No change events recorded in window.")
    for r in rows:
        ce = r["changeEvent"]
        dt = ce.get("changeDateTime","")[:19]
        op = ce.get("resourceChangeOperation","?")
        rt = ce.get("changeResourceType","?")
        u  = ce.get("userEmail","")[:30]
        cl = ce.get("clientType","")
        flds = ce.get("changedFields", "")
        print(f"  {dt:<19} {op:<8} {rt:<22} client={cl:<14} user={u}")
        if flds:
            print(f"     fields: {flds[:120]}")
except Exception as e:
    print(f"  [WARN] change_event query failed: {str(e)[:200]}")


# 3. Check campaign-level conversion settings + bidding target CPA
section("3. CAMPAIGN BIDDING + CONVERSION SETTINGS")
q = f"""SELECT campaign.bidding_strategy_type,
               campaign.maximize_conversions.target_cpa_micros,
               campaign.target_cpa.target_cpa_micros,
               campaign.selective_optimization.conversion_actions,
               campaign.serving_status,
               campaign.status,
               campaign.optimization_score
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q):
    c = r["campaign"]
    print(f"  Status        : {c.get('status','?')}")
    print(f"  Serving       : {c.get('servingStatus','?')}")
    print(f"  Bidding type  : {c.get('biddingStrategyType','?')}")
    mc = c.get("maximizeConversions", {})
    if mc:
        target = int(mc.get("targetCpaMicros", 0))/1e6
        print(f"  Max Conv target CPA  : ₹{target:.0f}")
    sel = c.get("selectiveOptimization", {})
    if sel and sel.get("conversionActions"):
        print(f"  Selective optimization: {sel.get('conversionActions')}")
    score = c.get("optimizationScore",0)
    print(f"  Optimization score: {float(score)*100:.0f}%")


# 4. Recent conversion attribution sources
section("4. CONVERSION SOURCES (LAST 30 DAYS, by date + action)")
q = f"""SELECT segments.date,
               segments.conversion_action_name,
               metrics.conversions
        FROM campaign WHERE campaign.id = {CAMP_ID}
          AND segments.date DURING LAST_30_DAYS
          AND metrics.conversions > 0"""
by_date_action = {}
for r in google_gaql(cfg, q):
    d = r["segments"]["date"]
    a = r["segments"].get("conversionActionName","?")
    by_date_action[(d, a)] = by_date_action.get((d, a), 0) + float(r.get("metrics",{}).get("conversions",0))
print(f"  {'Date':<12} {'Action':<35} {'Conv':>5}")
last_action_by_date = {}
for (d, a), c in sorted(by_date_action.items()):
    last_action_by_date.setdefault(d, []).append((a, c))
for d in sorted(last_action_by_date.keys())[-15:]:
    for a, c in last_action_by_date[d]:
        print(f"  {d:<12} {a[:34]:<35} {c:>5.0f}")


# 5. Recent ads that may have triggered review (if any DISAPPROVED, that explains rank crash)
section("5. ADS WITH NON-APPROVED STATUS")
q = f"""SELECT ad_group.name, ad_group_ad.ad.id,
               ad_group_ad.policy_summary.review_status,
               ad_group_ad.policy_summary.approval_status,
               ad_group_ad.policy_summary.policy_topic_entries
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status != 'REMOVED'
          AND ad_group_ad.policy_summary.approval_status != 'APPROVED'"""
found = False
for r in google_gaql(cfg, q):
    found = True
    a = r["adGroupAd"]
    pol = a.get("policySummary",{})
    print(f"  AG: {r['adGroup']['name']}  AD: {a['ad']['id']}  status: {pol.get('approvalStatus','?')}")
    for t in pol.get("policyTopicEntries", []):
        print(f"    topic: {t}")
if not found:
    print("  All ads APPROVED. Not a policy issue.")
