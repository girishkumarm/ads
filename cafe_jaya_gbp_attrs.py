#!/usr/bin/env python3
"""Discover and set valid attributes for the Jayanagar cafe (cafe category schema)."""
import os
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
LOC = "locations/1769514473951842535"
V1 = "https://mybusinessbusinessinformation.googleapis.com/v1"

# 1. Get valid attribute schema for this location's categories
print("="*70)
print("Discovering valid attribute names for the location...")
print("="*70)
url = f"{V1}/attributes?categoryName=categories/gcid:cafe&regionCode=IN&languageCode=en&showAll=true"
r, _ = http_request("GET", url, headers=H)
if not r or "attributeMetadata" not in r:
    print(f"[FAIL] {str(r)[:300]}")
    exit(1)

# 2. Get currently set attributes
url2 = f"{V1}/{LOC}/attributes"
r2, _ = http_request("GET", url2, headers=H)
existing = set(a["name"] for a in (r2 or {}).get("attributes", []))

# 3. Find valid ones we haven't set yet
print(f"\nGoogle returned {len(r['attributeMetadata'])} valid attribute schemas.")
print(f"Currently set: {len(existing)}")
print(f"\n--- VALID UNSET ATTRIBUTES (cafe category, India) ---")
candidates = []
for am in r["attributeMetadata"]:
    n = am["parent"]
    if n in existing: continue
    # only single-bool or repeated-enum types
    vtype = am.get("valueType","")
    grp = am.get("groupDisplayName","")
    nm = am.get("displayName","")
    if not nm: continue
    candidates.append({"name": n, "displayName": nm, "valueType": vtype, "group": grp,
                       "valueMetadata": am.get("valueMetadata",[])})
    print(f"  [{vtype:<6}] {n:<55} '{nm}'  (group: {grp})")

print(f"\nFound {len(candidates)} unset valid attributes.")


# 4. Set the relevant ones
print("\n" + "="*70)
print("SETTING RELEVANT NEW ATTRIBUTES")
print("="*70)

# Pick attributes that match our cafe (work/laptop friendly, late night, etc.)
TO_SET_TRUE_DISPLAY = [
    "wifi","wi-fi","outdoor seating","good for groups","good for kids","kid friendly",
    "casual","family-friendly","romantic","good for working","laptop friendly",
    "good for breakfast","good for lunch","good for dinner",
    "fast service","late-night food","quick bite","cozy","trendy","spacious",
    "outdoor","dessert","specialty","seating",
    "credit cards","debit cards","cash only","contactless","mobile payment",
    "free wifi","walk-ins","bookings","catering",
]
to_set = []
for c in candidates:
    if c["valueType"] != "BOOL": continue
    dl = c["displayName"].lower()
    for kw in TO_SET_TRUE_DISPLAY:
        if kw in dl:
            to_set.append(c)
            break

# Dedupe by name
seen = set()
to_set_dedup = []
for c in to_set:
    if c["name"] in seen: continue
    seen.add(c["name"])
    to_set_dedup.append(c)

print(f"\nMatched {len(to_set_dedup)} BOOL attributes to set TRUE:")
attr_payloads = []
for c in to_set_dedup:
    nm_short = c["name"].replace("attributes/","")
    print(f"  + {nm_short:<60} '{c['displayName']}'")
    attr_payloads.append({"name": c["name"], "values": [True]})

if not attr_payloads:
    print("Nothing to set.")
else:
    # Set them all in ONE call using attributeMask
    masks = ",".join(p["name"].replace("attributes/","") for p in attr_payloads)
    body = {"name": f"{LOC}/attributes", "attributes": attr_payloads}
    url = f"{V1}/{LOC}/attributes?attributeMask={masks}"
    r, _ = http_request("PATCH", url, headers=H, data=body)
    if r and "error" not in r:
        print(f"\n[OK] {len(attr_payloads)} attributes set in one batch")
    else:
        print(f"\n[WARN] batch failed, going one-by-one")
        ok = 0
        for p in attr_payloads:
            nm = p["name"].replace("attributes/","")
            body1 = {"name": f"{LOC}/attributes", "attributes": [p]}
            url1 = f"{V1}/{LOC}/attributes?attributeMask={nm}"
            r1, _ = http_request("PATCH", url1, headers=H, data=body1)
            if r1 and "error" not in r1:
                ok += 1
                print(f"  [OK] {nm}")
            else:
                err = (str(r1)[:120]) if r1 else "no response"
                print(f"  [FAIL] {nm}: {err}")
        print(f"\n[OK] {ok}/{len(attr_payloads)} set one-by-one")


# 5. Try to set Wi-Fi enum
print("\n" + "="*70)
print("WI-FI ENUM ATTRIBUTE")
print("="*70)
wifi_attr = next((c for c in candidates if "wifi" in c["displayName"].lower() or "wi-fi" in c["displayName"].lower()), None)
if wifi_attr and wifi_attr["valueType"] != "BOOL":
    print(f"Found wifi attribute: {wifi_attr['name']} type={wifi_attr['valueType']}")
    # values are enum like "free_wi_fi", "paid_wi_fi", "no_wi_fi"
    values_meta = wifi_attr.get("valueMetadata", [])
    print(f"Available enum values:")
    for v in values_meta:
        print(f"  - {v.get('value','')} ({v.get('displayName','')})")
    # Try setting to "free_wi_fi"
    free_v = next((v["value"] for v in values_meta if "free" in v.get("value","").lower()), None)
    if free_v:
        body = {"name": f"{LOC}/attributes",
                "attributes": [{"name": wifi_attr["name"], "repeatedEnumValue": {"setValues": [free_v]}}]}
        url = f"{V1}/{LOC}/attributes?attributeMask={wifi_attr['name'].replace('attributes/','')}"
        r, _ = http_request("PATCH", url, headers=H, data=body)
        if r and "error" not in r:
            print(f"[OK] wifi set to '{free_v}'")
        else:
            print(f"[FAIL] wifi enum: {str(r)[:300]}")
