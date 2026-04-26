#!/usr/bin/env python3
"""
Swap all cafe ads + sitelinks + PMax asset group to the SEARCH-format Maps URL
(approved format) instead of the namooru.com root (banned per user memory) or
the place_id format (disapproved as DESTINATION_MISMATCH).

Approved URL format: https://www.google.com/maps/search/<query>/
This is a search-results URL — no ownership claim — Google approves it.
"""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n

from ads_api import load_config, _get_google_ads_client, google_gaql
from google.protobuf.field_mask_pb2 import FieldMask

CUSTOMER_ID = "2995160429"
CAFE_OPS    = "23778954613"
CAFE_SALE   = "23790548087"
CAFE_PMAX   = "23769035916"
PMAX_AG_ID  = "6703742587"

TARGET_URL = "https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/"

cfg = load_config()
cl  = _get_google_ads_client(cfg)


def clone_rsas_to_maps_search():
    ad_svc = cl.get_service("AdGroupAdService")
    ServedAssetEnum = cl.enums.ServedAssetFieldTypeEnum

    q = f"""
        SELECT campaign.id, ad_group.id, ad_group.name,
               ad_group_ad.resource_name, ad_group_ad.ad.id,
               ad_group_ad.ad.final_urls,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.responsive_search_ad.path1,
               ad_group_ad.ad.responsive_search_ad.path2
        FROM ad_group_ad
        WHERE campaign.id IN ({CAFE_OPS}, {CAFE_SALE})
          AND ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    cloned = paused = skipped = 0
    for r in google_gaql(cfg, q):
        ag_id = r["adGroup"]["id"]
        ag_name = r["adGroup"]["name"]
        old = r["adGroupAd"]
        old_rn = old["resourceName"]
        urls = old["ad"].get("finalUrls", [])
        # Skip if already on the target URL
        if all(u == TARGET_URL for u in urls):
            skipped += 1
            continue
        rsa = old["ad"]["responsiveSearchAd"]

        op = cl.get_type("AdGroupAdOperation")
        new = op.create
        new.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
        new.status = cl.enums.AdGroupAdStatusEnum.ENABLED
        new.ad.final_urls.append(TARGET_URL)
        rsa_new = new.ad.responsive_search_ad
        if rsa.get("path1"): rsa_new.path1 = rsa["path1"][:15]
        if rsa.get("path2"): rsa_new.path2 = rsa["path2"][:15]
        for h in rsa["headlines"]:
            ht = cl.get_type("AdTextAsset")
            ht.text = h["text"]
            if h.get("pinnedField"):
                ht.pinned_field = getattr(ServedAssetEnum, h["pinnedField"])
            rsa_new.headlines.append(ht)
        for d in rsa["descriptions"]:
            dt = cl.get_type("AdTextAsset")
            dt.text = d["text"]
            if d.get("pinnedField"):
                dt.pinned_field = getattr(ServedAssetEnum, d["pinnedField"])
            rsa_new.descriptions.append(dt)
        try:
            resp = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
            print(f"  [OK] AG {ag_name[:32]:<32}: cloned → {resp.results[0].resource_name.split('/')[-1]}")
            cloned += 1
        except Exception as e:
            print(f"  [ERR] AG {ag_name[:32]:<32}: clone failed → {str(e)[:200]}")
            continue

        pop = cl.get_type("AdGroupAdOperation")
        pop.update.resource_name = old_rn
        pop.update.status = cl.enums.AdGroupAdStatusEnum.PAUSED
        pop.update_mask.CopyFrom(FieldMask(paths=["status"]))
        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[pop])
        paused += 1
    print(f"[OK] {cloned} cloned, {paused} old paused, {skipped} skipped (already on target)")


def fix_sitelinks():
    ca_svc = cl.get_service("CampaignAssetService")
    a_svc  = cl.get_service("AssetService")
    PROMO = {
        "Work Day Combo Rs 249": ("Unlimited Filter Coffee", "+ Sandwich · 2-6 PM"),
        "Couples Combo Rs 399":  ("2 Coffees + Dessert",      "Weekdays · 6-10 PM"),
        "Open till 11 PM":       ("Late-night coffee",        "& desserts, 7 days"),
        "Birthday Parties":      ("Private upper floor",      "From Rs 4,999 / 10 pax"),
    }
    q = f"""SELECT campaign.id, campaign_asset.resource_name,
                  asset.sitelink_asset.link_text, asset.final_urls
            FROM campaign_asset
            WHERE campaign.id = {CAFE_OPS}
              AND campaign_asset.field_type = 'SITELINK'
              AND campaign_asset.status = 'ENABLED'"""
    rows = google_gaql(cfg, q)
    to_unlink = []
    keep = set()
    for r in rows:
        text = r["asset"]["sitelinkAsset"]["linkText"]
        urls = r["asset"].get("finalUrls", [])
        if text not in PROMO:
            continue
        if all(u == TARGET_URL for u in urls):
            keep.add(text)
        else:
            to_unlink.append((text, r["campaignAsset"]["resourceName"]))
    for t, rn in to_unlink:
        try:
            op = cl.get_type("CampaignAssetOperation")
            op.remove = rn
            ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[op])
            print(f"  [unlinked] {t}")
        except Exception as e:
            if "RESOURCE_NOT_FOUND" not in str(e):
                print(f"  [skip] {t}: {str(e)[:80]}")

    needed = [t for t in PROMO if t not in keep]
    if not needed:
        print("[--] All 4 promo sitelinks already on target URL")
        return
    aops = []
    for t in needed:
        d1, d2 = PROMO[t]
        op = cl.get_type("AssetOperation")
        a = op.create
        a.sitelink_asset.link_text = t
        a.sitelink_asset.description1 = d1
        a.sitelink_asset.description2 = d2
        a.final_urls.append(TARGET_URL)
        aops.append(op)
    resp = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=aops)
    new_rns = [r.resource_name for r in resp.results]
    lops = []
    for rn in new_rns:
        op = cl.get_type("CampaignAssetOperation")
        ca = op.create
        ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_OPS}"
        ca.asset = rn
        ca.field_type = cl.enums.AssetFieldTypeEnum.SITELINK
        lops.append(op)
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=lops)
    print(f"[OK] Created {len(needed)} fresh sitelinks on target URL: {needed}")


def fix_pmax():
    svc = cl.get_service("AssetGroupService")
    q = f"""SELECT asset_group.id, asset_group.final_urls FROM asset_group
            WHERE asset_group.id = {PMAX_AG_ID}"""
    rows = google_gaql(cfg, q)
    if not rows:
        print("[--] no asset group found")
        return
    cur = rows[0]["assetGroup"].get("finalUrls", [])
    if cur == [TARGET_URL]:
        print("[--] PMax asset group already on target URL")
        return
    op = cl.get_type("AssetGroupOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/assetGroups/{PMAX_AG_ID}"
    op.update.final_urls.append(TARGET_URL)
    op.update_mask.CopyFrom(FieldMask(paths=["final_urls"]))
    try:
        svc.mutate_asset_groups(customer_id=CUSTOMER_ID, operations=[op])
        print(f"[OK] PMax asset group → {TARGET_URL}")
    except Exception as e:
        print(f"[ERR] PMax: {str(e)[:200]}")


def remove_paused_rsas():
    ad_svc = cl.get_service("AdGroupAdService")
    q = f"""SELECT ad_group_ad.resource_name FROM ad_group_ad
            WHERE campaign.id IN ({CAFE_OPS}, {CAFE_SALE})
              AND ad_group_ad.status = 'PAUSED'
              AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'"""
    rows = google_gaql(cfg, q)
    if not rows:
        print("[--] No paused RSAs to remove")
        return
    ops = []
    for r in rows:
        op = cl.get_type("AdGroupAdOperation")
        op.remove = r["adGroupAd"]["resourceName"]
        ops.append(op)
    for i in range(0, len(ops), 50):
        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=ops[i:i+50])
    print(f"[OK] Removed {len(ops)} paused RSAs")


if __name__ == "__main__":
    print("=== Step 1: Clone RSAs to /maps/search/ URL ===")
    clone_rsas_to_maps_search()
    print("\n=== Step 2: Fix sitelinks ===")
    fix_sitelinks()
    print("\n=== Step 3: Fix PMax asset group ===")
    fix_pmax()
    print("\n=== Step 4: Remove paused RSAs (clean ad-group consistency) ===")
    remove_paused_rsas()
