#!/usr/bin/env python3
"""Check existing PMax campaign + Store Visit eligibility for cafe."""
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

cfg = load_config()


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# 1. Find the PMax campaign
section("1. Existing PMax campaigns")
q = """SELECT campaign.id, campaign.name, campaign.status,
              campaign.advertising_channel_type,
              campaign.advertising_channel_sub_type,
              campaign_budget.amount_micros,
              metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions
       FROM campaign
       WHERE campaign.advertising_channel_type IN ('PERFORMANCE_MAX','LOCAL','LOCAL_SERVICES')
         AND campaign.status != 'REMOVED'
         AND segments.date DURING LAST_30_DAYS"""
agg = {}
for r in google_gaql(cfg, q):
    cid = r["campaign"]["id"]
    if cid not in agg:
        agg[cid] = {
            "id": cid, "name": r["campaign"]["name"],
            "status": r["campaign"].get("status",""),
            "type": r["campaign"].get("advertisingChannelType",""),
            "subtype": r["campaign"].get("advertisingChannelSubType",""),
            "budget": int(r.get("campaignBudget",{}).get("amountMicros",0))/1e6,
            "impr":0,"clk":0,"cost":0,"conv":0,
        }
    m = r.get("metrics",{})
    agg[cid]["impr"] += int(m.get("impressions",0))
    agg[cid]["clk"]  += int(m.get("clicks",0))
    agg[cid]["cost"] += int(m.get("costMicros",0))/1e6
    agg[cid]["conv"] += float(m.get("conversions",0))
for c in agg.values():
    print(f"  {c['id']}  {c['name'][:45]:<46} {c['type']:<14} {c['subtype'][:18]:<19} {c['status']:<8} bud=Rs{c['budget']:>4.0f} impr={c['impr']:>4} clk={c['clk']:>3} conv={c['conv']:>3.0f}")


# 2. Check all conversion actions for STORE_VISIT or similar
section("2. STORE VISIT eligibility — conversion actions on account")
q = """SELECT conversion_action.id, conversion_action.name,
              conversion_action.status, conversion_action.type,
              conversion_action.category,
              conversion_action.primary_for_goal,
              conversion_action.origin
       FROM conversion_action
       WHERE conversion_action.status != 'REMOVED'"""
all_actions = list(google_gaql(cfg, q))
print(f"  Total active conversion actions: {len(all_actions)}")
print()
for r in all_actions:
    ca = r["conversionAction"]
    nm = ca.get("name","")[:40]
    cat = ca.get("category","")
    typ = ca.get("type","")
    origin = ca.get("origin","")
    is_visit = ("STORE_VISIT" in cat or "STORE_VISIT" in typ or "STORE_VISITS" in str(ca).upper() or
                "store visit" in nm.lower())
    flag = "🏪 STORE VISIT" if is_visit else ""
    print(f"  {ca['id']}  {nm:<41} {cat:<22} {typ:<22} {origin:<18} {flag}")


# 3. Check the cafe customer linked locations
section("3. Customer-level GBP locations linked")
q = """SELECT customer.id, customer.has_partners_badge, customer.test_account
       FROM customer"""
for r in google_gaql(cfg, q):
    print(f"  Customer: {r}")


# 4. Asset sets (LOCATION_SYNC)
section("4. Asset sets — locations linked")
q = """SELECT asset_set.id, asset_set.name, asset_set.type,
              asset_set.status, asset_set.location_set
       FROM asset_set
       WHERE asset_set.status != 'REMOVED'"""
for r in google_gaql(cfg, q):
    a = r["assetSet"]
    print(f"  {a['id']}  {a.get('name','')[:30]:<30} type={a.get('type','')}  status={a.get('status','')}")


# 5. PMax campaign details — ad groups + asset groups
section("5. PMax 23769035916 detail")
q = """SELECT campaign.id, asset_group.id, asset_group.name, asset_group.status,
              asset_group.final_urls
       FROM asset_group
       WHERE campaign.id = 23769035916"""
for r in google_gaql(cfg, q):
    ag = r["assetGroup"]
    print(f"  {ag.get('id','')}  {ag.get('name','')[:35]:<36} {ag.get('status','')}  {ag.get('finalUrls',[])}")
