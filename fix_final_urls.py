#!/usr/bin/env python3
"""
Fix cafe ads final_urls: swap https://namooru.com/ → GBP maps URL everywhere.

Scope:
  - Cafe-for-sale campaign 23790548087 (2 RSAs, just created)
  - Cafe-operations Search campaign 23778954613 (4 RSAs)
  - Cafe PMax 23769035916 (asset group final_url)
  - 4 sitelinks added today on cafe-operations campaign

RSAs in Google Ads cannot have their final_urls modified in-place — must clone the
ad and pause the old one. Sitelinks (Assets) are immutable on link_text but the
asset can be replaced via the CampaignAsset. For simplicity we re-create sitelinks.
"""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"] = False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""

import sys
from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
# The short URL XZ18VWfeRT6xbRQn8 resolves to the BTM cafe by mistake.
# This is the correct Jayanagar 4th Block GBP page URL (from user 2026-04-24).
GBP_URL_WRONG = "https://maps.app.goo.gl/XZ18VWfeRT6xbRQn8"    # BTM cafe (wrong)
GBP_URL = (
    "https://www.google.com/maps/place/Brewing+Untold+Stories/"
    "@12.9199786,77.587245,905m/data=!3m2!1e3!4b1!4m6!3m5!"
    "1s0x3bae15fec810a3b3:0xf75b25b8f4c76726!"
    "8m2!3d12.9199786!4d77.5898199!16s%2Fg%2F11w9n2nqks!5m1!1e1"
)
# Old URLs we're swapping away from
OLD_URLS = {"https://namooru.com/", GBP_URL_WRONG}

CAFE_SEARCH_ID = "23778954613"   # operations
CAFE_PMAX_ID   = "23769035916"   # paused
CAFE_SALE_ID   = "23790548087"   # sale (new)
PMAX_ASSET_GROUP_ID = "6703742587"


def clone_rsas(campaign_id):
    """For every ENABLED RSA under this campaign with final_url == OLD_URL,
    create a clone with GBP_URL and pause the old ad."""
    config = load_config()
    client = _get_google_ads_client(config)
    ad_svc = client.get_service("AdGroupAdService")
    ServedAssetEnum = client.enums.ServedAssetFieldTypeEnum

    q = f"""
        SELECT ad_group.id, ad_group.name,
               ad_group_ad.resource_name,
               ad_group_ad.ad.id,
               ad_group_ad.ad.final_urls,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.responsive_search_ad.path1,
               ad_group_ad.ad.responsive_search_ad.path2
        FROM ad_group_ad
        WHERE campaign.id = {campaign_id}
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
          AND ad_group_ad.status = 'ENABLED'
    """
    rows = google_gaql(config, q)
    print(f"  Found {len(rows)} enabled RSA(s) under campaign {campaign_id}")

    cloned = 0
    paused = 0
    for r in rows:
        ag_id = r["adGroup"]["id"]
        ag_name = r["adGroup"]["name"]
        old_rn = r["adGroupAd"]["resourceName"]
        ad = r["adGroupAd"]["ad"]
        urls = ad.get("finalUrls", [])
        if not any(u in urls for u in OLD_URLS) and GBP_URL not in urls:
            # Don't touch if it's already on something else (e.g. the Core AG's
            # maps search URL). Only migrate URLs we explicitly want to replace.
            if GBP_URL in urls:
                print(f"    [SKIP] AG {ag_id} ({ag_name}): already on GBP_URL")
            else:
                print(f"    [SKIP] AG {ag_id} ({ag_name}): final_urls={urls} (unrelated URL, leaving alone)")
            continue
        if GBP_URL in urls and not any(u in urls for u in OLD_URLS):
            print(f"    [SKIP] AG {ag_id} ({ag_name}): already on GBP_URL")
            continue
        rsa = ad["responsiveSearchAd"]

        # Build clone
        op = client.get_type("AdGroupAdOperation")
        new = op.create
        new.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
        new.status = client.enums.AdGroupAdStatusEnum.ENABLED
        new.ad.final_urls.append(GBP_URL)
        r2 = new.ad.responsive_search_ad
        if rsa.get("path1"): r2.path1 = rsa["path1"]
        if rsa.get("path2"): r2.path2 = rsa["path2"]
        for h in rsa["headlines"]:
            ht = client.get_type("AdTextAsset")
            ht.text = h["text"]
            if h.get("pinnedField"):
                ht.pinned_field = getattr(ServedAssetEnum, h["pinnedField"])
            r2.headlines.append(ht)
        for d in rsa["descriptions"]:
            dt = client.get_type("AdTextAsset")
            dt.text = d["text"]
            if d.get("pinnedField"):
                dt.pinned_field = getattr(ServedAssetEnum, d["pinnedField"])
            r2.descriptions.append(dt)

        try:
            resp = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
            new_rn = resp.results[0].resource_name
            print(f"    [OK] AG {ag_id} ({ag_name}): new RSA {new_rn.split('/')[-1]}")
            cloned += 1
        except Exception as e:
            print(f"    [ERR] AG {ag_id} ({ag_name}): clone failed → {str(e)[:200]}")
            continue

        # Pause old
        pop = client.get_type("AdGroupAdOperation")
        pop.update.resource_name = old_rn
        pop.update.status = client.enums.AdGroupAdStatusEnum.PAUSED
        pop.update_mask.CopyFrom(FieldMask(paths=["status"]))
        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[pop])
        paused += 1
    print(f"  Campaign {campaign_id}: {cloned} new RSAs with GBP URL, {paused} old RSAs paused")


def fix_pmax_asset_group():
    """Update the cafe PMax asset group final_url."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("AssetGroupService")

    # Check current final URL
    q = f"""
        SELECT asset_group.id, asset_group.final_urls, asset_group.name
        FROM asset_group
        WHERE asset_group.id = {PMAX_ASSET_GROUP_ID}
    """
    rows = google_gaql(config, q)
    if not rows:
        print(f"  [SKIP] No asset group {PMAX_ASSET_GROUP_ID} found")
        return
    current = rows[0]["assetGroup"].get("finalUrls", [])
    print(f"  Asset group {PMAX_ASSET_GROUP_ID} current final_urls: {current}")
    if GBP_URL in current and not any(u in current for u in OLD_URLS):
        print(f"  [SKIP] Already on correct GBP URL")
        return

    op = client.get_type("AssetGroupOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/assetGroups/{PMAX_ASSET_GROUP_ID}"
    op.update.final_urls.append(GBP_URL)
    op.update_mask.CopyFrom(FieldMask(paths=["final_urls"]))
    svc.mutate_asset_groups(customer_id=CUSTOMER_ID, operations=[op])
    print(f"  [OK] Asset group {PMAX_ASSET_GROUP_ID} final_url → {GBP_URL}")


def fix_sitelinks():
    """Replace sitelinks on cafe-operations campaign — recreate the 4 promo
    sitelinks I added today with GBP_URL as final_url."""
    config = load_config()
    client = _get_google_ads_client(config)

    # The 4 sitelinks I added today (by link_text)
    PROMO_SITELINKS = {
        "Work Day Combo Rs 249":  ("Unlimited Filter Coffee", "+ Sandwich · 2-6 PM"),
        "Couples Combo Rs 399":   ("2 Coffees + Dessert",       "Weekdays · 6-10 PM"),
        "Open till 11 PM":        ("Late-night coffee",         "& desserts, 7 days"),
        "Birthday Parties":       ("Private upper floor",       "From Rs 4,999 / 10 pax"),
    }

    # Find existing campaign_asset + sitelink_asset combinations with these texts
    q = f"""
        SELECT campaign.id, campaign_asset.resource_name,
               asset.resource_name,
               asset.sitelink_asset.link_text,
               asset.final_urls
        FROM campaign_asset
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_asset.field_type = 'SITELINK'
    """
    rows = google_gaql(config, q)

    ca_svc = client.get_service("CampaignAssetService")
    asset_svc = client.get_service("AssetService")

    to_remove_ca = []
    for r in rows:
        text = r["asset"]["sitelinkAsset"]["linkText"]
        urls = r["asset"].get("finalUrls", [])
        # Relink if it's one of our promo sitelinks AND not already on the correct GBP URL
        if text in PROMO_SITELINKS and (GBP_URL not in urls or any(u in urls for u in OLD_URLS)):
            to_remove_ca.append(r["campaignAsset"]["resourceName"])
            print(f"  [UNLINK] sitelink '{text}' (was {urls})")
    if to_remove_ca:
        ops = []
        for rn in to_remove_ca:
            op = client.get_type("CampaignAssetOperation")
            op.remove = rn
            ops.append(op)
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=ops)
        print(f"  [OK] Unlinked {len(ops)} old promo sitelinks")

    # Create fresh sitelink assets with GBP URL
    asset_ops = []
    for text, (d1, d2) in PROMO_SITELINKS.items():
        op = client.get_type("AssetOperation")
        a = op.create
        a.sitelink_asset.link_text = text
        a.sitelink_asset.description1 = d1
        a.sitelink_asset.description2 = d2
        a.final_urls.append(GBP_URL)
        asset_ops.append(op)
    resp = asset_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=asset_ops)
    new_rns = [r.resource_name for r in resp.results]
    print(f"  [OK] Created {len(new_rns)} new promo sitelinks with GBP URL")

    # Link to campaign
    link_ops = []
    for rn in new_rns:
        op = client.get_type("CampaignAssetOperation")
        ca = op.create
        ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
        ca.asset = rn
        ca.field_type = client.enums.AssetFieldTypeEnum.SITELINK
        link_ops.append(op)
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=link_ops)
    print(f"  [OK] Linked {len(link_ops)} new sitelinks to campaign {CAFE_SEARCH_ID}")


def main():
    print("=== Fix cafe ads final_urls → GBP Maps URL ===\n")

    print("1. Cafe-for-sale campaign 23790548087 RSAs:")
    clone_rsas(CAFE_SALE_ID)
    print()

    print("2. Cafe-operations campaign 23778954613 RSAs:")
    clone_rsas(CAFE_SEARCH_ID)
    print()

    print("3. Cafe PMax 23769035916 asset group:")
    fix_pmax_asset_group()
    print()

    print("4. Promo sitelinks on cafe-operations campaign:")
    fix_sitelinks()
    print()

    print("DONE")


if __name__ == "__main__":
    main()
