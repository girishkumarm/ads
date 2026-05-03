#!/usr/bin/env python3
"""Pre-flight check before applying April optimizations."""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""
from ads_api import load_config, google_gaql
CAMP_ID = "21740834372"
cfg = load_config()

# Bidding strategy
print("=== BIDDING STRATEGY ===")
q = f"""SELECT campaign.bidding_strategy_type, campaign.target_cpa.target_cpa_micros,
               campaign.maximize_conversions.target_cpa_micros, campaign.manual_cpc.enhanced_cpc_enabled
        FROM campaign WHERE campaign.id = {CAMP_ID}"""
for r in google_gaql(cfg, q):
    print(f"  {r['campaign']}")

# Existing ad schedules
print("\n=== EXISTING AD SCHEDULES ===")
q = f"""SELECT campaign_criterion.resource_name,
               campaign_criterion.ad_schedule.day_of_week,
               campaign_criterion.ad_schedule.start_hour,
               campaign_criterion.ad_schedule.end_hour,
               campaign_criterion.bid_modifier
        FROM campaign_criterion
        WHERE campaign.id = {CAMP_ID}
          AND campaign_criterion.type = 'AD_SCHEDULE'"""
sched = list(google_gaql(cfg, q))
print(f"  {len(sched)} schedule entries:")
for r in sched:
    s = r["campaignCriterion"].get("adSchedule", {})
    print(f"    {s.get('dayOfWeek',''):<10} {s.get('startHour',0):>2}-{s.get('endHour',0):<2}h  ×{r['campaignCriterion'].get('bidModifier',1.0):.2f}")

# Existing device mods
print("\n=== EXISTING DEVICE BID MODS ===")
q = f"""SELECT campaign_criterion.device.type, campaign_criterion.bid_modifier
        FROM campaign_criterion
        WHERE campaign.id = {CAMP_ID}
          AND campaign_criterion.type = 'DEVICE'"""
for r in google_gaql(cfg, q):
    d = r["campaignCriterion"].get("device", {})
    print(f"    {d.get('type','')}: ×{r['campaignCriterion'].get('bidModifier',1.0):.2f}")

# Negatives count
print("\n=== EXISTING NEGATIVES ===")
q = f"""SELECT campaign_criterion.keyword.text,
               campaign_criterion.keyword.match_type,
               campaign_criterion.negative
        FROM campaign_criterion
        WHERE campaign.id = {CAMP_ID}
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'"""
negs = list(google_gaql(cfg, q))
print(f"  {len(negs)} negative keywords")
for r in negs[:20]:
    k = r["campaignCriterion"]["keyword"]
    print(f"    [{k['matchType']:<7}] {k['text']}")
if len(negs) > 20:
    print(f"    ... and {len(negs)-20} more")
