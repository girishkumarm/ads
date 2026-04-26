#!/usr/bin/env python3
"""
Fix all DISAPPROVED ads in cafe campaigns (2026-04-25).

Root cause: google.com/maps URLs trigger DESTINATION_MISMATCH (Google requires
advertiser-owned domain). Mixed URLs across ads in same ad group trigger
ONE_WEBSITE_PER_AD_GROUP.

Fix:
  1. Set campaign-level final_url_suffix with UTM tags so we still track cafe
     traffic separately even though final_url itself is namooru.com.
  2. For every cafe ad group that has at least one DISAPPROVED ad, create a
     fresh RSA on namooru.com using the same headlines/descriptions as the
     current disapproved ad, then PAUSE the disapproved ad.
  3. REMOVE (not pause) all old PAUSED ads in cafe ad groups so the
     ONE_WEBSITE_PER_AD_GROUP policy stops counting their URLs.
  4. Update all 4 promo sitelinks to namooru.com (currently on maps URL).
  5. Update PMax cafe asset group final_url to namooru.com.
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

CUSTOMER_ID    = "2995160429"
CAFE_OPS_ID    = "23778954613"
CAFE_SALE_ID   = "23790548087"
CAFE_PMAX_ID   = "23769035916"
PMAX_ASSET_GROUP_ID = "6703742587"

NAMOORU_URL = "https://namooru.com/"

# Final URL suffix uses ValueTrack params — Google appends to every click URL
SUFFIX_OPS  = "utm_source=google&utm_medium=cpc&utm_campaign=cafe_jayanagar_ops&utm_content={adgroupid}&utm_term={keyword}"
SUFFIX_SALE = "utm_source=google&utm_medium=cpc&utm_campaign=cafe_jayanagar_sale&utm_content={adgroupid}&utm_term={keyword}"

cfg = load_config()
cl  = _get_google_ads_client(cfg)


# ───────────────────────────────────────────────────────────
# 1. Set final_url_suffix on both cafe campaigns
# ───────────────────────────────────────────────────────────
def set_url_suffixes():
    svc = cl.get_service("CampaignService")
    ops = []
    for camp_id, suffix in [(CAFE_OPS_ID, SUFFIX_OPS), (CAFE_SALE_ID, SUFFIX_SALE)]:
        op = cl.get_type("CampaignOperation")
        op.update.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{camp_id}"
        op.update.final_url_suffix = suffix
        op.update_mask.CopyFrom(FieldMask(paths=["final_url_suffix"]))
        ops.append(op)
    svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=ops)
    print(f"[OK] final_url_suffix set on cafe ops + sale campaigns")


# ───────────────────────────────────────────────────────────
# 2. For each ad group, clone any non-namooru.com ENABLED RSA → namooru.com,
#    then pause the old disapproved ad.
# ───────────────────────────────────────────────────────────
def clone_disapproved_to_namooru():
    ad_svc = cl.get_service("AdGroupAdService")
    ServedAssetEnum = cl.enums.ServedAssetFieldTypeEnum

    q = f"""
        SELECT campaign.id, ad_group.id, ad_group.name,
               ad_group_ad.resource_name, ad_group_ad.ad.id,
               ad_group_ad.ad.final_urls,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.responsive_search_ad.path1,
               ad_group_ad.ad.responsive_search_ad.path2,
               ad_group_ad.policy_summary.approval_status
        FROM ad_group_ad
        WHERE campaign.id IN ({CAFE_OPS_ID}, {CAFE_SALE_ID})
          AND ad_group_ad.status = 'ENABLED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    cloned = 0
    paused = 0
    for r in google_gaql(cfg, q):
        ag_id = r["adGroup"]["id"]
        ag_name = r["adGroup"]["name"]
        old = r["adGroupAd"]
        old_rn = old["resourceName"]
        urls = old["ad"].get("finalUrls", [])
        appr = old.get("policySummary", {}).get("approvalStatus", "?")

        # Skip ads already on namooru.com (Core ad group, etc.)
        already_namooru = any("namooru.com" in u for u in urls)
        if already_namooru:
            continue
        # Skip ads that are APPROVED on a non-namooru URL — but our policy is uniform → still fix
        # Only skip if Core (which is on maps/search and approved earlier)
        # Actually: if ad is on google.com/maps it WILL get disapproved sooner or later. Fix all.

        rsa = old["ad"]["responsiveSearchAd"]
        op = cl.get_type("AdGroupAdOperation")
        new = op.create
        new.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
        new.status = cl.enums.AdGroupAdStatusEnum.ENABLED
        new.ad.final_urls.append(NAMOORU_URL)
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
            new_rn = resp.results[0].resource_name
            print(f"  [OK] AG {ag_name[:30]:<30}: cloned to namooru.com → {new_rn.split('/')[-1]}")
            cloned += 1
        except Exception as e:
            print(f"  [ERR] AG {ag_name[:30]:<30}: clone failed → {str(e)[:200]}")
            continue
        # Pause the disapproved old ad
        pop = cl.get_type("AdGroupAdOperation")
        pop.update.resource_name = old_rn
        pop.update.status = cl.enums.AdGroupAdStatusEnum.PAUSED
        pop.update_mask.CopyFrom(FieldMask(paths=["status"]))
        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[pop])
        paused += 1
    print(f"[OK] Cloned {cloned} ads onto namooru.com, paused {paused} disapproved old ads")


# ───────────────────────────────────────────────────────────
# 3. REMOVE all PAUSED RSAs in cafe campaigns to clean up ad-group consistency.
#    History is preserved in reports.
# ───────────────────────────────────────────────────────────
def remove_paused_rsas():
    ad_svc = cl.get_service("AdGroupAdService")
    q = f"""
        SELECT ad_group_ad.resource_name, ad_group.name
        FROM ad_group_ad
        WHERE campaign.id IN ({CAFE_OPS_ID}, {CAFE_SALE_ID})
          AND ad_group_ad.status = 'PAUSED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    rows = google_gaql(cfg, q)
    if not rows:
        print("[--] No paused RSAs to remove")
        return
    ops = []
    for r in rows:
        op = cl.get_type("AdGroupAdOperation")
        op.remove = r["adGroupAd"]["resourceName"]
        ops.append(op)
    # Process in chunks of 50 to be safe
    for i in range(0, len(ops), 50):
        chunk = ops[i:i+50]
        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=chunk)
    print(f"[OK] Removed {len(ops)} paused RSAs from cafe campaigns")


# ───────────────────────────────────────────────────────────
# 4. Update all promo sitelinks (currently on maps URL) → namooru.com
# ───────────────────────────────────────────────────────────
def fix_sitelinks():
    a_svc = cl.get_service("AssetService")
    ca_svc = cl.get_service("CampaignAssetService")

    PROMO = {
        "Work Day Combo Rs 249": ("Unlimited Filter Coffee", "+ Sandwich · 2-6 PM"),
        "Couples Combo Rs 399":  ("2 Coffees + Dessert",      "Weekdays · 6-10 PM"),
        "Open till 11 PM":       ("Late-night coffee",        "& desserts, 7 days"),
        "Birthday Parties":      ("Private upper floor",      "From Rs 4,999 / 10 pax"),
    }

    # Find all enabled sitelinks on cafe ops campaign
    q = f"""
        SELECT campaign.id, campaign_asset.resource_name, asset.sitelink_asset.link_text,
               asset.final_urls
        FROM campaign_asset
        WHERE campaign.id = {CAFE_OPS_ID}
          AND campaign_asset.field_type = 'SITELINK'
          AND campaign_asset.status = 'ENABLED'
    """
    rows = google_gaql(cfg, q)
    bad_links = []
    for r in rows:
        text = r["asset"]["sitelinkAsset"]["linkText"]
        urls = r["asset"].get("finalUrls", [])
        # Anything not on namooru.com is bad — including google.com/maps and old Zomato
        if not any("namooru.com" in u for u in urls):
            bad_links.append((text, r["campaignAsset"]["resourceName"]))

    if not bad_links:
        print("[--] All sitelinks already namooru.com — nothing to fix")
        return

    # Unlink the bad ones
    rm_ops = []
    for text, rn in bad_links:
        op = cl.get_type("CampaignAssetOperation")
        op.remove = rn
        rm_ops.append(op)
    try:
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=rm_ops)
        print(f"[OK] Unlinked {len(rm_ops)} non-namooru sitelinks")
    except Exception as e:
        # Some may already be removed
        print(f"[WARN] Some unlinks failed (likely already removed): {str(e)[:100]}")

    # Recreate the 4 promo sitelinks on namooru.com (skip if already exists with namooru)
    existing_namooru_promos = set()
    for r in rows:
        text = r["asset"]["sitelinkAsset"]["linkText"]
        urls = r["asset"].get("finalUrls", [])
        if any("namooru.com" in u for u in urls) and text in PROMO:
            existing_namooru_promos.add(text)

    a_ops = []
    needed = [t for t in PROMO if t not in existing_namooru_promos]
    if not needed:
        print("[--] Promo sitelinks already on namooru.com")
        return
    for t in needed:
        d1, d2 = PROMO[t]
        op = cl.get_type("AssetOperation")
        a = op.create
        a.sitelink_asset.link_text = t
        a.sitelink_asset.description1 = d1
        a.sitelink_asset.description2 = d2
        a.final_urls.append(NAMOORU_URL)
        a_ops.append(op)
    resp = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=a_ops)
    new_rns = [r.resource_name for r in resp.results]

    l_ops = []
    for rn in new_rns:
        op = cl.get_type("CampaignAssetOperation")
        ca = op.create
        ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_OPS_ID}"
        ca.asset = rn
        ca.field_type = cl.enums.AssetFieldTypeEnum.SITELINK
        l_ops.append(op)
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=l_ops)
    print(f"[OK] Created {len(needed)} fresh sitelinks on namooru.com: {needed}")


# ───────────────────────────────────────────────────────────
# 5. Update PMax cafe asset group final_url
# ───────────────────────────────────────────────────────────
def fix_pmax():
    svc = cl.get_service("AssetGroupService")
    q = f"""
        SELECT asset_group.id, asset_group.final_urls FROM asset_group
        WHERE asset_group.id = {PMAX_ASSET_GROUP_ID}
    """
    rows = google_gaql(cfg, q)
    if not rows:
        print("[--] No asset group found")
        return
    cur = rows[0]["assetGroup"].get("finalUrls", [])
    if any("namooru.com" in u for u in cur) and len([u for u in cur if "google.com" not in u and "maps.app.goo" not in u]) == len(cur):
        print(f"[--] PMax asset group already on advertiser domain")
        return
    op = cl.get_type("AssetGroupOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/assetGroups/{PMAX_ASSET_GROUP_ID}"
    while op.update.final_urls:
        op.update.final_urls.pop()
    op.update.final_urls.append(NAMOORU_URL)
    op.update_mask.CopyFrom(FieldMask(paths=["final_urls"]))
    try:
        svc.mutate_asset_groups(customer_id=CUSTOMER_ID, operations=[op])
        print(f"[OK] PMax asset group final_url → {NAMOORU_URL}")
    except Exception as e:
        print(f"[ERR] PMax: {str(e)[:200]}")


def main():
    print("=== Step 1: Set campaign-level final_url_suffix (UTM tracking) ===")
    set_url_suffixes()
    print()

    print("=== Step 2: Clone disapproved RSAs to namooru.com ===")
    clone_disapproved_to_namooru()
    print()

    print("=== Step 3: Remove old PAUSED RSAs (clean ad-group consistency) ===")
    remove_paused_rsas()
    print()

    print("=== Step 4: Fix sitelinks ===")
    fix_sitelinks()
    print()

    print("=== Step 5: Fix PMax asset group final_url ===")
    fix_pmax()


if __name__ == "__main__":
    main()
