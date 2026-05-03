#!/usr/bin/env python3
"""Retry RSA creation with shorter descriptions."""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, _get_google_ads_client

CUSTOMER_ID = "2995160429"
AG_RN = "customers/2995160429/adGroups/196256288356"
TARGET_URL = "https://namooru.com/?utm_source=google&utm_medium=cpc&utm_campaign=resort_group_bookings"

cfg = load_config()
cl = _get_google_ads_client(cfg)
ad_svc = cl.get_service("AdGroupAdService")

HEADLINES = [
    "Wedding Resort Bangalore",         # 24
    "Destination Wedding Venue",        # 25
    "Corporate Offsite Resort",         # 24
    "Team Outing - 60 Km BLR",          # 22
    "Group Bookings 50-300 Pax",        # 25
    "Big Birthday Party Venue",         # 24
    "Reception Hall Bangalore",         # 24
    "35 Acres Forest Resort",           # 22
    "Wedding Mandap & Banquet",         # 24
    "Bulk Booking Discounts",           # 22
    "Private Event Venue",              # 19
    "Kanakapura Resort Bookings",       # 26
    "From Rs 2499 Per Head",            # 21
    "100-300 Guests Capacity",          # 23
    "Custom Group Packages",            # 21
]
# Descriptions: max 90 chars each
DESCRIPTIONS = [
    "35-acre eco resort hosts weddings, offsites & birthdays. From Rs 2,499/head. Book direct.",  # 89
    "Banquet + mandap + cottages for 100-300. 60 km from Bangalore, Kanakapura Road.",            # 79
    "Group bookings 50-300 guests. Custom packages, in-house catering. Reserve today.",          # 80
    "Wedding venue, offsite, big party hall. Direct booking saves more.",                        # 66
]

# Length check
for h in HEADLINES:
    assert len(h) <= 30, f"Headline too long ({len(h)}): {h}"
for d in DESCRIPTIONS:
    assert len(d) <= 90, f"Description too long ({len(d)}): {d}"
print("All within limits.")

op = cl.get_type("AdGroupAdOperation")
ad = op.create
ad.ad_group = AG_RN
ad.status = cl.enums.AdGroupAdStatusEnum.ENABLED
rsa = ad.ad.responsive_search_ad
for h in HEADLINES:
    a = rsa.headlines.add(); a.text = h
for d in DESCRIPTIONS:
    a = rsa.descriptions.add(); a.text = d
ad.ad.final_urls.append(TARGET_URL)
rsa.path1 = "groups"
rsa.path2 = "events"

try:
    r = ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
    print(f"[OK] RSA created: {r.results[0].resource_name}")
except Exception as e:
    print(f"[FAIL] {str(e)[:500]}")
