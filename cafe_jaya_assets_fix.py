#!/usr/bin/env python3
"""Fix the 2 failed assets from cafe_jaya_full_assets.py:
   - Featured snippet (retry with valid format)
   - 'Best Reviewed in Jayanagar' callout (was 25 chars, retry shorter)"""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, _get_google_ads_client

CUSTOMER_ID = "2995160429"
CAMP_ID = "23778954613"
CORE_AG = "195096525985"

cfg = load_config()
cl = _get_google_ads_client(cfg)
a_svc = cl.get_service("AssetService")
ca_svc = cl.get_service("CampaignAssetService")
aga_svc = cl.get_service("AdGroupAssetService")


# Try 'Highlights' header (vs 'Featured') — Google's curated list of approved snippet headers
try:
    op = cl.get_type("AssetOperation")
    a = op.create.structured_snippet_asset
    a.header = "Highlights"
    a.values.extend(["Saturday Special","Birthday Bookings","Couple Combos","Work Cabins","Late Night"])
    r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    rn = r.results[0].resource_name
    op2 = cl.get_type("CampaignAssetOperation")
    op2.create.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
    op2.create.asset = rn
    op2.create.field_type = cl.enums.AssetFieldTypeEnum.STRUCTURED_SNIPPET
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op2])
    print(f"[OK] structured snippet 'Highlights' added")
except Exception as e:
    print(f"[FAIL] Highlights: {str(e)[:300]}")


# Retry callout with shorter text
try:
    op = cl.get_type("AssetOperation")
    op.create.callout_asset.callout_text = "Top Cafe in Jayanagar"  # 21 chars
    r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    rn = r.results[0].resource_name
    op2 = cl.get_type("AdGroupAssetOperation")
    op2.create.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{CORE_AG}"
    op2.create.asset = rn
    op2.create.field_type = cl.enums.AssetFieldTypeEnum.CALLOUT
    aga_svc.mutate_ad_group_assets(customer_id=CUSTOMER_ID, operations=[op2])
    print(f"[OK] Core AG callout 'Top Cafe in Jayanagar' added")
except Exception as e:
    print(f"[FAIL] callout: {str(e)[:300]}")
