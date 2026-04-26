#!/usr/bin/env python3
"""
One-shot mutation script for BUS Cafe Jayanagar Search + PMax changes (2026-04-24).

Applies:
  - Pause PMax campaign 23769035916
  - Dayparting bid modifiers on Search campaign 23778954613
  - Demographic bid modifiers on all 4 Search ad groups
  - Negative keywords (waste terms from 4-day search-term report)
  - Geo radius tightening + presence-only
  - Promo sitelinks (afternoon / evening / late)

Reuses auth helpers from ads_api.py. Idempotent where possible.

Usage:
    python3 apply_cafe_changes.py <step>
    steps: pause-pmax | dayparting | demographics | negatives | geo | sitelinks | all | verify
"""
import os
# Mac SSL bypass — same posture as ads_api.py (Zscaler / local dev cert issue).
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    import requests
    _orig_req = requests.Session.request
    def _no_verify(self, method, url, **kw):
        kw["verify"] = False
        return _orig_req(self, method, url, **kw)
    requests.Session.request = _no_verify
    # google-auth uses its own Request wrapper
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""

import sys
import json
from ads_api import load_config, _get_google_ads_client, google_gaql

CAFE_SEARCH_ID = "23778954613"
CAFE_PMAX_ID   = "23769035916"
CUSTOMER_ID    = "2995160429"

# Ad group IDs (from campaign restructure 2026-04-24)
AG_CORE = "195096525985"
AG_COUPLE = "193683802457"
AG_BIRTHDAY = "193683802497"
AG_WORK = "193683802537"

ALL_AD_GROUPS = [AG_CORE, AG_COUPLE, AG_BIRTHDAY, AG_WORK]


# ───────────────────────────────────────────────────────────
# 1. PAUSE PMAX
# ───────────────────────────────────────────────────────────

def pause_pmax():
    """Pause the cafe PMax campaign."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("CampaignService")

    op = client.get_type("CampaignOperation")
    campaign = op.update
    campaign.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_PMAX_ID}"
    campaign.status = client.enums.CampaignStatusEnum.PAUSED

    from google.protobuf.field_mask_pb2 import FieldMask
    op.update_mask.CopyFrom(FieldMask(paths=["status"]))

    try:
        resp = svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
        print(f"[OK] PMax paused: {resp.results[0].resource_name}")
        return True
    except Exception as e:
        print(f"[ERR] PMax pause failed: {e}")
        return False


# ───────────────────────────────────────────────────────────
# 2. DAYPARTING BID MODIFIERS
# ───────────────────────────────────────────────────────────

# Rules (7-day same schedule; weekdays and weekends identical for simplicity):
#   08-11  +30%    (breakfast)
#   11-14   0%     (peak; 1.00)
#   14-18  +20%    (afternoon empty-seat fill)
#   18-22  +40%    (evening empty-seat fill)
#   22-23  +10%    (late-night)
#   23-08  no ad schedule = no ads shown (schedule acts as whitelist when any exist)
#
# Google requires hour ranges in [start_hour, end_hour) with minutes
# Bid modifier 1.0 = 0%, 1.30 = +30%, etc.
DAYPARTING = [
    # (start_hour, end_hour, bid_modifier_pct)  ;  0% modifier means bid_modifier=1.00
    (8,  11, 1.30),
    (11, 14, 1.00),
    (14, 18, 1.20),
    (18, 22, 1.40),
    (22, 23, 1.10),
]
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]


def clear_existing_ad_schedules():
    """Remove any existing AD_SCHEDULE criteria on the Search campaign."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("CampaignCriterionService")

    # Pull existing
    query = f"""
        SELECT campaign_criterion.resource_name, campaign_criterion.type
        FROM campaign_criterion
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_criterion.type = 'AD_SCHEDULE'
    """
    rows = google_gaql(config, query)
    ops = []
    for r in rows:
        rn = r["campaignCriterion"]["resourceName"]
        op = client.get_type("CampaignCriterionOperation")
        op.remove = rn
        ops.append(op)

    if not ops:
        print("[OK] No existing ad_schedule criteria to remove")
        return

    resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"[OK] Removed {len(resp.results)} existing ad_schedule criteria")


def apply_dayparting():
    """Add new ad schedule criteria with bid modifiers."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("CampaignCriterionService")

    clear_existing_ad_schedules()

    ops = []
    DayEnum = client.enums.DayOfWeekEnum
    MinuteEnum = client.enums.MinuteOfHourEnum

    for day_str in DAYS:
        day_enum = getattr(DayEnum, day_str)
        for (sh, eh, bm) in DAYPARTING:
            op = client.get_type("CampaignCriterionOperation")
            crit = op.create
            crit.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
            crit.bid_modifier = bm
            crit.ad_schedule.day_of_week = day_enum
            crit.ad_schedule.start_hour = sh
            crit.ad_schedule.end_hour = eh
            crit.ad_schedule.start_minute = MinuteEnum.ZERO
            crit.ad_schedule.end_minute = MinuteEnum.ZERO
            ops.append(op)

    resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"[OK] Added {len(resp.results)} ad_schedule criteria")


# ───────────────────────────────────────────────────────────
# 3. DEMOGRAPHIC BID MODIFIERS
# ───────────────────────────────────────────────────────────

# Google age_range criterion IDs:
#   503001: 18-24, 503002: 25-34, 503003: 35-44, 503004: 45-54,
#   503005: 55-64, 503006: 65+,   503999: UNDETERMINED
AGE_MODIFIERS = {
    503001: 1.10,  # 18-24
    503002: 1.30,  # 25-34
    503003: 1.20,  # 35-44
    503004: 1.00,  # 45-54 baseline (must still exist)
    503005: 0.70,  # 55-64  -30%
    503006: 0.50,  # 65+    -50%
    503999: 0.85,  # UNDETERMINED  -15%
}
# Google gender criterion IDs: 10 MALE, 11 FEMALE, 20 UNDETERMINED
GENDER_MODIFIERS = {
    10: 1.00,   # Male baseline
    11: 1.15,   # Female +15%
    20: 0.90,   # Undetermined -10%
}


def apply_demographics():
    """Add age + gender bid modifiers to each ad group.

    Strategy: remove any existing age_range / gender criteria on each ad group
    then recreate them with our modifiers. Google requires all age/gender buckets
    to exist on an ad group — missing = INCLUDED at 0 modifier.
    """
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("AdGroupCriterionService")

    for ag_id in ALL_AD_GROUPS:
        # Fetch existing age + gender criteria to update in place
        query = f"""
            SELECT ad_group_criterion.resource_name,
                   ad_group_criterion.type,
                   ad_group_criterion.age_range.type,
                   ad_group_criterion.gender.type,
                   ad_group_criterion.criterion_id,
                   ad_group_criterion.bid_modifier
            FROM ad_group_criterion
            WHERE ad_group.id = {ag_id}
              AND ad_group_criterion.type IN ('AGE_RANGE','GENDER')
        """
        rows = google_gaql(config, query)

        ops = []
        existing_ids = {int(r["adGroupCriterion"]["criterionId"]): r["adGroupCriterion"]["resourceName"] for r in rows}

        # Update existing
        for crit_id, resource_name in existing_ids.items():
            if crit_id in AGE_MODIFIERS:
                new_bm = AGE_MODIFIERS[crit_id]
            elif crit_id in GENDER_MODIFIERS:
                new_bm = GENDER_MODIFIERS[crit_id]
            else:
                continue
            op = client.get_type("AdGroupCriterionOperation")
            c = op.update
            c.resource_name = resource_name
            c.bid_modifier = new_bm
            from google.protobuf.field_mask_pb2 import FieldMask
            op.update_mask.CopyFrom(FieldMask(paths=["bid_modifier"]))
            ops.append(op)

        # Create missing
        needed = set(AGE_MODIFIERS.keys()) | set(GENDER_MODIFIERS.keys())
        missing = needed - set(existing_ids.keys())
        AgeEnum = client.enums.AgeRangeTypeEnum
        GenderEnum = client.enums.GenderTypeEnum
        age_map = {503001: "AGE_RANGE_18_24", 503002: "AGE_RANGE_25_34",
                   503003: "AGE_RANGE_35_44", 503004: "AGE_RANGE_45_54",
                   503005: "AGE_RANGE_55_64", 503006: "AGE_RANGE_65_UP",
                   503999: "AGE_RANGE_UNDETERMINED"}
        gender_map = {10: "MALE", 11: "FEMALE", 20: "UNDETERMINED"}

        for crit_id in missing:
            op = client.get_type("AdGroupCriterionOperation")
            c = op.create
            c.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
            if crit_id in AGE_MODIFIERS:
                c.age_range.type_ = getattr(AgeEnum, age_map[crit_id])
                c.bid_modifier = AGE_MODIFIERS[crit_id]
            else:
                c.gender.type_ = getattr(GenderEnum, gender_map[crit_id])
                c.bid_modifier = GENDER_MODIFIERS[crit_id]
            ops.append(op)

        if ops:
            resp = svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
            print(f"[OK] Ad group {ag_id}: {len(resp.results)} demographic criteria mutated")
        else:
            print(f"[--] Ad group {ag_id}: no demographic changes needed")


# ───────────────────────────────────────────────────────────
# 4. NEGATIVE KEYWORDS (campaign-level)
# ───────────────────────────────────────────────────────────

# Waste terms visible in 4-day search-term report — duplicates Google is
# charging for even though a cleaner keyword already matches.
NEGATIVE_KEYWORDS = [
    # Junk "near me near me" permutations
    ("cafe near me near me", "PHRASE"),
    ("near by cafe near me", "PHRASE"),
    ("cafes near by", "PHRASE"),
    ("best cafe near me near me", "PHRASE"),
    ("nearby cafes near me", "PHRASE"),
    # Generic low-intent
    ("cafe jobs", "PHRASE"),
    ("cafe franchise", "PHRASE"),
    ("cafe interior", "PHRASE"),
    ("start a cafe", "PHRASE"),
    ("cafe business plan", "PHRASE"),
    ("cafe music", "PHRASE"),
    # Competitor scout terms
    ("cafe owner", "PHRASE"),
    ("cafe for sale", "PHRASE"),
    ("cafe construction", "PHRASE"),
]


def apply_negatives():
    """Add campaign-level negative keywords (skip any that already exist)."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("CampaignCriterionService")

    # Pull existing campaign-level negatives to avoid duplicates
    query = f"""
        SELECT campaign_criterion.keyword.text,
               campaign_criterion.keyword.match_type
        FROM campaign_criterion
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
    """
    existing = set()
    for r in google_gaql(config, query):
        kw = r.get("campaignCriterion", {}).get("keyword", {})
        existing.add((kw.get("text", "").lower(), kw.get("matchType", "")))

    MatchEnum = client.enums.KeywordMatchTypeEnum
    ops = []
    for text, mt in NEGATIVE_KEYWORDS:
        key = (text.lower(), mt)
        if key in existing:
            continue
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
        c.negative = True
        c.keyword.text = text
        c.keyword.match_type = getattr(MatchEnum, mt)
        ops.append(op)

    if not ops:
        print("[--] All negatives already present, nothing to add")
        return
    resp = svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"[OK] Added {len(resp.results)} campaign-level negatives")


# ───────────────────────────────────────────────────────────
# 5. GEO (presence-only flag + 3.5 km radius)
# ───────────────────────────────────────────────────────────

RADIUS_KM = 3.5


def apply_geo():
    """Switch campaign to Presence-only + replace 5km proximity with 3.5km."""
    config = load_config()
    client = _get_google_ads_client(config)
    svc = client.get_service("CampaignService")
    from google.protobuf.field_mask_pb2 import FieldMask

    # 1. Set Presence-only
    GeoTargetTypeEnum = client.enums.PositiveGeoTargetTypeEnum
    op = client.get_type("CampaignOperation")
    c = op.update
    c.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
    c.geo_target_type_setting.positive_geo_target_type = GeoTargetTypeEnum.PRESENCE
    c.geo_target_type_setting.negative_geo_target_type = client.enums.NegativeGeoTargetTypeEnum.PRESENCE
    op.update_mask.CopyFrom(FieldMask(paths=[
        "geo_target_type_setting.positive_geo_target_type",
        "geo_target_type_setting.negative_geo_target_type",
    ]))
    svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
    print("[OK] Campaign geoTargetTypeSetting → PRESENCE/PRESENCE")

    # 2. Replace proximity(5km → 3.5km) — keep existing center coords
    crit_svc = client.get_service("CampaignCriterionService")
    query = f"""
        SELECT campaign_criterion.resource_name,
               campaign_criterion.proximity.geo_point.latitude_in_micro_degrees,
               campaign_criterion.proximity.geo_point.longitude_in_micro_degrees,
               campaign_criterion.proximity.radius,
               campaign_criterion.proximity.radius_units
        FROM campaign_criterion
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_criterion.type = 'PROXIMITY'
    """
    existing = google_gaql(config, query)
    if not existing:
        print("[WARN] No existing proximity found — skip geo swap (no fallback coords)")
        return

    cur = existing[0]["campaignCriterion"]
    lat_micro = int(cur["proximity"]["geoPoint"]["latitudeInMicroDegrees"])
    lng_micro = int(cur["proximity"]["geoPoint"]["longitudeInMicroDegrees"])
    cur_radius = float(cur["proximity"].get("radius", 0))
    if abs(cur_radius - RADIUS_KM) < 0.05:
        print(f"[--] Proximity already at ~{RADIUS_KM}km, skipping")
        return

    # Remove old, add new in same mutation
    rm_op = client.get_type("CampaignCriterionOperation")
    rm_op.remove = cur["resourceName"]

    ProxUnits = client.enums.ProximityRadiusUnitsEnum
    add_op = client.get_type("CampaignCriterionOperation")
    c2 = add_op.create
    c2.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
    c2.proximity.geo_point.latitude_in_micro_degrees = lat_micro
    c2.proximity.geo_point.longitude_in_micro_degrees = lng_micro
    c2.proximity.radius = RADIUS_KM
    c2.proximity.radius_units = ProxUnits.KILOMETERS

    resp = crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[rm_op, add_op])
    print(f"[OK] Proximity swapped: {cur_radius}km → {RADIUS_KM}km at ({lat_micro/1e6:.4f}, {lng_micro/1e6:.4f})")


# ───────────────────────────────────────────────────────────
# 6. PROMO SITELINKS (campaign-level)
# ───────────────────────────────────────────────────────────

SITELINKS = [
    {
        "text": "Work Day Combo Rs 249",
        "description1": "Unlimited Filter Coffee",
        "description2": "+ Sandwich · 2-6 PM",
    },
    {
        "text": "Couples Combo Rs 399",
        "description1": "2 Coffees + Dessert",
        "description2": "Weekdays · 6-10 PM",
    },
    {
        "text": "Open till 11 PM",
        "description1": "Late-night coffee",
        "description2": "& desserts, 7 days",
    },
    {
        "text": "Birthday Parties",
        "description1": "Private upper floor",
        "description2": "From Rs 4,999 / 10 pax",
    },
]
# GBP Maps URL for BUS Cafe Jayanagar 4th Block — all cafe ads should land here,
# not the resort homepage (namooru.com). Changed 2026-04-24 after user review.
FINAL_URL = (
    "https://www.google.com/maps/place/Brewing+Untold+Stories/"
    "@12.9199786,77.587245,905m/data=!3m2!1e3!4b1!4m6!3m5!"
    "1s0x3bae15fec810a3b3:0xf75b25b8f4c76726!"
    "8m2!3d12.9199786!4d77.5898199!16s%2Fg%2F11w9n2nqks!5m1!1e1"
)


def apply_sitelinks():
    """Create sitelink assets + link to cafe search campaign."""
    config = load_config()
    client = _get_google_ads_client(config)
    asset_svc = client.get_service("AssetService")
    ca_svc = client.get_service("CampaignAssetService")

    # Create sitelink assets
    asset_ops = []
    for sl in SITELINKS:
        op = client.get_type("AssetOperation")
        a = op.create
        a.sitelink_asset.link_text = sl["text"]
        a.sitelink_asset.description1 = sl["description1"]
        a.sitelink_asset.description2 = sl["description2"]
        a.final_urls.append(FINAL_URL)
        asset_ops.append(op)

    resp = asset_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=asset_ops)
    asset_rns = [r.resource_name for r in resp.results]
    print(f"[OK] Created {len(asset_rns)} sitelink assets")

    # Link to campaign
    AssetFieldTypeEnum = client.enums.AssetFieldTypeEnum
    ca_ops = []
    for rn in asset_rns:
        op = client.get_type("CampaignAssetOperation")
        ca = op.create
        ca.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_SEARCH_ID}"
        ca.asset = rn
        ca.field_type = AssetFieldTypeEnum.SITELINK
        ca_ops.append(op)
    resp2 = ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=ca_ops)
    print(f"[OK] Linked {len(resp2.results)} sitelinks to campaign {CAFE_SEARCH_ID}")


# ───────────────────────────────────────────────────────────
# 7. PIN HEADLINE — clone each RSA with "BUS Cafe · Jayanagar 4th Block"
#    pinned to HEADLINE_1, pause the old RSA.
# ───────────────────────────────────────────────────────────

PINNED_HEADLINE_TEXT = "BUS Cafe · Jayanagar 4th Block"

# Per ad group, the brand-name headline to replace with the pinned one
REPLACE_MAP = {
    "195096525985": "Brewing Untold Stories Cafe",  # Core
    "193683802457": "BUS Cafe Jayanagar",            # Couple
    "193683802497": "Brewing Untold Stories",        # Birthday
    "193683802537": "BUS Cafe Jayanagar",            # Work
}


def pin_headline():
    config = load_config()
    client = _get_google_ads_client(config)
    ad_svc = client.get_service("AdGroupAdService")
    ServedAssetEnum = client.enums.ServedAssetFieldTypeEnum

    for ag_id, replace_text in REPLACE_MAP.items():
        # Pull the existing enabled RSA with headlines, descriptions, path, finalUrls
        q = f"""
            SELECT ad_group_ad.resource_name,
                   ad_group_ad.ad.id,
                   ad_group_ad.ad.final_urls,
                   ad_group_ad.ad.responsive_search_ad.headlines,
                   ad_group_ad.ad.responsive_search_ad.descriptions,
                   ad_group_ad.ad.responsive_search_ad.path1,
                   ad_group_ad.ad.responsive_search_ad.path2
            FROM ad_group_ad
            WHERE ad_group.id = {ag_id}
              AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
              AND ad_group_ad.status = 'ENABLED'
        """
        rows = google_gaql(config, q)
        if not rows:
            print(f"[SKIP] AG {ag_id}: no enabled RSA found")
            continue
        old = rows[0]["adGroupAd"]
        old_rn = old["resourceName"]
        old_ad = old["ad"]
        rsa = old_ad["responsiveSearchAd"]
        headlines_src = rsa["headlines"]
        descriptions_src = rsa["descriptions"]
        final_urls = old_ad.get("finalUrls", ["https://namooru.com/"])
        path1 = rsa.get("path1", "")
        path2 = rsa.get("path2", "")

        # Build new RSA: pinned H1 + existing headlines except the replaced one
        new_op = client.get_type("AdGroupAdOperation")
        new = new_op.create
        new.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
        new.status = client.enums.AdGroupAdStatusEnum.ENABLED
        new.ad.final_urls.extend(final_urls)
        rsa_new = new.ad.responsive_search_ad
        if path1: rsa_new.path1 = path1
        if path2: rsa_new.path2 = path2

        # Pinned headline (new)
        h1 = client.get_type("AdTextAsset")
        h1.text = PINNED_HEADLINE_TEXT
        h1.pinned_field = ServedAssetEnum.HEADLINE_1
        rsa_new.headlines.append(h1)

        # Copy remaining headlines except the one we're replacing; cap at 15 total
        kept = 1
        for h in headlines_src:
            if kept >= 15:
                break
            if h["text"].strip().lower() == replace_text.strip().lower():
                continue  # drop the one being replaced
            ht = client.get_type("AdTextAsset")
            ht.text = h["text"]
            # Preserve original pins (there weren't any but handle defensively)
            if h.get("pinnedField") and h["pinnedField"] != "HEADLINE_1":
                ht.pinned_field = getattr(ServedAssetEnum, h["pinnedField"])
            rsa_new.headlines.append(ht)
            kept += 1

        for d in descriptions_src:
            dt = client.get_type("AdTextAsset")
            dt.text = d["text"]
            if d.get("pinnedField"):
                dt.pinned_field = getattr(ServedAssetEnum, d["pinnedField"])
            rsa_new.descriptions.append(dt)

        try:
            resp = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[new_op])
            new_rn = resp.results[0].resource_name
            print(f"[OK] AG {ag_id}: created new RSA {new_rn}")
        except Exception as e:
            print(f"[ERR] AG {ag_id}: create new RSA failed → {e}")
            continue

        # Pause the old RSA (preserve history)
        from google.protobuf.field_mask_pb2 import FieldMask
        pause_op = client.get_type("AdGroupAdOperation")
        p = pause_op.update
        p.resource_name = old_rn
        p.status = client.enums.AdGroupAdStatusEnum.PAUSED
        pause_op.update_mask.CopyFrom(FieldMask(paths=["status"]))
        try:
            ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[pause_op])
            print(f"[OK] AG {ag_id}: paused old RSA {old_rn}")
        except Exception as e:
            print(f"[ERR] AG {ag_id}: pause old RSA failed → {e}")


# ───────────────────────────────────────────────────────────
# 8. VERIFICATION
# ───────────────────────────────────────────────────────────

def verify():
    config = load_config()

    # Campaign status
    q1 = f"""
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.advertising_channel_type,
               campaign.geo_target_type_setting.positive_geo_target_type
        FROM campaign
        WHERE campaign.id IN ({CAFE_SEARCH_ID}, {CAFE_PMAX_ID})
    """
    print("\n=== Campaign status ===")
    for r in google_gaql(config, q1):
        c = r["campaign"]
        gs = c.get("geoTargetTypeSetting", {}).get("positiveGeoTargetType", "?")
        print(f"  {c['id']:>14}  {c['status']:<8}  {c.get('advertisingChannelType','?'):<17}  geo={gs}  {c['name']}")

    # Ad schedules
    q2 = f"""
        SELECT campaign_criterion.ad_schedule.day_of_week,
               campaign_criterion.ad_schedule.start_hour,
               campaign_criterion.ad_schedule.end_hour,
               campaign_criterion.bid_modifier
        FROM campaign_criterion
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_criterion.type = 'AD_SCHEDULE'
        ORDER BY campaign_criterion.ad_schedule.day_of_week,
                 campaign_criterion.ad_schedule.start_hour
    """
    print(f"\n=== Ad schedules (campaign {CAFE_SEARCH_ID}) ===")
    rows = google_gaql(config, q2)
    # show just MONDAY to keep it short; schedules are same every day
    for r in rows:
        s = r["campaignCriterion"]["adSchedule"]
        if s.get("dayOfWeek") != "MONDAY":
            continue
        bm = r["campaignCriterion"].get("bidModifier", 1.0)
        print(f"  {s['dayOfWeek']:<10}  {s['startHour']:>2}:00-{s['endHour']:>2}:00  bid x{bm:.2f}")

    # Negatives count
    q3 = f"""
        SELECT campaign_criterion.keyword.text
        FROM campaign_criterion
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
    """
    rows = google_gaql(config, q3)
    print(f"\n=== Campaign-level negatives ({len(rows)} total) ===  (showing last 10 added)")
    for r in rows[-10:]:
        print(f"  {r['campaignCriterion']['keyword']['text']}")

    # Ad-group demographics
    print(f"\n=== Demographic bid modifiers (all 4 ad groups) ===")
    for ag_id in ALL_AD_GROUPS:
        q4 = f"""
            SELECT ad_group.name,
                   ad_group_criterion.age_range.type,
                   ad_group_criterion.gender.type,
                   ad_group_criterion.bid_modifier
            FROM ad_group_criterion
            WHERE ad_group.id = {ag_id}
              AND ad_group_criterion.type IN ('AGE_RANGE','GENDER')
            ORDER BY ad_group_criterion.type
        """
        rows = google_gaql(config, q4)
        if rows:
            name = rows[0]["adGroup"]["name"]
            print(f"  AG {ag_id} ({name}):")
            for r in rows:
                c = r["adGroupCriterion"]
                bm = c.get("bidModifier", 1.0)
                dim = c.get("ageRange", {}).get("type") or c.get("gender", {}).get("type")
                print(f"     {dim:<24}  x{bm:.2f}")

    # Sitelinks
    q5 = f"""
        SELECT asset.sitelink_asset.link_text,
               asset.resource_name
        FROM campaign_asset
        WHERE campaign.id = {CAFE_SEARCH_ID}
          AND campaign_asset.field_type = 'SITELINK'
    """
    rows = google_gaql(config, q5)
    print(f"\n=== Sitelinks on campaign ({len(rows)} total) ===")
    for r in rows:
        print(f"  {r['asset']['sitelinkAsset']['linkText']}")


# ───────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────

STEPS = {
    "pause-pmax": pause_pmax,
    "dayparting": apply_dayparting,
    "demographics": apply_demographics,
    "negatives": apply_negatives,
    "geo": apply_geo,
    "sitelinks": apply_sitelinks,
    "pin-headline": pin_headline,
    "verify": verify,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 apply_cafe_changes.py <step>")
        print(f"Steps: {', '.join(STEPS.keys())}, all")
        sys.exit(1)
    step = sys.argv[1]
    if step == "all":
        for name in ["pause-pmax", "dayparting", "demographics", "negatives", "geo", "sitelinks"]:
            print(f"\n─── {name.upper()} ───")
            STEPS[name]()
        print("\n─── VERIFY ───")
        verify()
    elif step in STEPS:
        STEPS[step]()
    else:
        print(f"Unknown step: {step}")
        sys.exit(1)


if __name__ == "__main__":
    main()
