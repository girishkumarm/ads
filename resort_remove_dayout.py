#!/usr/bin/env python3
"""Pause 3 unwanted keywords per user 2026-05-03:
   - day outing resort bangalore (wrong intent — user doesn't want day-outing crowd)
   - day outing near bangalore
   - private pool villa near bangalore (also unwanted)
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

from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
CAMP_ID = "21740834372"

REMOVE = [
    "day outing resort bangalore",
    "day outing near bangalore",
    "private pool villa near bangalore",
]

cfg = load_config()
cl = _get_google_ads_client(cfg)
svc = cl.get_service("AdGroupCriterionService")

# Find them
q = f"""SELECT ad_group.name,
               ad_group_criterion.resource_name,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.negative
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_criterion.status = 'ENABLED'"""
targets = []
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"):
        continue
    text = c.get("keyword", {}).get("text", "").lower()
    if text in [x.lower() for x in REMOVE]:
        targets.append({
            "rn": c["resourceName"],
            "text": text,
            "match": c["keyword"]["matchType"],
            "ag": r["adGroup"]["name"],
        })

print(f"Found {len(targets)} matching keywords:")
for t in targets:
    print(f"  REMOVE [{t['match']}] {t['text']:<42} (ag: {t['ag']})")

ok = 0
for t in targets:
    op = cl.get_type("AdGroupCriterionOperation")
    op.remove = t["rn"]
    try:
        svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
        ok += 1
        print(f"  [OK] removed '{t['text']}'")
    except Exception as e:
        print(f"  [FAIL] '{t['text']}': {str(e)[:200]}")
print(f"\n[DONE] {ok}/{len(targets)} removed")
