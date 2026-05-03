#!/usr/bin/env python3
"""BTM Search — diagnose 0-conversion mystery. Check ads + final URLs + tracking links."""
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
CAMP_ID = "22635490939"
cfg = load_config()
cfg["google_ads"]["customer_id"] = cfg["google_ads"]["cafe_customer_id"]

# 1. Ads on this campaign
print("="*70)
print("BTM Search — current ads + final URLs")
print("="*70)
q = f"""SELECT ad_group.name, ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.final_urls, ad_group_ad.ad.tracking_url_template,
               ad_group_ad.ad.url_custom_parameters,
               ad_group_ad.status, ad_group_ad.ad_strength
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status = 'ENABLED'"""
seen=set()
for r in google_gaql(cfg, q):
    aid = r["adGroupAd"]["ad"]["id"]
    if aid in seen: continue
    seen.add(aid)
    ad = r["adGroupAd"]["ad"]
    rsa = ad.get("responsiveSearchAd", {})
    print(f"\nAG: {r['adGroup']['name']}  AD: {aid}  Strength: {r['adGroupAd'].get('adStrength','?')}")
    print(f"  Final URL: {ad.get('finalUrls',[''])[0] if ad.get('finalUrls') else '—'}")
    print(f"  Tracking template: {ad.get('trackingUrlTemplate','—')}")
    h = rsa.get("headlines", [])[:5]
    print(f"  First 5 headlines: {[hh.get('text','') for hh in h]}")
    d = rsa.get("descriptions", [])[:2]
    print(f"  First 2 descriptions: {[dd.get('text','') for dd in d]}")

# 2. Campaign URL options
print("\n" + "="*70)
print("Campaign URL settings")
print("="*70)
q = f"""SELECT campaign.tracking_url_template, campaign.final_url_suffix,
               campaign.url_custom_parameters
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q):
    c = r["campaign"]
    print(f"  Tracking template: {c.get('trackingUrlTemplate','—')}")
    print(f"  Final URL suffix : {c.get('finalUrlSuffix','—')}")

# 3. Check if conversion actions are linked to this campaign
print("\n" + "="*70)
print("Recent conversions on BTM account (last 90 days, by campaign)")
print("="*70)
q = f"""SELECT campaign.id, campaign.name, segments.conversion_action_name,
               metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_90_DAYS
          AND campaign.status != 'REMOVED'
          AND metrics.conversions > 0"""
seen_action = {}
for r in google_gaql(cfg, q):
    name = r["campaign"]["name"][:30]
    action = r["segments"].get("conversionActionName","?")
    conv = float(r.get("metrics",{}).get("conversions",0))
    key = (name, action)
    seen_action[key] = seen_action.get(key, 0) + conv
if seen_action:
    print(f"{'Campaign':<32} {'Action':<35} {'Conv':>6}")
    for (camp, act), conv in sorted(seen_action.items(), key=lambda x: -x[1]):
        print(f"{camp:<32} {act[:34]:<35} {conv:>6.0f}")
else:
    print("  NO CONVERSIONS recorded on BTM account in last 90 days across ANY campaign.")

# 4. Sitelinks/extensions on BTM Search
print("\n" + "="*70)
print("Assets linked to BTM Search campaign")
print("="*70)
q = f"""SELECT campaign_asset.field_type, asset.name, asset.id,
               asset.sitelink_asset.link_text,
               asset.call_asset.phone_number,
               campaign_asset.status
        FROM campaign_asset
        WHERE campaign.id = {CAMP_ID}
          AND campaign_asset.status = 'ENABLED'"""
for r in google_gaql(cfg, q):
    ca = r["campaignAsset"]
    a = r["asset"]
    ftype = ca.get("fieldType","?")
    name = a.get("name") or a.get("sitelinkAsset",{}).get("linkText") or a.get("callAsset",{}).get("phoneNumber") or "?"
    print(f"  {ftype:<20} {name}")
