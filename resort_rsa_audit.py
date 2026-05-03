#!/usr/bin/env python3
"""Pull current resort RSAs (headlines + descriptions + ad strength + pinning)."""
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

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"
cfg = load_config()

q = f"""SELECT ad_group.id, ad_group.name,
               ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.responsive_search_ad.path1,
               ad_group_ad.ad.responsive_search_ad.path2,
               ad_group_ad.ad.final_urls,
               ad_group_ad.ad_strength,
               ad_group_ad.status,
               metrics.clicks, metrics.impressions, metrics.conversions
        FROM ad_group_ad
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_ad.status = 'ENABLED'
          AND segments.date DURING LAST_30_DAYS
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'"""

seen = set()
for r in google_gaql(cfg, q):
    aid = r["adGroupAd"]["ad"]["id"]
    if aid in seen: continue
    seen.add(aid)
    ad = r["adGroupAd"]["ad"]
    rsa = ad.get("responsiveSearchAd", {})
    print("="*75)
    print(f"AG: {r['adGroup']['name']}  (id={r['adGroup']['id']})")
    print(f"AD: {aid}  Strength: {r['adGroupAd'].get('adStrength','?')}  Status: {r['adGroupAd'].get('status','?')}")
    print(f"Final URL: {ad.get('finalUrls',[''])[0] if ad.get('finalUrls') else '—'}")
    print(f"Path1/2: /{rsa.get('path1','')}/{rsa.get('path2','')}")
    m = r.get("metrics",{})
    print(f"30d: clicks={int(m.get('clicks',0))}  impr={int(m.get('impressions',0))}  conv={float(m.get('conversions',0)):.0f}")
    print(f"\nHEADLINES ({len(rsa.get('headlines',[]))}):")
    for i, h in enumerate(rsa.get("headlines",[])):
        pin = h.get("pinnedField","")
        pin_str = f" [PIN:{pin}]" if pin and pin != "UNSPECIFIED" else ""
        print(f"  H{i+1:2d}. {h.get('text','')}{pin_str}")
    print(f"\nDESCRIPTIONS ({len(rsa.get('descriptions',[]))}):")
    for i, d in enumerate(rsa.get("descriptions",[])):
        pin = d.get("pinnedField","")
        pin_str = f" [PIN:{pin}]" if pin and pin != "UNSPECIFIED" else ""
        print(f"  D{i+1}. {d.get('text','')}{pin_str}")
    print()
