#!/usr/bin/env python3
"""
Fix missing UTM parameters on all active Facebook adsets.
UTM format: utm_source=facebook&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}
"""

import json
import requests
import sys
from datetime import datetime

# Load config
with open("/home/girish/ads/ads-config.json") as f:
    config = json.load(f)

ACCESS_TOKEN = config["facebook"]["access_token"]
AD_ACCOUNT = config["facebook"]["ad_account_id"]
BASE_URL = "https://graph.facebook.com/v21.0"

UTM_TAGS = "utm_source=facebook&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"

def get_active_adsets():
    url = f"{BASE_URL}/{AD_ACCOUNT}/adsets"
    params = {
        "fields": "id,name,status,effective_status,campaign_id,url_tags",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
        "access_token": ACCESS_TOKEN,
        "limit": 100,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()["data"]

def get_campaign_name(campaign_id):
    url = f"{BASE_URL}/{campaign_id}"
    params = {"fields": "name", "access_token": ACCESS_TOKEN}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("name", "unknown")

def is_resort_campaign(campaign_name):
    keywords = ["namooru", "resort", "ecostay"]
    return any(k in campaign_name.lower() for k in keywords)

def update_adset_url_tags(adset_id, url_tags):
    url = f"{BASE_URL}/{adset_id}"
    data = {
        "url_tags": url_tags,
        "access_token": ACCESS_TOKEN,
    }
    resp = requests.post(url, data=data)
    return resp.status_code, resp.json()

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching active adsets...")
    adsets = get_active_adsets()
    print(f"Found {len(adsets)} active adsets\n")

    results = []
    campaign_name_cache = {}

    for adset in adsets:
        adset_id = adset["id"]
        adset_name = adset["name"]
        campaign_id = adset["campaign_id"]
        current_tags = adset.get("url_tags", "")

        # Get campaign name (cached)
        if campaign_id not in campaign_name_cache:
            campaign_name_cache[campaign_id] = get_campaign_name(campaign_id)
        campaign_name = campaign_name_cache[campaign_id]

        resort = is_resort_campaign(campaign_name)
        category = "RESORT (Approval-only but applying UTM)" if resort else "CAFE (Full auto)"

        print(f"Adset: {adset_name}")
        print(f"  ID: {adset_id}")
        print(f"  Campaign: {campaign_name}")
        print(f"  Category: {category}")
        print(f"  Current url_tags: '{current_tags}'")

        if current_tags == UTM_TAGS:
            print(f"  Status: ALREADY CORRECT — skipping\n")
            results.append({
                "adset_id": adset_id,
                "adset_name": adset_name,
                "campaign": campaign_name,
                "action": "skipped_already_correct",
            })
            continue

        # Apply UTM tags
        status_code, response = update_adset_url_tags(adset_id, UTM_TAGS)
        success = response.get("success", False)

        if success:
            print(f"  Status: UPDATED SUCCESSFULLY\n")
            results.append({
                "adset_id": adset_id,
                "adset_name": adset_name,
                "campaign": campaign_name,
                "action": "updated",
            })
        else:
            print(f"  Status: FAILED — HTTP {status_code} — {response}\n")
            results.append({
                "adset_id": adset_id,
                "adset_name": adset_name,
                "campaign": campaign_name,
                "action": "failed",
                "error": str(response),
            })

    # Summary
    updated = [r for r in results if r["action"] == "updated"]
    skipped = [r for r in results if r["action"] == "skipped_already_correct"]
    failed = [r for r in results if r["action"] == "failed"]

    print("=" * 60)
    print(f"SUMMARY")
    print(f"  Total adsets: {len(results)}")
    print(f"  Updated:      {len(updated)}")
    print(f"  Already OK:   {len(skipped)}")
    print(f"  Failed:       {len(failed)}")
    print(f"  UTM format:   {UTM_TAGS}")
    print("=" * 60)

    if failed:
        print("\nFAILED adsets:")
        for r in failed:
            print(f"  - {r['adset_name']} ({r['adset_id']}): {r.get('error')}")

    return results

if __name__ == "__main__":
    results = main()
    sys.exit(0 if not any(r["action"] == "failed" for r in results) else 1)
