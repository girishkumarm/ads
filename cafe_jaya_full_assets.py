#!/usr/bin/env python3
"""Jayanagar Cafe Search — go end-to-end on Google Ads asset capabilities.

Phase 1: Add 8 new callouts (11 total — Google's max use)
Phase 2: Add 2 structured snippets (Service catalog + Featured)
Phase 3: Add 3 sitelinks (8 total)
Phase 4: Add Business Name asset
Phase 5: Per-AG callouts for differentiation (Events / Work / Couple / Competitors / Core)

Skipped (need human-side setup):
- Lead Form  (form fields, privacy URL, follow-up message)
- Hotel Callout (N/A for cafe)
- App / Affiliate / Mobile (N/A)
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
a_svc  = cl.get_service("AssetService")
ca_svc = cl.get_service("CampaignAssetService")
aga_svc = cl.get_service("AdGroupAssetService")


def make_callout(text):
    op = cl.get_type("AssetOperation")
    op.create.callout_asset.callout_text = text
    return op


def make_sitelink(link_text, desc1, desc2, url=TARGET_URL):
    op = cl.get_type("AssetOperation")
    a = op.create
    a.sitelink_asset.link_text = link_text
    a.sitelink_asset.description1 = desc1
    a.sitelink_asset.description2 = desc2
    a.final_urls.append(url)
    return op


def make_snippet(header, values):
    op = cl.get_type("AssetOperation")
    a = op.create.structured_snippet_asset
    a.header = header
    a.values.extend(values)
    return op


def make_business_name(name):
    op = cl.get_type("AssetOperation")
    a = op.create.business_name_asset
    a.business_name = name
    return op


def link_to_campaign(asset_rn, field_type_enum):
    op = cl.get_type("CampaignAssetOperation")
    op.create.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMP_ID}"
    op.create.asset = asset_rn
    op.create.field_type = field_type_enum
    return op


def link_to_adgroup(ag_id, asset_rn, field_type_enum):
    op = cl.get_type("AdGroupAssetOperation")
    op.create.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"
    op.create.asset = asset_rn
    op.create.field_type = field_type_enum
    return op


# ─── PHASE 1: Campaign-level callouts ──────────────────────────
print("="*78)
print("PHASE 1: 8 NEW CAMPAIGN-LEVEL CALLOUTS")
print("="*78)
NEW_CALLOUTS = [
    "AC Cafe",
    "Open Till Midnight",
    "Birthday Party Venue",
    "Outdoor Seating",
    "Pet-Friendly Space",
    "Cards & UPI Accepted",
    "Fresh Roasted Coffee",
    "Quiet Work Cabins",
]
created_callouts = []
for text in NEW_CALLOUTS:
    try:
        r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[make_callout(text)])
        rn = r.results[0].resource_name
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID,
            operations=[link_to_campaign(rn, cl.enums.AssetFieldTypeEnum.CALLOUT)])
        print(f"  [OK] '{text}'")
        created_callouts.append((text, rn))
    except Exception as e:
        print(f"  [FAIL] '{text}': {str(e)[:150]}")


# ─── PHASE 2: Structured snippets (Service catalog + Featured) ─────
print(f"\n{'='*78}")
print("PHASE 2: 2 NEW STRUCTURED SNIPPETS")
print("="*78)
NEW_SNIPPETS = [
    ("Service catalog", ["Specialty Coffee","Pizza","Pasta","Smoothies","Desserts","Breakfast"]),
    ("Featured",        ["Saturday Special","Birthday Bookings","Couple Combos","Work Cabins","Late Night Eats"]),
]
for header, vals in NEW_SNIPPETS:
    try:
        r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[make_snippet(header, vals)])
        rn = r.results[0].resource_name
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID,
            operations=[link_to_campaign(rn, cl.enums.AssetFieldTypeEnum.STRUCTURED_SNIPPET)])
        print(f"  [OK] {header}: {vals}")
    except Exception as e:
        print(f"  [FAIL] {header}: {str(e)[:200]}")


# ─── PHASE 3: 3 new sitelinks ───────────────────────────────
print(f"\n{'='*78}")
print("PHASE 3: 3 NEW SITELINKS (total 8)")
print("="*78)
NEW_SITELINKS = [
    ("Combo Deals",       "Rs 499 unlimited combos",  "Coffee + Pizza + Sides"),
    ("Birthday Bookings", "Cake cutting · Decor",     "Group rates available"),
    ("Late Night Open",   "Open till 12 AM daily",    "1+1 ice cream after 10"),
]
for link, d1, d2 in NEW_SITELINKS:
    try:
        r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[make_sitelink(link, d1, d2)])
        rn = r.results[0].resource_name
        ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID,
            operations=[link_to_campaign(rn, cl.enums.AssetFieldTypeEnum.SITELINK)])
        print(f"  [OK] '{link}'")
    except Exception as e:
        print(f"  [FAIL] '{link}': {str(e)[:200]}")


# ─── PHASE 4: Business Name asset ─────────────────────────────
print(f"\n{'='*78}")
print("PHASE 4: BUSINESS NAME ASSET")
print("="*78)
try:
    r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[make_business_name("BUS Cafe Jayanagar")])
    rn = r.results[0].resource_name
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID,
        operations=[link_to_campaign(rn, cl.enums.AssetFieldTypeEnum.BUSINESS_NAME)])
    print(f"  [OK] 'BUS Cafe Jayanagar'")
except Exception as e:
    print(f"  [FAIL] business_name: {str(e)[:300]}")


# ─── PHASE 5: Per-AG callouts for differentiation ─────────
print(f"\n{'='*78}")
print("PHASE 5: PER-AD-GROUP CALLOUTS (differentiation)")
print("="*78)

# Get current AG IDs
q = f"""SELECT ad_group.id, ad_group.name FROM ad_group
        WHERE campaign.id = {CAMP_ID} AND ad_group.status = 'ENABLED'"""
ags = {r["adGroup"]["name"]: r["adGroup"]["id"] for r in google_gaql(cfg, q)}
print(f"  Found AGs: {list(ags.keys())}\n")

PER_AG_CALLOUTS = {
    "Events - Jayanagar": ["Cake Cutting Decor", "Surprise Party Setup", "Photographer On Request", "Group Combo Deals"],
    "Work & Laptop Friendly - Jayanagar": ["5G WiFi & Power Plugs", "Quiet Cabins Available", "Free Coffee Refills", "Open till Midnight"],
    "Couple Outing - Jayanagar": ["Candle Light Tables", "Couple Combo Rs 399", "Romantic Privacy Booths", "Anniversary Specials"],
    "Competitors - Jayanagar": ["Better Coffee Than CCD", "Affordable Local Cafe", "Cozy Independent Spot", "Faster Service"],
    "Jayanagar Cafe - Core Keywords": ["Best Reviewed in Jayanagar", "4.7-Star Rated", "Fresh Daily Bakes", "AC Indoor Seating"],
}
for ag_name, callouts in PER_AG_CALLOUTS.items():
    ag_id = ags.get(ag_name)
    if not ag_id:
        print(f"  [skip] AG '{ag_name}' not found")
        continue
    print(f"  AG '{ag_name}' (id={ag_id}):")
    for text in callouts:
        try:
            r = a_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[make_callout(text)])
            rn = r.results[0].resource_name
            aga_svc.mutate_ad_group_assets(customer_id=CUSTOMER_ID,
                operations=[link_to_adgroup(ag_id, rn, cl.enums.AssetFieldTypeEnum.CALLOUT)])
            print(f"    [OK] '{text}'")
        except Exception as e:
            print(f"    [FAIL] '{text}': {str(e)[:120]}")


# ─── Summary ───────────────────────────────────────────────
print(f"\n{'='*78}")
print("SUMMARY")
print("="*78)
q = f"""SELECT campaign.id, campaign_asset.field_type
        FROM campaign_asset
        WHERE campaign.id = {CAMP_ID}
          AND campaign_asset.status = 'ENABLED'"""
counts = {}
for r in google_gaql(cfg, q):
    ft = r["campaignAsset"]["fieldType"]
    counts[ft] = counts.get(ft, 0) + 1
print("Final campaign-level asset counts:")
for ft, n in sorted(counts.items()):
    print(f"  {ft:<22} {n}")

q2 = f"""SELECT campaign.id, ad_group.id, ad_group_asset.field_type
        FROM ad_group_asset
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_asset.status = 'ENABLED'"""
ag_counts = {}
for r in google_gaql(cfg, q2):
    ft = r["adGroupAsset"]["fieldType"]
    ag_counts[ft] = ag_counts.get(ft, 0) + 1
print("\nAd-group-level asset counts:")
for ft, n in sorted(ag_counts.items()):
    print(f"  {ft:<22} {n}")
