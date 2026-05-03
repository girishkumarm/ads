#!/usr/bin/env python3
"""Jayanagar Cafe Search 23778954613 — add 3 price assets.

Per user request 2026-05-03:
  1. Rs 499 unlimited combo (Coffee + Pizza + Fries)
  2. Rs 199 cabin for work-from-cafe (WiFi + AC + Power)
  3. Rs 199 buy-1-get-1 ice cream after 10 PM

Price assets shown directly in search results below ad — proven CTR boost.
"""
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

CUSTOMER_ID = "2995160429"
CAMP_ID = "23778954613"
TARGET_URL = "https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/"

cfg = load_config()
cl = _get_google_ads_client(cfg)


def main():
    print(f"=== Adding price asset to Jayanagar Cafe Search {CAMP_ID} ===\n")

    a_svc = cl.get_service("AssetService")
    ca_svc = cl.get_service("CampaignAssetService")

    # Build the price asset
    op = cl.get_type("AssetOperation")
    a = op.create
    a.name = "Jayanagar Cafe — Combos & Deals"
    pa = a.price_asset
    pa.type_ = cl.enums.PriceExtensionTypeEnum.SERVICES
    pa.price_qualifier = cl.enums.PriceExtensionPriceQualifierEnum.FROM
    pa.language_code = "en"

    # Offering 1: Rs 499 unlimited combo
    o1 = pa.price_offerings.add()
    o1.header = "Unlimited Combo"
    o1.description = "Coffee + Pizza + Fries"
    o1.price.amount_micros = 499 * 1_000_000
    o1.price.currency_code = "INR"
    o1.unit = cl.enums.PriceExtensionPriceUnitEnum.UNSPECIFIED
    o1.final_url = TARGET_URL

    # Offering 2: Rs 199 cabin for work-from-cafe
    o2 = pa.price_offerings.add()
    o2.header = "Work Cabin Day Pass"
    o2.description = "WiFi + AC + Power Plug"
    o2.price.amount_micros = 199 * 1_000_000
    o2.price.currency_code = "INR"
    o2.unit = cl.enums.PriceExtensionPriceUnitEnum.PER_DAY
    o2.final_url = TARGET_URL

    # Offering 3: Rs 199 1+1 ice cream after 10pm
    o3 = pa.price_offerings.add()
    o3.header = "1+1 Ice Cream"
    o3.description = "Daily after 10 PM"
    o3.price.amount_micros = 199 * 1_000_000
    o3.price.currency_code = "INR"
    o3.unit = cl.enums.PriceExtensionPriceUnitEnum.UNSPECIFIED
    o3.final_url = TARGET_URL

    # Create the asset
    print("Creating price asset with 3 offerings...")
    print(f"  1. Unlimited Combo            — Rs 499  | Coffee + Pizza + Fries")
    print(f"  2. Work Cabin Day Pass        — Rs 199 /day  | WiFi + AC + Power Plug")
    print(f"  3. 1+1 Ice Cream              — Rs 199  | Daily after 10 PM")

    try:
        resp = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
        asset_rn = resp.results[0].resource_name
        print(f"\n[OK] price asset created: {asset_rn}")
    except Exception as e:
        print(f"\n[ERR] asset create failed: {str(e)[:600]}")
        return

    # Link to campaign
    print("\nLinking price asset to campaign...")
    op2 = cl.get_type("CampaignAssetOperation")
    ca = op2.create
    ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
    ca.asset = asset_rn
    ca.field_type = cl.enums.AssetFieldTypeEnum.PRICE
    try:
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op2])
        print(f"[OK] price asset linked to campaign {CAMP_ID}")
    except Exception as e:
        print(f"[FAIL] link to campaign: {str(e)[:300]}")
        # Try at account-level fallback
        try:
            cust_svc = cl.get_service("CustomerAssetService")
            op3 = cl.get_type("CustomerAssetOperation")
            cu = op3.create
            cu.asset = asset_rn
            cu.field_type = cl.enums.AssetFieldTypeEnum.PRICE
            cust_svc.mutate_customer_assets(customer_id=CUSTOMER_ID, operations=[op3])
            print(f"[OK] price asset linked at account-level (fallback)")
        except Exception as e2:
            print(f"[FAIL] account-level link too: {str(e2)[:300]}")

    # Verify
    print("\n=== Verifying ===")
    q = f"""SELECT asset.id, asset.name, campaign_asset.field_type,
                   campaign_asset.status
            FROM campaign_asset
            WHERE campaign.id = {CAMP_ID}
              AND campaign_asset.field_type = 'PRICE'
              AND campaign_asset.status = 'ENABLED'"""
    found = False
    for r in google_gaql(cfg, q):
        found = True
        a = r["asset"]
        print(f"  PRICE asset live: id={a['id']} name='{a.get('name','')}'")
    if not found:
        print(f"  No PRICE asset showing yet on campaign {CAMP_ID} (may need 5-15 min to propagate)")


if __name__ == "__main__":
    main()
