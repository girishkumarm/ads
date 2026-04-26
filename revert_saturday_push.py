#!/usr/bin/env python3
"""Revert Saturday push tomorrow morning. Restores budget, schedules, and removes
the Saturday-only sitelink + promotion asset."""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""

import json
from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
CAMP_ID = "23778954613"

cfg = load_config()
cl = _get_google_ads_client(cfg)

with open(".saturday_push_state.json") as f:
    state = json.load(f)

print(f"=== Reverting Saturday push (applied {state['timestamp']}) ===\n")

# 1. Budget back
print("=== 1. Restore budget ===")
q = f"""SELECT campaign.id, campaign_budget.id
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
bud_id = google_gaql(cfg, q)[0]["campaignBudget"]["id"]
svc = cl.get_service("CampaignBudgetService")
op = cl.get_type("CampaignBudgetOperation")
op.update.resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{bud_id}"
op.update.amount_micros = int(state["budget_old"] * 1_000_000)
op.update_mask.CopyFrom(FieldMask(paths=["amount_micros"]))
svc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[op])
print(f"  [OK] Budget restored to Rs {state['budget_old']:.0f}/day")

# 2. Saturday schedules back
print("\n=== 2. Restore Saturday schedules ===")
crit_svc = cl.get_service("CampaignCriterionService")
ops = []
for orig in (state.get("sat_originals") or []):
    op = cl.get_type("CampaignCriterionOperation")
    op.update.resource_name = orig["rn"]
    op.update.bid_modifier = orig["old"]
    op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
    ops.append(op)
    print(f"  SAT {orig['start']:>2}-{orig['end']:>2}h restored to ×{orig['old']:.2f}")
if ops:
    crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)

# 3. Unlink Saturday sitelink
print("\n=== 3. Unlink Saturday Special sitelink ===")
sat_rn = state.get("saturday_sitelink_rn")
if sat_rn:
    q2 = f"""SELECT campaign.id, campaign_asset.resource_name, asset.resource_name
             FROM campaign_asset
             WHERE campaign.id = {CAMP_ID}
               AND campaign_asset.field_type = 'SITELINK'
               AND campaign_asset.status = 'ENABLED'"""
    for r in google_gaql(cfg, q2):
        if r["asset"]["resourceName"] == sat_rn:
            ca_svc = cl.get_service("CampaignAssetService")
            op = cl.get_type("CampaignAssetOperation")
            op.remove = r["campaignAsset"]["resourceName"]
            ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op])
            print(f"  [OK] Unlinked Saturday Special sitelink")
            break

# 4. Unlink Promotion
print("\n=== 4. Unlink Promotion asset ===")
promo_rn = state.get("promotion_rn")
if promo_rn:
    q3 = f"""SELECT campaign.id, campaign_asset.resource_name, asset.resource_name
             FROM campaign_asset
             WHERE campaign.id = {CAMP_ID}
               AND campaign_asset.field_type = 'PROMOTION'
               AND campaign_asset.status = 'ENABLED'"""
    for r in google_gaql(cfg, q3):
        if r["asset"]["resourceName"] == promo_rn:
            ca_svc = cl.get_service("CampaignAssetService")
            op = cl.get_type("CampaignAssetOperation")
            op.remove = r["campaignAsset"]["resourceName"]
            ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op])
            print(f"  [OK] Unlinked Couples Combo promo")
            break

print("\n=== Revert complete ===")
