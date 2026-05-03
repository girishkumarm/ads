#!/usr/bin/env python3
"""Replace any '35 acre' mention in resort RSA headlines/descriptions + GBP service items.
User correction 2026-05-03: resort is 2 acres, not 35.
"""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, _get_google_ads_client, google_gaql, gbp_get_token, http_request

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"
cfg = load_config()
cl = _get_google_ads_client(cfg)


# 1) Find all resort campaign RSAs that mention "35"
print("=== Resort RSAs with '35' mention ===")
q = f"""SELECT ad_group.id, ad_group.name,
               ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status = 'ENABLED'"""

ads_to_fix = []
for r in google_gaql(cfg, q):
    ad = r["adGroupAd"]["ad"]
    rsa = ad.get("responsiveSearchAd", {})
    headlines = rsa.get("headlines", [])
    descriptions = rsa.get("descriptions", [])
    has35 = any("35" in (h.get("text","") or "") for h in headlines) or \
            any("35" in (d.get("text","") or "") for d in descriptions)
    if has35:
        ads_to_fix.append({
            "ag_id": r["adGroup"]["id"], "ag_name": r["adGroup"]["name"],
            "ad_id": ad["id"], "headlines": headlines, "descriptions": descriptions,
        })
        print(f"  AG '{r['adGroup']['name']}' AD {ad['id']}")
        for h in headlines:
            if "35" in (h.get("text","") or ""):
                print(f"    H: {h.get('text','')}")

if not ads_to_fix:
    print("  No 35-acre mentions found in RSAs.")
else:
    print(f"\nReplacing in {len(ads_to_fix)} ads...")
    ad_svc = cl.get_service("AdService")
    from google.protobuf.field_mask_pb2 import FieldMask
    for a in ads_to_fix:
        new_headlines = []
        for h in a["headlines"]:
            t = (h.get("text","") or "").replace("35 Acres","2 Acres").replace("35 acre","2 acre").replace("35-Acre","2-Acre")
            new_headlines.append({"text": t, "pinnedField": h.get("pinnedField") or "UNSPECIFIED"})
        new_descs = []
        for d in a["descriptions"]:
            t = (d.get("text","") or "").replace("35 acre","2 acre").replace("35-acre","2-acre")
            new_descs.append({"text": t, "pinnedField": d.get("pinnedField") or "UNSPECIFIED"})

        op = cl.get_type("AdOperation")
        op.update.resource_name = f"customers/{CUSTOMER_ID}/ads/{a['ad_id']}"
        for h in new_headlines:
            asset = op.update.responsive_search_ad.headlines.add()
            asset.text = h["text"]
        for d in new_descs:
            asset = op.update.responsive_search_ad.descriptions.add()
            asset.text = d["text"]
        op.update_mask.CopyFrom(FieldMask(paths=["responsive_search_ad.headlines", "responsive_search_ad.descriptions"]))
        try:
            ad_svc.mutate_ads(customer_id=CUSTOMER_ID, operations=[op])
            print(f"  [OK] AD {a['ad_id']} updated")
        except Exception as e:
            print(f"  [FAIL] AD {a['ad_id']}: {str(e)[:300]}")


# 2) Update GBP service items: replace "35 acre" → "2 acre" in descriptions
print("\n=== GBP service items ===")
LOC = "locations/10815844322260560435"
V1 = "https://mybusinessbusinessinformation.googleapis.com/v1"
token = gbp_get_token(cfg)
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

url = f"{V1}/{LOC}?readMask=serviceItems"
r, _ = http_request("GET", url, headers=H)
if r and "serviceItems" in r:
    items = r["serviceItems"]
    changed = False
    for s in items:
        ff = s.get("freeFormServiceItem", {})
        label = ff.get("label", {})
        nm = label.get("displayName", "")
        desc = label.get("description", "")
        if "35 acre" in (nm + desc).lower() or "35-acre" in (nm + desc).lower():
            label["displayName"] = nm.replace("35 acre","2 acre").replace("35-acre","2-acre")
            label["description"] = desc.replace("35 acre","2 acre").replace("35-acre","2-acre")
            changed = True
    if changed:
        body = {"serviceItems": items}
        url2 = f"{V1}/{LOC}?updateMask=serviceItems"
        r2, _ = http_request("PATCH", url2, headers=H, data=body)
        if r2 and "error" not in r2:
            print("  [OK] GBP service items updated")
        else:
            print(f"  [FAIL] {str(r2)[:200]}")
    else:
        print("  No '35 acre' in service items.")
