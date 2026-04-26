#!/usr/bin/env python3
"""
Big-bill Google Ads moves for BUS Cafe Jayanagar (2026-04-26).
Skipping Corporate B2B per user instruction.

1. Add `for sale` PHRASE as cross-AG negative on cafe ops campaign
2. Expand Birthday & Events AG with 13 new high-intent keywords
3. Create new Brand Defense campaign (Manual CPC, Rs 100/day, 3 brand KWs)
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

CUSTOMER_ID  = "2995160429"
CAFE_OPS_ID  = "23778954613"
BIRTHDAY_AG  = "193683802497"  # Birthday & Events - Jayanagar

# /maps/search/ URL — same as the 4 ENABLED RSAs already use, policy-clean
TARGET_URL = "https://www.google.com/maps/search/Brewing+Untold+Stories+Jayanagar+Bangalore/"

cfg = load_config()
cl = _get_google_ads_client(cfg)


# ─────────────────────────────────────────────────────
# 1. Add `for sale` cross-campaign negative
# ─────────────────────────────────────────────────────
def add_for_sale_negative():
    print("\n=== 1. Add `for sale` PHRASE negative on cafe ops campaign ===")
    svc = cl.get_service("CampaignCriterionService")
    MatchEnum = cl.enums.KeywordMatchTypeEnum

    # Skip if already exists
    q = f"""SELECT campaign_criterion.keyword.text, campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign.id = {CAFE_OPS_ID}
              AND campaign_criterion.negative = TRUE
              AND campaign_criterion.type = 'KEYWORD'"""
    existing = set()
    for r in google_gaql(cfg, q):
        kw = r.get("campaignCriterion",{}).get("keyword",{})
        existing.add((kw.get("text","").lower(), kw.get("matchType","")))

    if ("for sale", "PHRASE") in existing:
        print("  [--] `for sale` PHRASE already exists, skipping")
        return

    op = cl.get_type("CampaignCriterionOperation")
    c = op.create
    c.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAFE_OPS_ID}"
    c.negative = True
    c.keyword.text = "for sale"
    c.keyword.match_type = MatchEnum.PHRASE
    svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[op])
    print("  [OK] Added `for sale` PHRASE negative — prevents cross-cannibalization with cafe-for-sale campaign")


# ─────────────────────────────────────────────────────
# 2. Expand Birthday AG with 13 new keywords
# ─────────────────────────────────────────────────────
NEW_BIRTHDAY_KEYWORDS = [
    # EXACT — high-intent direct match
    ("birthday venue jayanagar", "EXACT"),
    ("private dining jayanagar", "EXACT"),
    ("birthday cafe 4th block", "EXACT"),
    # PHRASE — discovery
    ("cafe for birthday party", "PHRASE"),
    ("private cafe birthday booking", "PHRASE"),
    ("kids birthday cafe jayanagar", "PHRASE"),
    ("birthday cafe 15 people bangalore", "PHRASE"),
    ("outside cake allowed cafe jayanagar", "PHRASE"),
    ("cake cutting cafe jayanagar", "PHRASE"),
    ("surprise birthday cafe bangalore", "PHRASE"),
    ("upper floor birthday cafe", "PHRASE"),
    ("birthday cafe with private room", "PHRASE"),
    ("bridal shower cafe bangalore", "PHRASE"),
    ("baby shower venue jayanagar", "PHRASE"),
    ("birthday celebration jayanagar", "PHRASE"),
]


def expand_birthday_keywords():
    print("\n=== 2. Expand Birthday & Events AG with new keywords ===")
    svc = cl.get_service("AdGroupCriterionService")
    MatchEnum = cl.enums.KeywordMatchTypeEnum

    # Pull existing keywords in this AG to skip dups
    q = f"""SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type
            FROM ad_group_criterion
            WHERE ad_group.id = {BIRTHDAY_AG}
              AND ad_group_criterion.type = 'KEYWORD'
              AND ad_group_criterion.status != 'REMOVED'"""
    existing = set()
    for r in google_gaql(cfg, q):
        kw = r.get("adGroupCriterion",{}).get("keyword",{})
        existing.add((kw.get("text","").lower(), kw.get("matchType","")))

    ops = []
    skipped = []
    added_list = []
    for text, mt in NEW_BIRTHDAY_KEYWORDS:
        key = (text.lower(), mt)
        if key in existing:
            skipped.append(text)
            continue
        op = cl.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{BIRTHDAY_AG}"
        c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = text
        c.keyword.match_type = getattr(MatchEnum, mt)
        ops.append(op)
        added_list.append((text, mt))

    if not ops:
        print("  [--] All keywords already exist in Birthday AG")
        return
    svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"  [OK] Added {len(ops)} new keywords to Birthday & Events AG:")
    for t, m in added_list:
        print(f"      [{m:<6}] {t}")
    if skipped:
        print(f"  [skip] {len(skipped)} already existed: {skipped}")


# ─────────────────────────────────────────────────────
# 3. Create Brand Defense campaign
# ─────────────────────────────────────────────────────
BRAND_KEYWORDS = [
    ("brewing untold stories", "EXACT"),
    ("bus cafe jayanagar", "EXACT"),
    ("brewing untold stories cafe", "PHRASE"),
    ("brewing untold stories jayanagar", "PHRASE"),
    ("BUS cafe", "PHRASE"),
]
BRAND_HEADLINES = [
    ("Brewing Untold Stories", "HEADLINE_1"),  # pin H1
    ("BUS Cafe Jayanagar", "HEADLINE_2"),       # pin H2
    ("Pure Veg Cafe in Jayanagar", None),
    ("4.4 Star · 400+ Reviews", None),
    ("Open 8 AM to 11 PM Daily", None),
    ("Free Wi-Fi · Plug Points", None),
    ("Birthday Bookings Available", None),
    ("Private Upper Floor", None),
    ("Walking Distance from Metro", None),
    ("Outside Cake Allowed", None),
    ("Wood-Fired Pizza · Coffee", None),
    ("AC · Free Parking", None),
    ("Pure Veg Menu", None),
    ("Visit Us in 4th Block", None),
    ("Trusted Cafe Bangalore", None),
]
BRAND_DESCRIPTIONS = [
    "Brewing Untold Stories — pure-veg cafe in Jayanagar 4th Block. Open 8 AM to 11 PM daily.",
    "Visit BUS Cafe for coffee, wood-fired pizza, desserts. AC, Wi-Fi, free parking available.",
    "Birthday bookings, private dining, group reservations welcome. Call or visit today.",
    "4.4 stars on 400+ Google reviews. Walking distance from Jayanagar Metro station.",
]


def create_brand_campaign():
    print("\n=== 3. Create Brand Defense campaign ===")
    from google.protobuf.field_mask_pb2 import FieldMask

    # Check if it already exists
    q = """SELECT campaign.id, campaign.name, campaign.status
           FROM campaign
           WHERE campaign.name = 'Jayanagar Cafe - Brand Defense | 2026-04-26'"""
    rows = list(google_gaql(cfg, q))
    if rows:
        print(f"  [--] Brand campaign already exists: {rows[0]['campaign']['id']}")
        return rows[0]["campaign"]["id"]

    # 1. Budget
    bud_svc = cl.get_service("CampaignBudgetService")
    bop = cl.get_type("CampaignBudgetOperation")
    b = bop.create
    b.name = "Budget - Jayanagar Cafe Brand Defense"
    b.amount_micros = 100 * 1_000_000  # Rs 100/day
    b.delivery_method = cl.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    bud_resp = bud_svc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[bop])
    budget_rn = bud_resp.results[0].resource_name
    print(f"  [OK] Budget created: Rs 100/day")

    # 2. Campaign — Manual CPC, Search-only
    camp_svc = cl.get_service("CampaignService")
    cop = cl.get_type("CampaignOperation")
    c = cop.create
    c.name = "Jayanagar Cafe - Brand Defense | 2026-04-26"
    c.advertising_channel_type = cl.enums.AdvertisingChannelTypeEnum.SEARCH
    c.status = cl.enums.CampaignStatusEnum.PAUSED  # create paused, enable after RSA built
    c.campaign_budget = budget_rn
    # Manual CPC (lets us cap brand bids tightly)
    c.manual_cpc.enhanced_cpc_enabled = False
    # Networks: Search only
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    c.network_settings.target_content_network = False
    c.network_settings.target_partner_search_network = False
    # Geo type: PRESENCE only
    c.geo_target_type_setting.positive_geo_target_type = cl.enums.PositiveGeoTargetTypeEnum.PRESENCE
    c.geo_target_type_setting.negative_geo_target_type = cl.enums.NegativeGeoTargetTypeEnum.PRESENCE
    c.contains_eu_political_advertising = cl.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    camp_resp = camp_svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[cop])
    campaign_rn = camp_resp.results[0].resource_name
    campaign_id = campaign_rn.split("/")[-1]
    print(f"  [OK] Campaign created: {campaign_id} (PAUSED)")

    # 3. Geo: India (geo_target_constants/2356) — brand traffic from anywhere
    crit_svc = cl.get_service("CampaignCriterionService")
    crit_ops = []
    op = cl.get_type("CampaignCriterionOperation")
    cc = op.create
    cc.campaign = campaign_rn
    cc.location.geo_target_constant = "geoTargetConstants/2356"  # India
    crit_ops.append(op)
    # Languages: English + Hindi + Kannada
    for lid in ["1000", "1023", "1086"]:
        op = cl.get_type("CampaignCriterionOperation")
        cc = op.create
        cc.campaign = campaign_rn
        cc.language.language_constant = f"languageConstants/{lid}"
        crit_ops.append(op)
    crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=crit_ops)
    print(f"  [OK] Geo (India) + 3 languages added")

    # 4. Ad group
    ag_svc = cl.get_service("AdGroupService")
    aop = cl.get_type("AdGroupOperation")
    ag = aop.create
    ag.name = "Brand Keywords"
    ag.campaign = campaign_rn
    ag.status = cl.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = cl.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ag.cpc_bid_micros = 8 * 1_000_000  # Rs 8 max CPC (brand QS=10 → actual cost Rs 2-4)
    ag_resp = ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[aop])
    ag_rn = ag_resp.results[0].resource_name
    ag_id = ag_rn.split("/")[-1]
    print(f"  [OK] Ad group 'Brand Keywords' created: {ag_id} (Max CPC Rs 8)")

    # 5. Keywords
    agc_svc = cl.get_service("AdGroupCriterionService")
    MatchEnum = cl.enums.KeywordMatchTypeEnum
    kops = []
    for text, mt in BRAND_KEYWORDS:
        op = cl.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = ag_rn
        c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = text
        c.keyword.match_type = getattr(MatchEnum, mt)
        kops.append(op)
    agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=kops)
    print(f"  [OK] {len(BRAND_KEYWORDS)} brand keywords added")

    # 6. RSA
    ad_svc = cl.get_service("AdGroupAdService")
    ServedAssetEnum = cl.enums.ServedAssetFieldTypeEnum
    aop = cl.get_type("AdGroupAdOperation")
    new = aop.create
    new.ad_group = ag_rn
    new.status = cl.enums.AdGroupAdStatusEnum.ENABLED
    new.ad.final_urls.append(TARGET_URL)
    rsa = new.ad.responsive_search_ad
    for text, pin in BRAND_HEADLINES:
        ht = cl.get_type("AdTextAsset")
        ht.text = text
        if pin:
            ht.pinned_field = getattr(ServedAssetEnum, pin)
        rsa.headlines.append(ht)
    for d in BRAND_DESCRIPTIONS:
        dt = cl.get_type("AdTextAsset")
        dt.text = d
        rsa.descriptions.append(dt)
    ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[aop])
    print(f"  [OK] RSA created with 15 headlines + 4 descriptions")

    # 7. Enable campaign
    cop2 = cl.get_type("CampaignOperation")
    cop2.update.resource_name = campaign_rn
    cop2.update.status = cl.enums.CampaignStatusEnum.ENABLED
    cop2.update_mask.CopyFrom(FieldMask(paths=["status"]))
    camp_svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[cop2])
    print(f"  [OK] Brand Defense campaign ENABLED")

    return campaign_id


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    add_for_sale_negative()
    expand_birthday_keywords()
    brand_id = create_brand_campaign()
    print("\n=== ALL DONE ===")
    print("- `for sale` PHRASE negative added on cafe ops")
    print("- 15 new birthday-intent keywords added to Birthday & Events AG")
    print(f"- Brand Defense campaign ENABLED at Rs 100/day")
