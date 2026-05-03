#!/usr/bin/env python3
"""Pull Keyword Planner volumes for current Group Bookings AG keywords + new candidates.
Drops anything <100/mo India avg."""
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
cfg = load_config()
cl = _get_google_ads_client(cfg)


# Currently in Group Bookings AG (25 keywords)
EXISTING_25 = [
    "wedding resort bangalore",
    "destination wedding bangalore",
    "wedding venue near bangalore",
    "wedding venue bangalore",
    "corporate offsite resort bangalore",
    "corporate offsite venue bangalore",
    "team outing resort bangalore",
    "team outing places near bangalore",
    "birthday party resort bangalore",
    "group booking resort bangalore",
    "reception venue bangalore",
    "event venue near bangalore",
    "wedding resort kanakapura",
    "corporate offsite kanakapura",
    "marriage venue near bangalore",
    "private party venue bangalore",
    "birthday banquet hall bangalore",
    "destination wedding kanakapura",
    "company offsite bangalore",
    "corporate retreat resort",
    "group resort booking bangalore",
    "large group resort bangalore",
    "50 people resort booking",
    "100 people resort booking",
    "party venue near bangalore",
]

# New candidates — corporate + group booking focused
NEW_CANDIDATES = [
    "team outing bangalore",
    "team outing places bangalore",
    "team outing near bangalore",
    "corporate outing bangalore",
    "corporate offsite bangalore",
    "company outing bangalore",
    "team building activities bangalore",
    "team building bangalore",
    "office team outing bangalore",
    "team retreat bangalore",
    "corporate event venue bangalore",
    "corporate venue bangalore",
    "company offsite venue bangalore",
    "team offsite bangalore",
    "team offsite venue",
    "company retreat bangalore",
    "corporate day outing bangalore",
    "corporate team outing",
    "group outing bangalore",
    "group booking near bangalore",
    "group accommodation bangalore",
    "wedding venue kanakapura",
    "marriage hall bangalore",
    "marriage hall near bangalore",
    "banquet hall bangalore",
    "function hall bangalore",
    "function hall near bangalore",
    "engagement venue bangalore",
    "haldi venue bangalore",
    "mehendi venue bangalore",
    "sangeet venue bangalore",
    "pre wedding shoot venue bangalore",
    "outdoor wedding venue bangalore",
    "wedding lawn bangalore",
    "destination wedding venues",
    "destination wedding near bangalore",
    "resort for wedding bangalore",
    "wedding resort near bangalore",
]

ALL_KW = list(set(EXISTING_25 + NEW_CANDIDATES))

svc = cl.get_service("KeywordPlanIdeaService")
req = cl.get_type("GenerateKeywordHistoricalMetricsRequest")
req.customer_id = CUSTOMER_ID
req.language = "languageConstants/1000"
req.geo_target_constants.append("geoTargetConstants/2356")
req.include_adult_keywords = False
req.keyword_plan_network = cl.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
req.keywords.extend(ALL_KW)

print(f"Pulling Keyword Planner volumes for {len(ALL_KW)} keywords...")
resp = svc.generate_keyword_historical_metrics(request=req)

vol = {}
for r in resp.results:
    m = r.keyword_metrics
    vol[r.text.lower()] = {
        "monthly": getattr(m, "avg_monthly_searches", 0) or 0,
        "comp": str(m.competition).split(".")[-1] if m.competition else "—",
        "low": (getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1e6,
        "high": (getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1e6,
    }

print(f"\n{'='*90}")
print("CURRENT 25 KEYWORDS — verdict")
print(f"{'='*90}")
keep, drop = [], []
for kw in EXISTING_25:
    v = vol.get(kw.lower(), {})
    mo = v.get("monthly", 0)
    cpc = f"{v.get('low',0):.0f}-{v.get('high',0):.0f}" if v else "—"
    verdict = "✅ KEEP" if mo >= 100 else ("🟡 weak" if mo >= 30 else "🔴 DROP")
    if mo >= 100: keep.append(kw)
    else: drop.append((kw, mo))
    print(f"  {kw[:42]:<42} {mo:>7,}/mo {v.get('comp','—'):<6} ₹{cpc:<10} {verdict}")

print(f"\n  KEEP: {len(keep)}    DROP/weak: {len(drop)}")
print(f"\n--- TO DROP ---")
for kw, mo in drop:
    print(f"  {kw}  ({mo}/mo)")

print(f"\n{'='*90}")
print("NEW CANDIDATES — sorted by volume desc")
print(f"{'='*90}")
ranked = []
for kw in NEW_CANDIDATES:
    v = vol.get(kw.lower(), {})
    ranked.append((kw, v.get("monthly", 0), v.get("comp","—"),
                   f"{v.get('low',0):.0f}-{v.get('high',0):.0f}"))
ranked.sort(key=lambda x: -x[1])
add = []
for kw, mo, comp, cpc in ranked:
    take = "🟢 ADD" if mo >= 200 else ("🟡 maybe" if mo >= 80 else "🔴 skip")
    if mo >= 200: add.append(kw)
    print(f"  {kw[:42]:<42} {mo:>7,}/mo {comp:<6} ₹{cpc:<10} {take}")

print(f"\n  Recommended to ADD: {len(add)} new keywords")
for kw in add:
    print(f"    + {kw}")
