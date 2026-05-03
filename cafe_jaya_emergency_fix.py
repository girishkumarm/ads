#!/usr/bin/env python3
"""Jayanagar Cafe — emergency impression boost.

Plan:
  Step 1: dump current negatives (find aggressive ones blocking real intent)
  Step 2: re-enable 4 GOOD/EXCELLENT paused ads in active AGs
  Step 3: re-enable 3 paused ad groups (Couple Outing, Work & Laptop, Competitors)
"""
import os, json, datetime
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

CAMP_ID = "23778954613"
CUSTOMER_ID = "2995160429"
cfg = load_config()
cl = _get_google_ads_client(cfg)


# ─── Step 1: list ALL active negatives, especially ones added recently ─────
print("="*78)
print("STEP 1: CURRENT NEGATIVE KEYWORDS ON CAMPAIGN")
print("="*78)
q = f"""SELECT campaign_criterion.criterion_id,
               campaign_criterion.keyword.text,
               campaign_criterion.keyword.match_type,
               campaign_criterion.status
        FROM campaign_criterion
        WHERE campaign.id = {CAMP_ID}
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
          AND campaign_criterion.status = 'ENABLED'"""
negs = []
for r in google_gaql(cfg, q):
    c = r["campaignCriterion"]
    k = c["keyword"]
    negs.append({"crit_id": c["criterionId"], "text": k["text"], "match": k["matchType"]})
print(f"Found {len(negs)} active negative keywords:")
suspicious = []
for n in negs:
    flag = ""
    txt = n["text"].lower()
    # Flag overly broad / dangerous negatives
    if txt in ["cafe","cafes","coffee","coffee shop","near me","jayanagar","bangalore","bengaluru","food","drink","drinks","restaurant","restaurants"]:
        flag = "🚨 TOO BROAD — PROBABLY KILLING TRAFFIC"
        suspicious.append(n)
    elif n["match"]=="BROAD" and len(txt.split()) <= 2:
        flag = "🟡 broad+short — may over-block"
    print(f"  [{n['match']:<7}] {n['text']:<35} crit={n['crit_id']} {flag}")

if suspicious:
    print(f"\n🚨 {len(suspicious)} SUSPICIOUS negatives — listing them:")
    for n in suspicious:
        print(f"  RECOMMEND REMOVE: [{n['match']}] {n['text']}")


# ─── Step 2: Re-enable 4 GOOD/EXCELLENT paused ads in active AGs ─────
print(f"\n{'='*78}")
print("STEP 2: RE-ENABLE 4 GOOD/EXCELLENT PAUSED ADS")
print("="*78)
ENABLE_ADS = [
    ("193683802497", "807545229005"),  # Events AG, GOOD
    ("195096525985", "807359638224"),  # Core AG, GOOD - Cafe Near Me - Jayanagar
    ("195096525985", "807473448428"),  # Core AG, GOOD - Cafe Near Me Open Now
    ("195096525985", "807608390771"),  # Core AG, GOOD - Cafes Near Me Jayanagar
]
svc = cl.get_service("AdGroupAdService")
for ag_id, ad_id in ENABLE_ADS:
    op = cl.get_type("AdGroupAdOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/adGroupAds/{ag_id}~{ad_id}"
    op.update.status = cl.enums.AdGroupAdStatusEnum.ENABLED
    op.update_mask.CopyFrom(FieldMask(paths=["status"]))
    try:
        svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] enabled AD {ad_id} in AG {ag_id}")
    except Exception as e:
        print(f"  [FAIL] AD {ad_id}: {str(e)[:200]}")


# ─── Step 3: Re-enable 3 paused ad groups ─────
print(f"\n{'='*78}")
print("STEP 3: RE-ENABLE 3 PAUSED AD GROUPS")
print("="*78)
ENABLE_AGS = [
    ("193683802457", "Couple Outing - Jayanagar"),
    ("193683802537", "Work & Laptop Friendly - Jayanagar"),
    ("197176818458", "Competitors - Jayanagar"),
]
ag_svc = cl.get_service("AdGroupService")
for ag_id, name in ENABLE_AGS:
    op = cl.get_type("AdGroupOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
    op.update.status = cl.enums.AdGroupStatusEnum.ENABLED
    op.update_mask.CopyFrom(FieldMask(paths=["status"]))
    try:
        ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] enabled AG {ag_id} '{name}'")
    except Exception as e:
        print(f"  [FAIL] AG {ag_id}: {str(e)[:200]}")
