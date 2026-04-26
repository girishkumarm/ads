#!/usr/bin/env python3
"""
Create a Google Ads Search campaign to SELL BUS Cafe Jayanagar (business acquisition).

Goal: phone calls from real buyers (entrepreneurs / F&B operators looking to
      acquire a running cafe).

Target: +919738769973 (same as Facebook cafe-sale ads).
Budget: Rs 400/day.

Campaign design:
  - Channel: SEARCH (intent-driven, pre-qualified buyers)
  - Networks: Google Search only (no partners, no display)
  - Bid strategy: MAXIMIZE_CONVERSIONS for first 30 call conversions, then
    upgrade to tCPA Rs 200/call
  - Geo: Bangalore metro (PRESENCE only — no tourists)
  - Schedule: 10am-8pm IST daily (calls need human pickup)
  - Languages: English, Hindi, Kannada

Ad groups:
  AG1 "Cafe For Sale — Direct" (Max CPC Rs 30)
  AG2 "Restaurant / F&B Business For Sale" (Max CPC Rs 25)

Conversion action: existing "Calls from ads" (id 6672734760, AD_CALL).

Usage:
    python3 create_cafe_sale_campaign.py dryrun
    python3 create_cafe_sale_campaign.py create
    python3 create_cafe_sale_campaign.py verify
"""
import os
# SSL bypass for mac
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

CUSTOMER_ID        = "2995160429"
SALE_PHONE         = "+919738769973"
SALE_COUNTRY_CODE  = "IN"
# GBP Maps page for Jayanagar cafe — if a buyer clicks through instead of tapping
# call, they land on the cafe's public listing (photos, 400+ reviews, hours, phone).
FINAL_URL = (
    "https://www.google.com/maps/place/Brewing+Untold+Stories/"
    "@12.9199786,77.587245,905m/data=!3m2!1e3!4b1!4m6!3m5!"
    "1s0x3bae15fec810a3b3:0xf75b25b8f4c76726!"
    "8m2!3d12.9199786!4d77.5898199!16s%2Fg%2F11w9n2nqks!5m1!1e1"
)
BUDGET_MICROS      = 400 * 1_000_000         # Rs 400/day
CAMPAIGN_NAME      = "Jayanagar Cafe For Sale - Calls | 2026-04-24"
CONV_ACTION_ID     = "6672734760"            # existing "Calls from ads" (AD_CALL)

# Geo target constants (Google's location IDs)
# Bangalore metro 1007755 covers a wide radius. Add Hyderabad, Chennai, Mumbai, Delhi for
# mobile investors/operators as well.
GEO_TARGETS = {
    "Bengaluru":   "1007755",   # Bangalore city
    # Broader India expansion — uncomment if no leads in 7 days:
    # "Hyderabad":   "1007772",
    # "Chennai":     "1007762",
    # "Mumbai":      "1007785",
    # "Delhi":       "1007765",
}

LANGUAGE_CONSTANTS = {
    "English": "1000",
    "Hindi":   "1023",
    "Kannada": "1086",
}

AD_GROUPS = [
    {
        "name": "Cafe For Sale - Direct",
        "max_cpc_micros": 30 * 1_000_000,
        "keywords": [
            ("cafe for sale bangalore",          "PHRASE"),
            ("cafe for sale jayanagar",          "PHRASE"),
            ("cafe for sale",                    "PHRASE"),
            ("running cafe for sale",            "PHRASE"),
            ("cafe for sale near me",            "PHRASE"),
            ("buy cafe bangalore",               "PHRASE"),
            ("cafe business for sale bangalore", "PHRASE"),
            ("cafe takeover bangalore",          "PHRASE"),
            ("cafe for sale south bangalore",    "PHRASE"),
            ("coffee shop for sale bangalore",   "PHRASE"),
            ("running coffee shop for sale",     "PHRASE"),
        ],
        "headlines": [
            "Running Cafe For Sale",                # pinned H1
            "Jayanagar 4th Block",
            "Profitable Cafe Business",
            "Established Brand Handover",
            "Loyal Regulars Included",
            "Prime Jayanagar Location",
            "Ask For Full Financials",
            "4.4 Stars, 400+ Reviews",
            "Move In Ready",
            "Fully Operational Sale",
            "Beautifully Fitted Cafe",
            "Long Lease, Low Rent",
            "Owner Selling Direct",
            "Cafe Sale In Jayanagar",
            "Serious Buyers Welcome",
        ],
        "descriptions": [
            "Profitable 4.4 star cafe in Jayanagar 4th Block. Owner relocating. Ask for details.",
            "Full handover: equipment, interiors, POS, staff, brand. Call for site visit.",
            "Serious buyers only. P&L shared on request. No brokers please.",
            "Prime Jayanagar spot, 400+ reviews. Owner selling direct.",
        ],
    },
    {
        "name": "Restaurant / F&B Business For Sale",
        "max_cpc_micros": 25 * 1_000_000,
        "keywords": [
            ("restaurant for sale bangalore",     "PHRASE"),
            ("food business for sale bangalore",  "PHRASE"),
            ("running restaurant for sale",       "PHRASE"),
            ("running business for sale bangalore", "PHRASE"),
            ("profitable business for sale bangalore", "PHRASE"),
            ("small business for sale bangalore", "PHRASE"),
            ("f and b business for sale",         "PHRASE"),
            ("buy running restaurant bangalore",  "PHRASE"),
            ("restaurant business acquisition",   "PHRASE"),
            ("business for sale jayanagar",       "PHRASE"),
        ],
        "headlines": [
            "Running F&B Business For Sale",        # pinned H1
            "Jayanagar Bangalore",
            "Profitable Turnkey Handover",
            "400+ Google Reviews",
            "Selling Due To Relocation",
            "Established Loyal Regulars",
            "Prime Location 4th Block",
            "Ask For Financials",
            "Cafe Format F&B Business",
            "Fully Fitted Premises",
            "Long Lease, Low Rent",
            "Serious Buyers Welcome",
            "Ready To Take Over",
            "Business For Sale Bangalore",
            "Owner Selling Direct",
        ],
        "descriptions": [
            "Running cafe-format F&B business in Jayanagar 4th Block. Profitable, established.",
            "Full handover: brand, interiors, staff, POS, vendors. Call to view financials.",
            "Owner relocating. Prime spot, low rent. Call direct to discuss.",
            "Serious buyers only, no brokers. Call for P&L and site visit.",
        ],
    },
]


# ───────────────────────────────────────────────────────────
# DRY RUN
# ───────────────────────────────────────────────────────────

def dryrun():
    print("=== DRY RUN — Cafe Sale Campaign Plan ===\n")
    print(f"Campaign:  {CAMPAIGN_NAME}")
    print(f"Budget:    Rs {BUDGET_MICROS // 1_000_000}/day")
    print(f"Phone:     {SALE_PHONE}")
    print(f"Geo:       {list(GEO_TARGETS.keys())}")
    print(f"Languages: {list(LANGUAGE_CONSTANTS.keys())}")
    print(f"Schedule:  10:00-20:00 IST every day")
    print(f"Bid:       MAXIMIZE_CONVERSIONS (→ tCPA after 30 calls)")
    print(f"Networks:  Google Search only (no partners, no display)")
    print(f"Conversion: existing 'Calls from ads' (ID {CONV_ACTION_ID})")
    print()
    for ag in AD_GROUPS:
        print(f"─ Ad Group: {ag['name']}  (Max CPC Rs {ag['max_cpc_micros']//1_000_000})")
        print(f"    {len(ag['keywords'])} keywords, {len(ag['headlines'])} headlines, "
              f"{len(ag['long_headlines'])} long headlines, {len(ag['descriptions'])} descriptions")
        for k, mt in ag["keywords"][:4]:
            print(f"       {mt:<7}  {k}")
        print(f"       ... and {len(ag['keywords'])-4} more")


# ───────────────────────────────────────────────────────────
# CREATE
# ───────────────────────────────────────────────────────────

def _temp(idx):
    """Return a negative resource id for same-request dependency chaining."""
    return str(-abs(int(idx)))


def create():
    config = load_config()
    client = _get_google_ads_client(config)

    from google.protobuf.field_mask_pb2 import FieldMask

    # 1. Budget
    bud_svc = client.get_service("CampaignBudgetService")
    bud_op = client.get_type("CampaignBudgetOperation")
    b = bud_op.create
    b.name = f"Budget - {CAMPAIGN_NAME}"
    b.amount_micros = BUDGET_MICROS
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    bud_resp = bud_svc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[bud_op])
    budget_rn = bud_resp.results[0].resource_name
    print(f"[OK] Budget created: {budget_rn}")

    # 2. Campaign
    camp_svc = client.get_service("CampaignService")
    camp_op = client.get_type("CampaignOperation")
    c = camp_op.create
    c.name = CAMPAIGN_NAME
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.status = client.enums.CampaignStatusEnum.PAUSED  # create paused, enable after ads ready
    c.campaign_budget = budget_rn
    # Maximize Conversions (no tCPA yet)
    c.maximize_conversions.target_cpa_micros = 0
    # Networks
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    c.network_settings.target_content_network = False
    c.network_settings.target_partner_search_network = False
    # Geo type: presence only
    c.geo_target_type_setting.positive_geo_target_type = client.enums.PositiveGeoTargetTypeEnum.PRESENCE
    c.geo_target_type_setting.negative_geo_target_type = client.enums.NegativeGeoTargetTypeEnum.PRESENCE
    # Google requires this flag on all new campaigns (post-DSA EU political ads rule)
    c.contains_eu_political_advertising = client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    camp_resp = camp_svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[camp_op])
    campaign_rn = camp_resp.results[0].resource_name
    campaign_id = campaign_rn.split("/")[-1]
    print(f"[OK] Campaign created: {campaign_rn}  (id={campaign_id})  [status=PAUSED]")

    # 3. Campaign criteria: geo, language, ad schedule, call asset
    crit_svc = client.get_service("CampaignCriterionService")
    ops = []

    # Geo targets
    for name, gid in GEO_TARGETS.items():
        op = client.get_type("CampaignCriterionOperation")
        cc = op.create
        cc.campaign = campaign_rn
        cc.location.geo_target_constant = f"geoTargetConstants/{gid}"
        ops.append(op)
    # Languages
    for name, lid in LANGUAGE_CONSTANTS.items():
        op = client.get_type("CampaignCriterionOperation")
        cc = op.create
        cc.campaign = campaign_rn
        cc.language.language_constant = f"languageConstants/{lid}"
        ops.append(op)
    # Ad schedule 10-20h every day
    DayEnum = client.enums.DayOfWeekEnum
    MinEnum = client.enums.MinuteOfHourEnum
    for d in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]:
        op = client.get_type("CampaignCriterionOperation")
        cc = op.create
        cc.campaign = campaign_rn
        cc.ad_schedule.day_of_week = getattr(DayEnum, d)
        cc.ad_schedule.start_hour = 10
        cc.ad_schedule.end_hour = 20
        cc.ad_schedule.start_minute = MinEnum.ZERO
        cc.ad_schedule.end_minute = MinEnum.ZERO
        ops.append(op)
    crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"[OK] Campaign criteria added: {len(GEO_TARGETS)} geo, "
          f"{len(LANGUAGE_CONSTANTS)} languages, 7-day ad schedule (10:00-20:00)")

    # 4. Call asset at campaign level
    asset_svc = client.get_service("AssetService")
    asset_op = client.get_type("AssetOperation")
    a = asset_op.create
    a.call_asset.country_code = SALE_COUNTRY_CODE
    a.call_asset.phone_number = SALE_PHONE.replace("+91", "")  # "9738769973"
    a.call_asset.call_conversion_reporting_state = client.enums.CallConversionReportingStateEnum.USE_RESOURCE_LEVEL_CALL_CONVERSION_ACTION
    a.call_asset.call_conversion_action = f"customers/{CUSTOMER_ID}/conversionActions/{CONV_ACTION_ID}"
    resp_a = asset_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[asset_op])
    call_asset_rn = resp_a.results[0].resource_name
    print(f"[OK] Call asset created: {call_asset_rn}")

    ca_svc = client.get_service("CampaignAssetService")
    ca_op = client.get_type("CampaignAssetOperation")
    ca = ca_op.create
    ca.campaign = campaign_rn
    ca.asset = call_asset_rn
    ca.field_type = client.enums.AssetFieldTypeEnum.CALL
    ca_svc.mutate_campaign_assets(customer_id=CUSTOMER_ID, operations=[ca_op])
    print(f"[OK] Call asset linked to campaign")

    # 5. Ad groups + keywords + RSAs
    ag_svc   = client.get_service("AdGroupService")
    agc_svc  = client.get_service("AdGroupCriterionService")
    ad_svc   = client.get_service("AdGroupAdService")
    MatchEnum = client.enums.KeywordMatchTypeEnum
    ServedAssetEnum = client.enums.ServedAssetFieldTypeEnum

    for agdef in AD_GROUPS:
        # 5a. Ad group
        agop = client.get_type("AdGroupOperation")
        ag = agop.create
        ag.name = agdef["name"]
        ag.campaign = campaign_rn
        ag.status = client.enums.AdGroupStatusEnum.ENABLED
        ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ag.cpc_bid_micros = agdef["max_cpc_micros"]
        agresp = ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[agop])
        ag_rn = agresp.results[0].resource_name
        print(f"[OK] Ad group created: {agdef['name']} → {ag_rn}")

        # 5b. Keywords
        kops = []
        for text, mt in agdef["keywords"]:
            k = client.get_type("AdGroupCriterionOperation")
            c2 = k.create
            c2.ad_group = ag_rn
            c2.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            c2.keyword.text = text
            c2.keyword.match_type = getattr(MatchEnum, mt)
            kops.append(k)
        agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=kops)
        print(f"    [OK] {len(kops)} keywords added")

        # 5c. RSA with pinned H1 + H2
        adop = client.get_type("AdGroupAdOperation")
        newad = adop.create
        newad.ad_group = ag_rn
        newad.status = client.enums.AdGroupAdStatusEnum.ENABLED
        newad.ad.final_urls.append(FINAL_URL)
        rsa = newad.ad.responsive_search_ad

        for i, h in enumerate(agdef["headlines"]):
            ht = client.get_type("AdTextAsset")
            ht.text = h
            # Pin H1 = first headline, H2 = second (call number)
            if i == 0:
                ht.pinned_field = ServedAssetEnum.HEADLINE_1
            elif i == 1:
                ht.pinned_field = ServedAssetEnum.HEADLINE_2
            rsa.headlines.append(ht)

        for lh in agdef["long_headlines"]:
            # long_headlines aren't a thing in standard RSA — descriptions take this role.
            # Keeping them in our data model in case we expand to PMax/Demand Gen later.
            pass

        for d in agdef["descriptions"]:
            dt = client.get_type("AdTextAsset")
            dt.text = d
            rsa.descriptions.append(dt)

        ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[adop])
        print(f"    [OK] RSA created with {len(rsa.headlines)} headlines, {len(rsa.descriptions)} descs")

    print(f"\n=== Campaign created PAUSED. Enable via:")
    print(f"  python3 create_cafe_sale_campaign.py enable {campaign_id}")
    return campaign_id


def enable(campaign_id):
    config = load_config()
    client = _get_google_ads_client(config)
    from google.protobuf.field_mask_pb2 import FieldMask
    svc = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    op.update.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{campaign_id}"
    op.update.status = client.enums.CampaignStatusEnum.ENABLED
    op.update_mask.CopyFrom(FieldMask(paths=["status"]))
    svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
    print(f"[OK] Campaign {campaign_id} ENABLED — ads will start serving shortly")


def verify(campaign_id=None):
    config = load_config()
    if not campaign_id:
        q = f"""SELECT campaign.id, campaign.name FROM campaign
                WHERE campaign.name = '{CAMPAIGN_NAME}'"""
        rows = google_gaql(config, q)
        if not rows:
            print(f"No campaign named '{CAMPAIGN_NAME}' found")
            return
        campaign_id = rows[0]["campaign"]["id"]

    print(f"\n=== Campaign {campaign_id} ===")
    q = f"""SELECT campaign.id, campaign.name, campaign.status,
                   campaign.campaign_budget,
                   campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}"""
    for r in google_gaql(config, q):
        c = r["campaign"]
        b = r.get("campaignBudget", {})
        print(f"  {c['id']}  {c['status']}  Rs {int(b.get('amountMicros',0))//1_000_000}/day  {c['name']}")

    q2 = f"""SELECT ad_group.id, ad_group.name, ad_group.status,
                    ad_group.cpc_bid_micros
             FROM ad_group
             WHERE campaign.id = {campaign_id}"""
    print(f"\n=== Ad groups ===")
    for r in google_gaql(config, q2):
        ag = r["adGroup"]
        print(f"  {ag['id']}  {ag['status']}  Rs {int(ag.get('cpcBidMicros',0))//1_000_000} maxCPC  {ag['name']}")

    q3 = f"""SELECT ad_group.id, ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type
             FROM ad_group_criterion
             WHERE campaign.id = {campaign_id}
               AND ad_group_criterion.type = 'KEYWORD'"""
    rows = google_gaql(config, q3)
    print(f"\n=== Keywords ({len(rows)} total) ===")
    for r in rows[:10]:
        k = r["adGroupCriterion"]["keyword"]
        print(f"  [{k.get('matchType','')}] {k['text']}")
    if len(rows) > 10:
        print(f"  ... and {len(rows)-10} more")

    q4 = f"""SELECT campaign.id, asset.type,
                    asset.call_asset.phone_number,
                    asset.call_asset.country_code
             FROM campaign_asset
             WHERE campaign.id = {campaign_id}"""
    print(f"\n=== Campaign assets ===")
    for r in google_gaql(config, q4):
        a = r["asset"]
        if a.get("type") == "CALL":
            ca = a["callAsset"]
            print(f"  CALL  +{ca.get('countryCode','')} {ca.get('phoneNumber','')}")
        else:
            print(f"  {a.get('type')}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_cafe_sale_campaign.py [dryrun|create|verify|enable CAMPAIGN_ID]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "dryrun":
        dryrun()
    elif cmd == "create":
        create()
    elif cmd == "enable":
        if len(sys.argv) < 3:
            print("Need campaign_id: python3 create_cafe_sale_campaign.py enable CAMPAIGN_ID")
            sys.exit(1)
        enable(sys.argv[2])
    elif cmd == "verify":
        verify(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
