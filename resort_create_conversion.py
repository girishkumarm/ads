#!/usr/bin/env python3
"""Create Google Ads conversion action 'Wedding/Event Form Submit' for resort.

Type: WEBPAGE
Default value: Rs 500 (group inquiry value)
Count: ONE_PER_CLICK (each form fill = 1 conversion)
Category: SUBMIT_LEAD_FORM
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

CUSTOMER_ID = "2995160429"
cfg = load_config()
cl = _get_google_ads_client(cfg)


# Pull customer-level conversion tracking ID first (needed for gtag)
print("=== Pulling Google Ads Conversion Tracking ID ===")
q = "SELECT customer.id, customer.conversion_tracking_setting.google_ads_conversion_customer FROM customer"
for r in google_gaql(cfg, q):
    cust = r["customer"]
    cts = cust.get("conversionTrackingSetting", {})
    conv_cust = cts.get("googleAdsConversionCustomer", "")
    print(f"  Customer ID: {cust['id']}")
    print(f"  Conversion tracking customer: {conv_cust}")
    CONV_CUSTOMER = conv_cust.split("/")[-1] if conv_cust else cust['id']

print(f"\n=== Creating conversion action 'Wedding/Event Inquiry' ===")
svc = cl.get_service("ConversionActionService")
op = cl.get_type("ConversionActionOperation")
ca = op.create
ca.name = "Wedding/Event Form Submit"
ca.type_ = cl.enums.ConversionActionTypeEnum.WEBPAGE
ca.category = cl.enums.ConversionActionCategoryEnum.SUBMIT_LEAD_FORM
ca.status = cl.enums.ConversionActionStatusEnum.ENABLED
ca.value_settings.default_value = 500.0
ca.value_settings.default_currency_code = "INR"
ca.value_settings.always_use_default_value = False
ca.counting_type = cl.enums.ConversionActionCountingTypeEnum.ONE_PER_CLICK
ca.click_through_lookback_window_days = 30
ca.view_through_lookback_window_days = 1
ca.attribution_model_settings.attribution_model = cl.enums.AttributionModelEnum.GOOGLE_ADS_LAST_CLICK

try:
    r = svc.mutate_conversion_actions(customer_id=CUSTOMER_ID, operations=[op])
    rn = r.results[0].resource_name
    cid = rn.split("/")[-1]
    print(f"  [OK] created: {rn}")
    print(f"  Conversion action ID: {cid}")

    # Pull the gtag tag snippet
    q2 = f"""SELECT conversion_action.id, conversion_action.name,
                    conversion_action.tag_snippets
             FROM conversion_action WHERE conversion_action.id = {cid}"""
    for r2 in google_gaql(cfg, q2):
        ca = r2["conversionAction"]
        snippets = ca.get("tagSnippets", [])
        print(f"\n=== Tag snippets ===")
        for s in snippets:
            print(f"\n  type={s.get('type','?')} page_format={s.get('pageFormat','?')}")
            print(f"  GLOBAL SITE TAG:\n{s.get('globalSiteTag','')[:500]}")
            print(f"\n  EVENT SNIPPET:\n{s.get('eventSnippet','')}")

    # Save the conversion action ID for the landing page
    import json
    with open("/Users/girishkumar/Documents/ads/.wedding_conv.json","w") as f:
        json.dump({"id": cid, "resource_name": rn,
                   "customer_id": CUSTOMER_ID, "conv_customer": CONV_CUSTOMER}, f, indent=2)
    print(f"\n[OK] saved to .wedding_conv.json")

except Exception as e:
    print(f"[FAIL] {str(e)[:600]}")
