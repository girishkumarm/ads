#!/usr/bin/env python3
"""Jayanagar Cafe — full asset inventory across all 18 asset types."""
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

# All asset types Google Ads supports
ALL_TYPES = [
    "SITELINK","CALLOUT","STRUCTURED_SNIPPET","CALL","CALL_TO_ACTION_SELECTION",
    "LEAD_FORM","LOCATION","AFFILIATE_LOCATION","MOBILE_APP","HOTEL_CALLOUT",
    "PRICE","PROMOTION","AD_IMAGE","BUSINESS_LOGO","BUSINESS_NAME",
    "PORTRAIT_IMAGE","SQUARE_IMAGE","LANDSCAPE_IMAGE","HEADER_IMAGE",
    "LOGO","BOOK_ON_GOOGLE","BUSINESS_HOURS"
]

# Pull at campaign level
print("="*78)
print("CAMPAIGN-LEVEL ASSETS ON JAYANAGAR CAFE SEARCH")
print("="*78)
q = f"""SELECT campaign.id, campaign_asset.field_type, asset.type,
               asset.id, asset.name,
               asset.sitelink_asset.link_text,
               asset.callout_asset.callout_text,
               asset.structured_snippet_asset.header,
               asset.call_asset.phone_number,
               asset.promotion_asset.promotion_target,
               asset.price_asset.type,
               asset.image_asset.full_size.width_pixels,
               campaign_asset.status
        FROM campaign_asset
        WHERE campaign.id = {CAMP_ID}
          AND campaign_asset.status = 'ENABLED'"""
by_type = {}
for r in google_gaql(cfg, q):
    ca = r["campaignAsset"]
    a = r["asset"]
    ft = ca.get("fieldType","?")
    if ft not in by_type: by_type[ft] = []
    label = ""
    if a.get("sitelinkAsset"): label = a["sitelinkAsset"].get("linkText","")
    elif a.get("calloutAsset"): label = a["calloutAsset"].get("calloutText","")
    elif a.get("structuredSnippetAsset"): label = a["structuredSnippetAsset"].get("header","")
    elif a.get("callAsset"): label = a["callAsset"].get("phoneNumber","")
    elif a.get("promotionAsset"): label = a["promotionAsset"].get("promotionTarget","")
    elif a.get("priceAsset"): label = "(price)"
    else: label = a.get("name","?")
    by_type[ft].append({"id": a["id"], "label": label})

print(f"\nFound {sum(len(v) for v in by_type.values())} assets in {len(by_type)} types:\n")
for ft in sorted(by_type.keys()):
    print(f"  {ft}: {len(by_type[ft])}")
    for a in by_type[ft]:
        print(f"    - {a['id']:<14} {a['label'][:50]}")

# What's MISSING
present = set(by_type.keys())
print(f"\n{'='*78}")
print("MISSING ASSET TYPES (opportunities to add)")
print("="*78)
key_types = ["SITELINK","CALLOUT","STRUCTURED_SNIPPET","CALL","PROMOTION",
             "PRICE","LOCATION","BUSINESS_LOGO","BUSINESS_NAME"]
for ft in key_types:
    status = "✅ have" if ft in present else "❌ MISSING"
    print(f"  {status:<12}  {ft}")

# Account-level (CustomerAsset) check
print(f"\n{'='*78}")
print("ACCOUNT-LEVEL CUSTOMER ASSETS (apply to all campaigns)")
print("="*78)
q2 = """SELECT customer_asset.field_type, asset.id, asset.name,
               asset.sitelink_asset.link_text,
               asset.callout_asset.callout_text,
               asset.call_asset.phone_number,
               customer_asset.status
        FROM customer_asset
        WHERE customer_asset.status = 'ENABLED'"""
for r in google_gaql(cfg, q2):
    ca = r["customerAsset"]
    a = r["asset"]
    label = (a.get("sitelinkAsset",{}).get("linkText") or
             a.get("calloutAsset",{}).get("calloutText") or
             a.get("callAsset",{}).get("phoneNumber") or
             a.get("name","?"))
    print(f"  {ca.get('fieldType',''):<22} {a['id']:<14} {label[:50]}")

# AdGroup-level
print(f"\n{'='*78}")
print("AD-GROUP LEVEL ASSETS")
print("="*78)
q3 = f"""SELECT ad_group.name, ad_group_asset.field_type, asset.id, asset.name,
               asset.sitelink_asset.link_text, asset.callout_asset.callout_text,
               ad_group_asset.status
        FROM ad_group_asset
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_asset.status = 'ENABLED'"""
ag_count = 0
for r in google_gaql(cfg, q3):
    ag_count += 1
    aga = r["adGroupAsset"]
    a = r["asset"]
    label = (a.get("sitelinkAsset",{}).get("linkText") or
             a.get("calloutAsset",{}).get("calloutText") or
             a.get("name","?"))
    print(f"  AG '{r['adGroup']['name'][:25]:<26}'  {aga.get('fieldType',''):<18} {a['id']:<14} {label[:30]}")
if ag_count == 0:
    print("  None.")
