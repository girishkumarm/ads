#!/usr/bin/env python3
"""Jayanagar Cafe Google Business Profile audit — full SEO inventory.

Uses existing gbp_* functions in ads_api.py (read-only for now)."""
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
if not token:
    print("[FAIL] no GBP access token")
    exit(1)

H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 1. List accounts
print("="*78)
print("1. GBP ACCOUNTS")
print("="*78)
r, _ = http_request("GET", "https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=H)
if not r or "accounts" not in r:
    print(f"  [FAIL] {r}")
    exit(1)
accounts = r["accounts"]
for a in accounts:
    print(f"  {a.get('name','?')}  type={a.get('type','?')}  role={a.get('role','?')}  primaryOwner={a.get('primaryOwner','?')}")


# 2. For each account, list locations and find the Jayanagar cafe
print(f"\n{'='*78}")
print("2. LOCATIONS — finding Jayanagar Brewing Untold Stories")
print("="*78)
JAYA_LOCATION = None
all_locations = []
for a in accounts:
    acc_name = a["name"]
    print(f"\n  Account: {acc_name}")
    url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc_name}/locations?readMask=name,title,storefrontAddress,categories,phoneNumbers,websiteUri,regularHours,profile,metadata,labels"
    r, _ = http_request("GET", url, headers=H)
    if not r or "locations" not in r:
        # Pagination not exhausted? Just print
        print(f"    no locations or err: {str(r)[:200]}")
        continue
    for loc in r.get("locations", []):
        title = loc.get("title", "")
        addr = loc.get("storefrontAddress", {})
        locality = addr.get("locality","")
        regions = addr.get("administrativeArea","")
        full_addr = (", ".join(addr.get("addressLines",[])) + ", " + locality)[:80]
        print(f"    - {loc.get('name','?'):<40} {title[:35]:<36} {full_addr}")
        all_locations.append({"name": loc["name"], "title": title, "data": loc, "account": acc_name})
        # match Jayanagar location
        if "jayanagar" in title.lower() or ("jayanagar" in locality.lower() and "brewing" in title.lower()):
            JAYA_LOCATION = {"name": loc["name"], "title": title, "data": loc, "account": acc_name}

if not JAYA_LOCATION:
    # Heuristic: pick the one matching coords or 4th block
    for l in all_locations:
        addr = l["data"].get("storefrontAddress", {})
        if "jayanagar" in (addr.get("locality","") + " " + " ".join(addr.get("addressLines",[]))).lower():
            JAYA_LOCATION = l
            break

if not JAYA_LOCATION:
    print(f"\n[FAIL] Could not auto-detect Jayanagar location — listing all so user can pick.")
    exit(1)

print(f"\n[OK] Jayanagar location: {JAYA_LOCATION['name']}  '{JAYA_LOCATION['title']}'  account={JAYA_LOCATION['account']}")


# 3. Detailed view
loc_name = JAYA_LOCATION["name"]
print(f"\n{'='*78}")
print(f"3. CURRENT STATE — {JAYA_LOCATION['title']}")
print(f"{'='*78}")
url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{loc_name}?readMask=title,phoneNumbers,categories,storefrontAddress,websiteUri,regularHours,specialHours,serviceArea,profile,labels,moreHours,serviceItems,metadata,relationshipData,openInfo,latlng"
r, _ = http_request("GET", url, headers=H)
if r:
    title = r.get("title","")
    print(f"  Title       : {title}")
    print(f"  Website     : {r.get('websiteUri','—')}")
    phs = r.get("phoneNumbers", {})
    print(f"  Phone (primary)  : {phs.get('primaryPhone','—')}")
    print(f"  Phone (additional): {phs.get('additionalPhones',[])}")
    cats = r.get("categories", {})
    pri = cats.get("primaryCategory", {})
    print(f"  Primary category : {pri.get('displayName','—')}  ({pri.get('name','')})")
    add_cats = cats.get("additionalCategories", [])
    print(f"  Additional categories ({len(add_cats)}):")
    for c in add_cats:
        print(f"    - {c.get('displayName','?')} ({c.get('name','')})")
    desc = r.get("profile", {}).get("description","")
    print(f"  Description ({len(desc)} chars):")
    print(f"    {desc[:300]}")
    hours = r.get("regularHours", {}).get("periods", [])
    print(f"  Regular hours periods: {len(hours)}")
    if hours[:2]:
        for p in hours[:7]:
            o = p.get("openTime",{}); c = p.get("closeTime",{})
            print(f"    {p.get('openDay','?'):<10} {o.get('hours','?')}:{o.get('minutes','00'):0>2} → {c.get('hours','?')}:{c.get('minutes','00'):0>2}")
    sh = r.get("specialHours", {})
    print(f"  Special hours periods: {len(sh.get('specialHourPeriods', []))}")
    si = r.get("serviceItems", [])
    print(f"  Service items: {len(si)}")
    for s in si[:10]:
        si_type = s.get("structuredServiceItem") or s.get("freeFormServiceItem", {})
        print(f"    - {si_type}")


# 4. Attributes
print(f"\n{'='*78}")
print(f"4. CURRENT ATTRIBUTES")
print(f"{'='*78}")
attr_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{loc_name}/attributes"
r, _ = http_request("GET", attr_url, headers=H)
if r and "attributes" in r:
    for a in r["attributes"]:
        nm = a.get("name","").replace("attributes/","")
        bools = a.get("values", [])
        repvals = a.get("repeatedEnumValue", {})
        print(f"  {nm:<55} values={bools} repeated={repvals}")
else:
    print(f"  None or err: {str(r)[:200]}")


# 5. Reviews
print(f"\n{'='*78}")
print(f"5. RECENT REVIEWS")
print(f"{'='*78}")
url = f"https://mybusiness.googleapis.com/v4/{loc_name}/reviews?pageSize=10"
r, _ = http_request("GET", url, headers=H)
if r and "reviews" in r:
    print(f"  Total: {r.get('totalReviewCount','?')}, Avg rating: {r.get('averageRating','?')}")
    for rev in r["reviews"][:5]:
        rating = rev.get("starRating","?")
        comment = rev.get("comment","")[:120]
        replied = "REPLIED" if rev.get("reviewReply") else "NO REPLY"
        author = rev.get("reviewer",{}).get("displayName","?")
        print(f"  ⭐{rating:<10} [{replied:<8}] {author[:20]:<22} {comment}")
else:
    print(f"  None or err: {str(r)[:200]}")


# 6. Recent posts
print(f"\n{'='*78}")
print(f"6. RECENT LOCAL POSTS")
print(f"{'='*78}")
url = f"https://mybusiness.googleapis.com/v4/{loc_name}/localPosts?pageSize=10"
r, _ = http_request("GET", url, headers=H)
if r and "localPosts" in r:
    for p in r["localPosts"][:10]:
        sm = p.get("summary","")[:60]
        st = p.get("state","?")
        ct = p.get("createTime","")[:10]
        tt = p.get("topicType","?")
        print(f"  {ct} {tt:<10} {st:<8} {sm}")
else:
    print(f"  None or err: {str(r)[:200]}")


# 7. Photos / media
print(f"\n{'='*78}")
print(f"7. MEDIA INVENTORY")
print(f"{'='*78}")
url = f"https://mybusiness.googleapis.com/v4/{loc_name}/media"
r, _ = http_request("GET", url, headers=H)
if r and "mediaItems" in r:
    by_cat = {}
    for m in r["mediaItems"]:
        cat = m.get("locationAssociation",{}).get("category","?")
        by_cat[cat] = by_cat.get(cat, 0) + 1
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:<30} {n}")
    print(f"  TOTAL: {len(r['mediaItems'])}")
else:
    print(f"  None or err: {str(r)[:200]}")


print(f"\n=== AUDIT COMPLETE — Jayanagar location: {JAYA_LOCATION['name']} ===")
print(f"Saving location info to .gbp_jayanagar.json for downstream scripts.")
with open("/Users/girishkumar/Documents/ads/.gbp_jayanagar.json","w") as f:
    json.dump({"location_name": JAYA_LOCATION["name"], "title": JAYA_LOCATION["title"],
               "account": JAYA_LOCATION["account"]}, f, indent=2)
