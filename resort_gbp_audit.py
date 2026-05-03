#!/usr/bin/env python3
"""Namooru Ecostay Resort GBP — full audit (read-only)."""
import os, json
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, gbp_get_token, http_request

cfg = load_config()
token = gbp_get_token(cfg)
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
LOC = "locations/10815844322260560435"  # Namooru Ecostay
V1 = "https://mybusinessbusinessinformation.googleapis.com/v1"


def section(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


section("RESORT GBP — FULL AUDIT")
url = f"{V1}/{LOC}?readMask=title,phoneNumbers,categories,storefrontAddress,websiteUri,regularHours,specialHours,profile,labels,moreHours,serviceItems,metadata,latlng"
r, _ = http_request("GET", url, headers=H)
if not r:
    print("FAIL"); exit(1)

print(f"  Title       : {r.get('title','')}")
print(f"  Website     : {r.get('websiteUri','—')}")
phs = r.get("phoneNumbers", {})
print(f"  Phone primary  : {phs.get('primaryPhone','—')}")
print(f"  Phone additional: {phs.get('additionalPhones',[])}")
addr = r.get("storefrontAddress", {})
print(f"  Address     : {', '.join(addr.get('addressLines',[]))}, {addr.get('locality','')}, {addr.get('postalCode','')}")

cats = r.get("categories", {})
pri = cats.get("primaryCategory", {})
print(f"  Primary category : {pri.get('displayName','—')} ({pri.get('name','')})")
add_cats = cats.get("additionalCategories", [])
print(f"  Additional categories ({len(add_cats)}):")
for c in add_cats:
    print(f"    - {c.get('displayName','?')} ({c.get('name','')})")

desc = r.get("profile", {}).get("description","")
print(f"  Description ({len(desc)} chars):")
print(f"    {desc[:300]}")

hours = r.get("regularHours", {}).get("periods", [])
print(f"  Regular hours periods: {len(hours)}")
for p in hours[:7]:
    o = p.get("openTime",{}); c = p.get("closeTime",{})
    print(f"    {p.get('openDay','?'):<10} {o.get('hours','?')}:{o.get('minutes',0):02} → {c.get('hours','?')}:{c.get('minutes',0):02}")

sh = r.get("specialHours", {}).get("specialHourPeriods", [])
print(f"  Special hour periods: {len(sh)}")

mh = r.get("moreHours", [])
print(f"  More hours: {len(mh)}")
for h in mh:
    print(f"    - {h.get('hoursTypeId','?')}")

si = r.get("serviceItems", [])
print(f"  Service items: {len(si)}")
for s in si[:15]:
    si_data = s.get("structuredServiceItem") or s.get("freeFormServiceItem", {})
    label = si_data.get("label", {})
    print(f"    - {label.get('displayName','?')}: {label.get('description','')[:80]}")

labels = r.get("labels", [])
print(f"  Labels: {labels}")


# Attributes
print(f"\n=== Attributes ===")
url = f"{V1}/{LOC}/attributes"
r, _ = http_request("GET", url, headers=H)
attrs = (r or {}).get("attributes", [])
print(f"  Total: {len(attrs)}")
for a in attrs:
    nm = a.get("name","").replace("attributes/","")
    bools = a.get("values", [])
    repvals = a.get("repeatedEnumValue", {})
    print(f"    {nm:<55} bool={bools} enum={repvals}")
