#!/usr/bin/env python3
"""Point Group Bookings AG → namooru.com/weddings (live landing page)."""
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
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
AG_ID = "196256288356"  # Group Bookings & Events
NEW_URL = "https://namooru.com/weddings/?utm_source=google&utm_medium=cpc&utm_campaign=resort_group_bookings"

cfg = load_config()
cl = _get_google_ads_client(cfg)

# Find the RSA in this AG and update its final_urls
q = f"""SELECT ad_group_ad.ad.id, ad_group_ad.ad.final_urls,
               ad_group_ad.ad.responsive_search_ad.headlines
        FROM ad_group_ad
        WHERE ad_group.id = {AG_ID}
          AND ad_group_ad.status = 'ENABLED'"""
ads = list(google_gaql(cfg, q))
print(f"Found {len(ads)} ads in Group Bookings AG")
for r in ads:
    ad = r["adGroupAd"]["ad"]
    print(f"  AD {ad['id']}  current URLs: {ad.get('finalUrls',[])}")

if not ads:
    print("[ERR] no ads to update"); exit(1)

svc = cl.get_service("AdService")
for r in ads:
    ad_id = r["adGroupAd"]["ad"]["id"]
    op = cl.get_type("AdOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/ads/{ad_id}"
    op.update.final_urls.append(NEW_URL)
    op.update_mask.CopyFrom(FieldMask(paths=["final_urls"]))
    try:
        svc.mutate_ads(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] AD {ad_id} → {NEW_URL}")
    except Exception as e:
        print(f"  [FAIL] AD {ad_id}: {str(e)[:300]}")

print("\n=== Done ===")
