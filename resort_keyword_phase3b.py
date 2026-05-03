#!/usr/bin/env python3
"""Re-add the 2 keywords that failed Phase 3 (REMOVED status is permanent — must create fresh)."""
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
CAMP_ID = "21740834372"
AG_ID = "167245531185"  # Ad group 1

REMAINING = [
    ("resorts near bangalore",            27_100),
    ("resort near bangalore for couples", 1_000),
]

cfg = load_config()
cl = _get_google_ads_client(cfg)
svc = cl.get_service("AdGroupCriterionService")

# Verify nothing ENABLED with same text+match already exists
q = f"""SELECT ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.negative
        FROM keyword_view
        WHERE campaign.id = {CAMP_ID}
          AND ad_group_criterion.status = 'ENABLED'"""
already = set()
for r in google_gaql(cfg, q):
    c = r["adGroupCriterion"]
    if c.get("negative"):
        continue
    kw = c.get("keyword", {})
    already.add((kw.get("text","").lower(), kw.get("matchType","")))

ops = []
plan = []
for text, mo in REMAINING:
    if (text.lower(), "EXACT") in already:
        print(f"  [skip] '{text}' EXACT already enabled")
        continue
    op = cl.get_type("AdGroupCriterionOperation")
    c = op.create
    c.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{AG_ID}"
    c.status = cl.enums.AdGroupCriterionStatusEnum.ENABLED
    c.keyword.text = text
    c.keyword.match_type = cl.enums.KeywordMatchTypeEnum.EXACT
    ops.append(op)
    plan.append((text, mo))

if not ops:
    print("Nothing to add.")
else:
    print(f"Adding {len(ops)} keywords (fresh, since REMOVED is permanent):")
    for t, mo in plan:
        print(f"  ADD [EXACT] {t:<40} ({mo:,}/mo)")
    ok = 0
    for i, op in enumerate(ops):
        try:
            svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=[op])
            ok += 1
            print(f"  [OK] '{plan[i][0]}'")
        except Exception as e:
            print(f"  [FAIL] '{plan[i][0]}': {str(e)[:300]}")
    print(f"\n[DONE] {ok}/{len(ops)} added")
