#!/usr/bin/env python3
"""Jayanagar — emergency unblock: remove damaging broad negatives + check bidding cap."""
import os, json
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

# ─── Step 1: bidding strategy details ──────────────
print("="*78)
print("BIDDING / TARGET CPA")
print("="*78)
q = f"""SELECT campaign.bidding_strategy_type,
               campaign.maximize_conversions.target_cpa_micros,
               campaign_budget.amount_micros
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q):
    c = r["campaign"]
    cb = r.get("campaignBudget",{})
    bid = c.get("biddingStrategyType","?")
    print(f"  Bidding: {bid}")
    if bid == "MAXIMIZE_CONVERSIONS":
        tcpa = int(c.get("maximizeConversions",{}).get("targetCpaMicros",0))/1e6
        if tcpa:
            print(f"  Target CPA cap: ₹{tcpa:.0f}  ← This caps how high algo bids!")
        else:
            print(f"  Target CPA cap: NONE — algorithm bids freely")
    print(f"  Budget: ₹{int(cb.get('amountMicros',0))/1e6:.0f}/day")


# ─── Step 2: remove damaging broad negatives ───────
print(f"\n{'='*78}")
print("REMOVING DAMAGING BROAD NEGATIVES")
print("="*78)

# These are blocking too much real intent
DAMAGING_NEGS = [
    ("restaurant", "BROAD"),  # blocks "X restaurant cafe" too
    ("lunch", "BROAD"),       # blocks "lunch cafe near me"
    ("breakfast", "BROAD"),   # blocks "breakfast cafe near me"
    ("brunch", "BROAD"),      # blocks "brunch cafe near me"
]

# Pull current negatives to find their resource_names
q = f"""SELECT campaign_criterion.resource_name,
               campaign_criterion.keyword.text,
               campaign_criterion.keyword.match_type
        FROM campaign_criterion
        WHERE campaign.id = {CAMP_ID}
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
          AND campaign_criterion.status = 'ENABLED'"""
existing = {}
for r in google_gaql(cfg, q):
    c = r["campaignCriterion"]
    k = c["keyword"]
    existing[(k["text"].lower(), k["matchType"])] = c["resourceName"]

svc = cl.get_service("CampaignCriterionService")
for text, match in DAMAGING_NEGS:
    rn = existing.get((text.lower(), match))
    if not rn:
        print(f"  [skip] [{match}] {text} not found")
        continue
    op = cl.get_type("CampaignCriterionOperation")
    op.remove = rn
    try:
        svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  [OK] removed [{match}] {text}")
    except Exception as e:
        print(f"  [FAIL] [{match}] {text}: {str(e)[:200]}")


# ─── Step 3: confirm AG status now ─────────────────
print(f"\n{'='*78}")
print("CURRENT AD GROUP STATUS")
print("="*78)
q = f"""SELECT ad_group.id, ad_group.name, ad_group.status
        FROM ad_group WHERE campaign.id = {CAMP_ID}
          AND ad_group.status != 'REMOVED'"""
for r in google_gaql(cfg, q):
    a = r["adGroup"]
    print(f"  {a['id']:<14} {a['name'][:40]:<40} {a.get('status','')}")
