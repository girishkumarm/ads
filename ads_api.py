#!/usr/bin/env python3
"""
Ads Management API Module
Google Ads + Facebook Marketing API — CLI interface for automated ads optimization.

Usage:
  python3 ads_api.py auth google                         # Test Google OAuth token
  python3 ads_api.py auth facebook                       # Test FB token validity

  # ── Google Ads (Read-Only) ──────────────────────────────────
  python3 ads_api.py google campaigns                    # List all campaigns
  python3 ads_api.py google metrics CAMPAIGN_ID [DAYS]   # Campaign metrics
  python3 ads_api.py google keywords CAMPAIGN_ID         # Keywords with metrics
  python3 ads_api.py google negatives CAMPAIGN_ID        # Negative keywords
  python3 ads_api.py google search-terms CAMPAIGN_ID [DAYS]  # Search terms report
  python3 ads_api.py google ad-groups CAMPAIGN_ID        # Ad groups
  python3 ads_api.py google ads ADGROUP_ID               # Ads in ad group
  python3 ads_api.py google budget                       # Account balance
  python3 ads_api.py google age-targeting CAMPAIGN_ID    # Age demographic targeting
  python3 ads_api.py google recommendations              # Google optimization recs
  python3 ads_api.py google change-history [DAYS]        # Recent account changes
  python3 ads_api.py google impression-share CAMPAIGN_ID [DAYS]  # Impression share metrics
  python3 ads_api.py google device-metrics CAMPAIGN_ID [DAYS]    # Device breakdown
  python3 ads_api.py google hourly-metrics CAMPAIGN_ID [DAYS]    # Hourly breakdown
  python3 ads_api.py google geo-metrics CAMPAIGN_ID [DAYS]       # Geographic breakdown
  python3 ads_api.py google auction-insights CAMPAIGN_ID [DAYS]  # Competitor auction data

  # ── Facebook Ads (Read + Write) ─────────────────────────────
  python3 ads_api.py fb campaigns                        # List all campaigns
  python3 ads_api.py fb adsets CAMPAIGN_ID               # Ad sets in campaign
  python3 ads_api.py fb ads ADSET_ID                     # Ads in ad set
  python3 ads_api.py fb metrics OBJECT_ID [DAYS]         # Insights
  python3 ads_api.py fb adset-metrics ADSET_ID [DAYS]    # Ad set insights
  python3 ads_api.py fb ad-metrics AD_ID [DAYS]          # Individual ad insights
  python3 ads_api.py fb frequency CAMPAIGN_ID            # Frequency + reach
  python3 ads_api.py fb demographics CAMPAIGN_ID         # Age/gender breakdown
  python3 ads_api.py fb placements CAMPAIGN_ID           # Placement breakdown
  python3 ads_api.py fb account-spend [DAYS]             # Total account spend
  python3 ads_api.py fb pixel-events [DAYS]              # Pixel event data
  python3 ads_api.py fb pause AD_ID                      # Pause an ad
  python3 ads_api.py fb resume AD_ID                     # Resume an ad
  python3 ads_api.py fb pause-adset ADSET_ID             # Pause an ad set
  python3 ads_api.py fb resume-adset ADSET_ID            # Resume an ad set
  python3 ads_api.py fb pause-campaign CAMPAIGN_ID       # Pause campaign
  python3 ads_api.py fb resume-campaign CAMPAIGN_ID      # Resume campaign
  python3 ads_api.py fb update-budget CAMPAIGN_ID AMOUNT # Update daily budget
  python3 ads_api.py fb quality-ranking AD_ID [DAYS]     # Ad quality/relevance rankings
  python3 ads_api.py fb video-metrics AD_ID [DAYS]       # Video watch-through rates
  python3 ads_api.py fb ad-review AD_ID                  # Ad review status & feedback
  python3 ads_api.py fb cost-unique CAMPAIGN_ID [DAYS]   # Cost per unique click/impressions

  # ── Cross-Platform ──────────────────────────────────────────
  python3 ads_api.py summary                             # Combined overview
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from datetime import datetime, timedelta

# ── Configuration ─────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "ads-config.json")
TOKEN_CACHE = os.path.join(SCRIPT_DIR, ".ads-token.json")

# SSL context — disable verification only behind Zscaler proxy (local dev)
SSL_CTX = ssl.create_default_context()
if os.environ.get("SKIP_SSL_VERIFY") or os.path.exists(os.path.expanduser("~/Library")):
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE

GOOGLE_ADS_API_VERSION = "v19"
GOOGLE_ADS_BASE = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}"
GOOGLE_OAUTH_URL = "https://oauth2.googleapis.com/token"

FB_API_VERSION = "v22.0"
FB_GRAPH_BASE = f"https://graph.facebook.com/{FB_API_VERSION}"

# ── Helpers ───────────────────────────────────────────────────

def load_config():
    """Load API configuration from ads-config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: {CONFIG_PATH} not found. Create it with your API credentials.", file=sys.stderr)
        print("""Required format:
{
  "google_ads": {
    "developer_token": "YOUR_DEV_TOKEN",
    "client_id": "YOUR_OAUTH_CLIENT_ID",
    "client_secret": "YOUR_OAUTH_CLIENT_SECRET",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "customer_id": "2995160429"
  },
  "facebook": {
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "YOUR_LONG_LIVED_TOKEN",
    "ad_account_id": "act_511239865642774",
    "pixel_id": "789775680451708"
  }
}""", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fmt_money(amount_micros):
    """Convert Google Ads micros (1/1,000,000) to Rs display string."""
    if amount_micros is None:
        return "N/A"
    return f"Rs {int(amount_micros) / 1_000_000:,.2f}"


def fmt_pct(value):
    """Format a decimal ratio as percentage."""
    if value is None:
        return "N/A"
    return f"{float(value) * 100:.2f}%"


def fmt_fb_money(amount_str):
    """Format FB API amount (string in account currency units) to Rs display."""
    if amount_str is None:
        return "N/A"
    return f"Rs {float(amount_str):,.2f}"


def days_ago_str(days):
    """Return date string N days ago in YYYY-MM-DD format."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


# ── HTTP Client ───────────────────────────────────────────────
# Mirrors upstox_api.py: curl_cffi preferred, urllib fallback.

_cffi_session = None

def _get_cffi_session():
    global _cffi_session
    if _cffi_session is None:
        try:
            from curl_cffi import requests as cffi_requests
            skip_ssl = bool(os.environ.get("SKIP_SSL_VERIFY") or os.path.exists(os.path.expanduser("~/Library")))
            _cffi_session = cffi_requests.Session(impersonate="chrome131", verify=not skip_ssl)
        except ImportError:
            _cffi_session = False
    return _cffi_session


def http_request(method, url, data=None, headers=None, _retry_count=0):
    """Generic HTTP request with retry on transient failures."""
    MAX_RETRIES = 3
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    if headers is None:
        headers = {}

    result = None
    status_code = None

    session = _get_cffi_session()
    if session:
        try:
            if method == "GET":
                resp = session.get(url, headers=headers, timeout=30)
            elif method == "POST":
                if isinstance(data, str):
                    resp = session.post(url, data=data, headers=headers, timeout=30)
                else:
                    resp = session.post(url, json=data, headers=headers, timeout=30)
            else:
                resp = session.request(method, url, json=data, headers=headers, timeout=30)
            status_code = resp.status_code
            try:
                result = resp.json()
            except Exception:
                result = {"error": {"message": resp.text[:500]}}
        except Exception as e:
            print(f"Request failed: {e}", file=sys.stderr)
            result = {"error": {"message": str(e)}}
    else:
        headers.setdefault("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        if isinstance(data, dict):
            body = json.dumps(data).encode()
        elif isinstance(data, str):
            body = data.encode()
        else:
            body = data
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
            status_code = resp.status
            result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            status_code = e.code
            error_body = e.read().decode() if e.fp else ""
            print(f"API Error {e.code}: {error_body[:300]}", file=sys.stderr)
            try:
                result = json.loads(error_body)
            except json.JSONDecodeError:
                result = {"error": {"message": error_body[:300], "code": e.code}}
        except Exception as e:
            print(f"Request failed: {e}", file=sys.stderr)
            result = {"error": {"message": str(e)}}

    # Retry on transient failures
    if _retry_count < MAX_RETRIES and status_code and status_code in RETRYABLE_CODES:
        delay = 2 ** _retry_count
        print(f"Retrying {method} {url[:80]}... in {delay}s (attempt {_retry_count + 1}/{MAX_RETRIES}, status={status_code})", file=sys.stderr)
        time.sleep(delay)
        return http_request(method, url, data=data, headers=headers, _retry_count=_retry_count + 1)

    return result, status_code


# ══════════════════════════════════════════════════════════════
#  GOOGLE ADS API
# ══════════════════════════════════════════════════════════════

def google_get_token(config):
    """Get Google OAuth2 access token from refresh token, with caching."""
    gc = config["google_ads"]

    # Check cache
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE) as f:
            cache = json.load(f)
        if cache.get("google_expires_at", 0) > time.time() + 60:
            return cache["google_access_token"]

    # Refresh token exchange
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": gc["client_id"],
        "client_secret": gc["client_secret"],
        "refresh_token": gc["refresh_token"],
    })
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result, status = http_request("POST", GOOGLE_OAUTH_URL, data=body, headers=headers)

    if not result or "access_token" not in result:
        print(f"Google OAuth failed: {result}", file=sys.stderr)
        return None

    token = result["access_token"]
    expires_in = result.get("expires_in", 3600)

    # Cache token
    cache = {}
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE) as f:
            cache = json.load(f)
    cache["google_access_token"] = token
    cache["google_expires_at"] = time.time() + expires_in
    with open(TOKEN_CACHE, "w") as f:
        json.dump(cache, f)
    return token


def google_gaql(config, query):
    """Execute a GAQL query via Google Ads searchStream API."""
    gc = config["google_ads"]
    token = google_get_token(config)
    if not token:
        return None

    customer_id = gc["customer_id"].replace("-", "")
    url = f"{GOOGLE_ADS_BASE}/customers/{customer_id}/googleAds:searchStream"
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": gc["developer_token"],
        "Content-Type": "application/json",
    }
    # Add login-customer-id if present (for MCC accounts)
    if gc.get("login_customer_id"):
        headers["login-customer-id"] = gc["login_customer_id"].replace("-", "")

    data = {"query": query}
    result, status = http_request("POST", url, data=data, headers=headers)

    if status == 401:
        # Token expired — clear cache and retry once
        if os.path.exists(TOKEN_CACHE):
            cache = {}
            try:
                with open(TOKEN_CACHE) as f:
                    cache = json.load(f)
                cache.pop("google_access_token", None)
                cache.pop("google_expires_at", None)
                with open(TOKEN_CACHE, "w") as f:
                    json.dump(cache, f)
            except Exception:
                pass
        token = google_get_token(config)
        if token:
            headers["Authorization"] = f"Bearer {token}"
            result, status = http_request("POST", url, data=data, headers=headers)

    if not result:
        return []

    # searchStream returns array of batches, each with "results"
    rows = []
    if isinstance(result, list):
        for batch in result:
            rows.extend(batch.get("results", []))
    elif isinstance(result, dict):
        if "error" in result:
            print(f"Google Ads API error: {json.dumps(result['error'], indent=2)}", file=sys.stderr)
            return []
        rows.extend(result.get("results", []))
    return rows


def google_campaigns(config):
    """List all non-removed campaigns."""
    query = """
        SELECT campaign.id, campaign.name, campaign.status,
               campaign_budget.amount_micros,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.conversions, metrics.cost_micros
        FROM campaign
        WHERE campaign.status != 'REMOVED'
        ORDER BY campaign.name
    """
    return google_gaql(config, query)


def google_metrics(config, campaign_id, days=7):
    """Get campaign metrics for last N days."""
    query = f"""
        SELECT segments.date,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.conversions, metrics.cost_micros,
               metrics.interactions, metrics.interaction_rate,
               metrics.phone_calls, metrics.all_conversions
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING LAST_{days}_DAYS
        ORDER BY segments.date DESC
    """
    # GAQL only supports specific date range constants
    if days not in [7, 14, 30]:
        start = days_ago_str(days)
        end = today_str()
        query = f"""
            SELECT segments.date,
                   metrics.clicks, metrics.impressions, metrics.ctr,
                   metrics.average_cpc, metrics.conversions, metrics.cost_micros,
                   metrics.interactions, metrics.interaction_rate
            FROM campaign
            WHERE campaign.id = {campaign_id}
              AND segments.date BETWEEN '{start}' AND '{end}'
            ORDER BY segments.date DESC
        """
    return google_gaql(config, query)


def google_keywords(config, campaign_id):
    """List all keywords with metrics for a campaign."""
    query = f"""
        SELECT ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.quality_info.quality_score,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.cost_micros,
               metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {campaign_id}
          AND ad_group_criterion.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
    """
    return google_gaql(config, query)


def google_negatives(config, campaign_id):
    """List campaign-level negative keywords."""
    query = f"""
        SELECT campaign_criterion.keyword.text,
               campaign_criterion.keyword.match_type,
               campaign_criterion.negative
        FROM campaign_criterion
        WHERE campaign.id = {campaign_id}
          AND campaign_criterion.type = 'KEYWORD'
          AND campaign_criterion.negative = TRUE
        ORDER BY campaign_criterion.keyword.text
    """
    return google_gaql(config, query)


def google_search_terms(config, campaign_id, days=7):
    """Search terms report — what people actually searched."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT search_term_view.search_term,
               segments.search_term_match_type,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.cost_micros,
               metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.cost_micros DESC
    """
    return google_gaql(config, query)


def google_ad_groups(config, campaign_id):
    """List ad groups in a campaign."""
    query = f"""
        SELECT ad_group.id, ad_group.name, ad_group.status,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.cost_micros
        FROM ad_group
        WHERE campaign.id = {campaign_id}
          AND ad_group.status != 'REMOVED'
        ORDER BY ad_group.name
    """
    return google_gaql(config, query)


def google_ads(config, adgroup_id):
    """List ads in an ad group."""
    query = f"""
        SELECT ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad.final_urls,
               ad_group_ad.status,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.cost_micros
        FROM ad_group_ad
        WHERE ad_group.id = {adgroup_id}
          AND ad_group_ad.status != 'REMOVED'
    """
    return google_gaql(config, query)


def google_budget(config):
    """Get account budget/balance info."""
    query = """
        SELECT account_budget.status,
               account_budget.approved_spending_limit_micros,
               account_budget.adjusted_spending_limit_micros,
               account_budget.amount_served_micros
        FROM account_budget
        WHERE account_budget.status = 'APPROVED'
    """
    return google_gaql(config, query)


def google_age_targeting(config, campaign_id):
    """Get age demographic targeting for a campaign."""
    query = f"""
        SELECT campaign_criterion.age_range.type,
               campaign_criterion.negative
        FROM campaign_criterion
        WHERE campaign.id = {campaign_id}
          AND campaign_criterion.type = 'AGE_RANGE'
    """
    return google_gaql(config, query)


def google_recommendations(config):
    """Get Google's optimization recommendations."""
    query = """
        SELECT recommendation.type,
               recommendation.impact.base_metrics.impressions,
               recommendation.impact.base_metrics.clicks,
               recommendation.impact.potential_metrics.impressions,
               recommendation.impact.potential_metrics.clicks,
               recommendation.campaign
        FROM recommendation
        ORDER BY recommendation.type
    """
    return google_gaql(config, query)


def google_change_history(config, days=7):
    """Get recent changes to the account."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT change_event.change_date_time,
               change_event.change_resource_type,
               change_event.resource_change_operation,
               change_event.user_email,
               change_event.client_type,
               change_event.old_resource,
               change_event.new_resource
        FROM change_event
        WHERE change_event.change_date_time BETWEEN '{start}' AND '{end}'
        ORDER BY change_event.change_date_time DESC
        LIMIT 50
    """
    return google_gaql(config, query)


# ══════════════════════════════════════════════════════════════
#  FACEBOOK MARKETING API
# ══════════════════════════════════════════════════════════════

def fb_get_token(config):
    """Get Facebook access token, check validity, warn on expiry."""
    fc = config["facebook"]
    token = fc["access_token"]

    # Check cache for token debug info
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE) as f:
            cache = json.load(f)
        expires_at = cache.get("fb_expires_at", 0)
        if expires_at > 0:
            days_left = (expires_at - time.time()) / 86400
            if days_left < 7:
                print(f"WARNING: Facebook token expires in {days_left:.1f} days! Refresh it.", file=sys.stderr)
            if days_left < 0:
                print("ERROR: Facebook token has EXPIRED. Generate a new one.", file=sys.stderr)
                return None
    return token


def fb_debug_token(config):
    """Debug/validate FB token and cache expiry info."""
    fc = config["facebook"]
    token = fc["access_token"]
    url = f"{FB_GRAPH_BASE}/debug_token?input_token={token}&access_token={token}"
    result, status = http_request("GET", url)
    if result and "data" in result:
        data = result["data"]
        expires_at = data.get("expires_at", 0)
        # Cache expiry
        cache = {}
        if os.path.exists(TOKEN_CACHE):
            with open(TOKEN_CACHE) as f:
                cache = json.load(f)
        cache["fb_expires_at"] = expires_at
        with open(TOKEN_CACHE, "w") as f:
            json.dump(cache, f)
        return data
    return result


def fb_api(config, endpoint, params=None, method="GET", data=None):
    """Make a Facebook Graph API request."""
    token = fb_get_token(config)
    if not token:
        return None

    if params is None:
        params = {}
    params["access_token"] = token

    if method == "GET":
        qs = urllib.parse.urlencode(params)
        url = f"{FB_GRAPH_BASE}/{endpoint}?{qs}"
        result, status = http_request("GET", url)
    else:
        url = f"{FB_GRAPH_BASE}/{endpoint}"
        if data:
            data["access_token"] = token
        else:
            data = params
        result, status = http_request("POST", url, data=data)

    if result and "error" in result:
        print(f"Facebook API error: {json.dumps(result['error'], indent=2)}", file=sys.stderr)
    return result


def fb_campaigns(config):
    """List all campaigns with key fields."""
    fc = config["facebook"]
    return fb_api(config, f"{fc['ad_account_id']}/campaigns", {
        "fields": "id,name,status,daily_budget,lifetime_budget,objective,start_time,stop_time,effective_status",
        "limit": 100,
    })


def fb_adsets(config, campaign_id):
    """List ad sets in a campaign."""
    return fb_api(config, f"{campaign_id}/adsets", {
        "fields": "id,name,status,daily_budget,targeting,optimization_goal,billing_event,effective_status",
        "limit": 100,
    })


def fb_ads_list(config, adset_id):
    """List ads in an ad set."""
    return fb_api(config, f"{adset_id}/ads", {
        "fields": "id,name,status,effective_status,creative{id,name,title,body,thumbnail_url}",
        "limit": 100,
    })


def fb_insights(config, object_id, days=7, level=None):
    """Get insights for a campaign/adset/ad."""
    params = {
        "fields": "impressions,reach,frequency,clicks,ctr,cpc,cpm,spend,actions,cost_per_action_type",
        "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30] else "last_7d",
    }
    if level:
        params["level"] = level
    return fb_api(config, f"{object_id}/insights", params)


def fb_frequency(config, campaign_id):
    """Get frequency and reach data for fatigue detection."""
    return fb_api(config, f"{campaign_id}/insights", {
        "fields": "reach,frequency,impressions,clicks,ctr,cpc,spend",
        "date_preset": "last_7d",
    })


def fb_demographics(config, campaign_id):
    """Get age/gender breakdown."""
    return fb_api(config, f"{campaign_id}/insights", {
        "fields": "impressions,clicks,spend,ctr,cpc",
        "breakdowns": "age,gender",
        "date_preset": "last_7d",
    })


def fb_placements(config, campaign_id):
    """Get placement breakdown (feed, stories, reels, etc.)."""
    return fb_api(config, f"{campaign_id}/insights", {
        "fields": "impressions,clicks,spend,ctr,cpc",
        "breakdowns": "publisher_platform,platform_position",
        "date_preset": "last_7d",
    })


def fb_account_spend(config, days=30):
    """Get total account spend."""
    fc = config["facebook"]
    return fb_api(config, f"{fc['ad_account_id']}/insights", {
        "fields": "spend,impressions,clicks,ctr,cpc,actions",
        "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30] else "last_30d",
    })


def fb_pixel_events(config, days=7):
    """Get pixel event data."""
    fc = config["facebook"]
    pixel_id = fc.get("pixel_id")
    if not pixel_id:
        print("No pixel_id configured", file=sys.stderr)
        return None
    return fb_api(config, f"{pixel_id}/stats", {
        "aggregation": "event",
    })


def fb_update_status(config, object_id, status):
    """Update status of a campaign/adset/ad (ACTIVE or PAUSED)."""
    token = fb_get_token(config)
    if not token:
        return None
    url = f"{FB_GRAPH_BASE}/{object_id}"
    data = {"status": status, "access_token": token}
    result, code = http_request("POST", url, data=data)
    return result


def fb_update_budget(config, campaign_id, amount):
    """Update daily budget for a campaign (amount in Rs, converted to paisa)."""
    token = fb_get_token(config)
    if not token:
        return None
    # FB API expects budget in smallest currency unit (paisa = Rs * 100)
    budget_paisa = int(float(amount) * 100)
    url = f"{FB_GRAPH_BASE}/{campaign_id}"
    data = {"daily_budget": budget_paisa, "access_token": token}
    result, code = http_request("POST", url, data=data)
    return result


# ── Google Ads: Impression Share ──────────────────────────────

def google_impression_share(config, campaign_id, days=7):
    """Get impression share metrics for a campaign."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT segments.date,
               metrics.search_impression_share,
               metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share,
               metrics.search_top_impression_share,
               metrics.search_absolute_top_impression_share
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY segments.date DESC
    """
    return google_gaql(config, query)


def google_device_metrics(config, campaign_id, days=7):
    """Get campaign metrics broken down by device."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT segments.device,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.conversions, metrics.cost_micros
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
    """
    return google_gaql(config, query)


def google_hourly_metrics(config, campaign_id, days=7):
    """Get campaign metrics broken down by hour of day."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT segments.hour,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.conversions, metrics.cost_micros
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
    """
    return google_gaql(config, query)


def google_geo_metrics(config, campaign_id, days=7):
    """Get campaign metrics broken down by geographic location."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT geographic_view.country_criterion_id,
               geographic_view.location_type,
               metrics.clicks, metrics.impressions, metrics.ctr,
               metrics.average_cpc, metrics.conversions, metrics.cost_micros
        FROM geographic_view
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
        ORDER BY metrics.clicks DESC
    """
    return google_gaql(config, query)


def google_auction_insights(config, campaign_id, days=30):
    """Get auction insights — competitor overlap and impression share."""
    start = days_ago_str(days)
    end = today_str()
    query = f"""
        SELECT auction_insight.display_domain,
               metrics.auction_insight_search_impression_share,
               metrics.auction_insight_search_overlap_rate,
               metrics.auction_insight_search_outranking_share
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date BETWEEN '{start}' AND '{end}'
    """
    return google_gaql(config, query)


# ── Facebook: Quality & Video Metrics ─────────────────────────

def fb_quality_ranking(config, ad_id, days=7):
    """Get ad quality/relevance rankings."""
    return fb_api(config, f"{ad_id}/insights", {
        "fields": "quality_ranking,engagement_rate_ranking,conversion_rate_ranking,impressions,clicks,spend",
        "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30] else "last_7d",
    })


def fb_video_metrics(config, ad_id, days=7):
    """Get video watch-through metrics."""
    return fb_api(config, f"{ad_id}/insights", {
        "fields": "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions,impressions,spend",
        "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30] else "last_7d",
    })


def fb_ad_review_status(config, ad_id):
    """Get ad review feedback and effective status."""
    return fb_api(config, ad_id, {
        "fields": "effective_status,ad_review_feedback",
    })


def fb_cost_per_unique(config, campaign_id, days=7):
    """Get cost per unique click and unique reach metrics."""
    return fb_api(config, f"{campaign_id}/insights", {
        "fields": "cost_per_unique_click,unique_clicks,unique_impressions,impressions,clicks,spend",
        "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30] else "last_7d",
    })


# ══════════════════════════════════════════════════════════════
#  CROSS-PLATFORM SUMMARY
# ══════════════════════════════════════════════════════════════

def print_summary(config):
    """Print combined overview of both platforms."""
    print("\n  ══════════════════════════════════════════════════")
    print("  ADS MANAGEMENT SUMMARY")
    print("  ══════════════════════════════════════════════════\n")

    # Google Ads
    print("  ── GOOGLE ADS (Namooru Ecostay Resort) ──────────\n")
    campaigns = google_campaigns(config)
    if campaigns:
        for row in campaigns:
            c = row.get("campaign", {})
            m = row.get("metrics", {})
            b = row.get("campaignBudget", {})
            status = c.get("status", "?")
            icon = "ACTIVE" if status == "ENABLED" else status
            print(f"  [{icon}] {c.get('name', '?')} (ID: {c.get('id', '?')})")
            print(f"    Budget: {fmt_money(b.get('amountMicros'))} /day")
            print(f"    Clicks: {m.get('clicks', 0)} | Impr: {m.get('impressions', 0)} | CTR: {fmt_pct(m.get('ctr'))}")
            print(f"    CPC: {fmt_money(m.get('averageCpc'))} | Conv: {m.get('conversions', 0)} | Spend: {fmt_money(m.get('costMicros'))}")
            print()
    else:
        print("  No campaigns found or API error.\n")

    budget = google_budget(config)
    if budget:
        for row in budget:
            ab = row.get("accountBudget", {})
            approved = ab.get("approvedSpendingLimitMicros")
            served = ab.get("amountServedMicros")
            if approved and served:
                remaining = int(approved) - int(served)
                print(f"  Account Budget: {fmt_money(approved)} approved, {fmt_money(served)} spent")
                print(f"  Remaining: {fmt_money(str(remaining))}")
    print()

    # Facebook Ads
    print("  ── FACEBOOK ADS (BUS Cafe) ───────────────────────\n")
    fb_result = fb_campaigns(config)
    if fb_result and "data" in fb_result:
        total_budget = 0
        for c in fb_result["data"]:
            status = c.get("effective_status", c.get("status", "?"))
            budget = c.get("daily_budget", "0")
            budget_rs = float(budget) / 100 if budget else 0
            total_budget += budget_rs
            icon = "ACTIVE" if status == "ACTIVE" else status
            print(f"  [{icon}] {c.get('name', '?')} (ID: {c.get('id', '?')})")
            print(f"    Budget: Rs {budget_rs:,.0f}/day | Objective: {c.get('objective', '?')}")
        print(f"\n  Total FB daily budget: Rs {total_budget:,.0f}")
    else:
        print("  No campaigns found or API error.")

    # Account spend
    spend = fb_account_spend(config, 30)
    if spend and "data" in spend and spend["data"]:
        s = spend["data"][0]
        print(f"  Last 30 days spend: {fmt_fb_money(s.get('spend'))}")
        print(f"  Clicks: {s.get('clicks', 0)} | Impressions: {s.get('impressions', 0)}")
    print()


# ══════════════════════════════════════════════════════════════
#  GOOGLE BUSINESS PROFILE (GBP) — Namooru Ecostay Resort
# ══════════════════════════════════════════════════════════════

GBP_API_BASE = "https://mybusiness.googleapis.com/v4"
GBP_API_V1 = "https://mybusinessbusinessinformation.googleapis.com/v1"

def gbp_get_token(config):
    """Get Google access token (reuses Google Ads OAuth — same account)."""
    return google_get_token(config)

def gbp_get_account(config):
    """Get the GBP account ID."""
    token = gbp_get_token(config)
    if not token:
        return None
    url = f"{GBP_API_BASE}/accounts"
    result, code = http_request("GET", url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    return result

def gbp_get_locations(config):
    """List all business locations."""
    token = gbp_get_token(config)
    if not token:
        return None
    gc = config.get("google_business", config.get("google_ads", {}))
    account_id = gc.get("gbp_account_id", "")
    if not account_id:
        # Try to auto-discover
        accounts = gbp_get_account(config)
        if accounts and "accounts" in accounts:
            account_id = accounts["accounts"][0].get("name", "")
        else:
            return None
    url = f"{GBP_API_V1}/{account_id}/locations"
    result, code = http_request("GET", url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    return result

def gbp_get_reviews(config, location_name=None):
    """Get reviews for a location."""
    token = gbp_get_token(config)
    if not token:
        return None
    gc = config.get("google_business", config.get("google_ads", {}))
    loc = location_name or gc.get("gbp_location_name", "")
    if not loc:
        return {"error": "No GBP location configured. Set google_business.gbp_location_name in ads-config.json"}
    url = f"{GBP_API_BASE}/{loc}/reviews"
    result, code = http_request("GET", url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    return result

def gbp_reply_review(config, review_name, reply_text):
    """Reply to a review."""
    token = gbp_get_token(config)
    if not token:
        return None
    url = f"{GBP_API_BASE}/{review_name}/reply"
    data = {"comment": reply_text}
    result, code = http_request("PUT", url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json_data=data)
    return result

def gbp_get_insights(config, location_name=None, days=7):
    """Get location insights (views, searches, actions)."""
    token = gbp_get_token(config)
    if not token:
        return None
    gc = config.get("google_business", config.get("google_ads", {}))
    loc = location_name or gc.get("gbp_location_name", "")
    if not loc:
        return {"error": "No GBP location configured"}
    # reportInsights endpoint
    url = f"https://businessprofileperformance.googleapis.com/v1/{loc}:getDailyMetricsTimeSeries"
    from datetime import datetime, timedelta
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "dailyMetric": "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
        "dailyRange.startDate.year": start.year,
        "dailyRange.startDate.month": start.month,
        "dailyRange.startDate.day": start.day,
        "dailyRange.endDate.year": end.year,
        "dailyRange.endDate.month": end.month,
        "dailyRange.endDate.day": end.day,
    }
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    result, code = http_request("GET", f"{url}?{param_str}", headers={
        "Authorization": f"Bearer {token}",
    })
    return result

def gbp_create_post(config, text, location_name=None):
    """Create a Google Business post."""
    token = gbp_get_token(config)
    if not token:
        return None
    gc = config.get("google_business", config.get("google_ads", {}))
    loc = location_name or gc.get("gbp_location_name", "")
    if not loc:
        return {"error": "No GBP location configured"}
    url = f"{GBP_API_BASE}/{loc}/localPosts"
    data = {
        "languageCode": "en",
        "summary": text,
        "topicType": "STANDARD"
    }
    result, code = http_request("POST", url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json_data=data)
    return result

def gbp_get_info(config, location_name=None):
    """Get business information."""
    token = gbp_get_token(config)
    if not token:
        return None
    gc = config.get("google_business", config.get("google_ads", {}))
    loc = location_name or gc.get("gbp_location_name", "")
    if not loc:
        return {"error": "No GBP location configured"}
    url = f"{GBP_API_V1}/{loc}?readMask=title,phoneNumbers,categories,storefrontAddress,websiteUri,regularHours,profile"
    result, code = http_request("GET", url, headers={
        "Authorization": f"Bearer {token}",
    })
    return result

def print_gbp_reviews(config):
    """Print reviews in readable format."""
    result = gbp_get_reviews(config)
    if not result:
        print("  Failed to fetch reviews")
        return
    if "error" in result:
        print(f"  Error: {result['error']}")
        return
    reviews = result.get("reviews", [])
    if not reviews:
        print("  No reviews found")
        return
    print(f"\n  {'Rating':<8} {'Author':<25} {'Date':<12} Comment")
    print(f"  {'─'*8} {'─'*25} {'─'*12} {'─'*40}")
    for r in reviews[:20]:
        rating = r.get("starRating", "?")
        author = r.get("reviewer", {}).get("displayName", "Anonymous")[:24]
        date = r.get("createTime", "")[:10]
        comment = r.get("comment", "(no comment)")[:60]
        reply = r.get("reviewReply", {}).get("comment", "")
        replied = "✓" if reply else "✗"
        print(f"  {rating:<8} {author:<25} {date:<12} {comment}")
        print(f"  {'':8} Replied: {replied}  Review ID: {r.get('name', '?')}")


# ══════════════════════════════════════════════════════════════
#  GODADDY — namooru.com Domain & DNS Management
# ══════════════════════════════════════════════════════════════

GODADDY_API_BASE = "https://api.godaddy.com/v1"

def godaddy_headers(config):
    """Get GoDaddy API auth headers."""
    gc = config.get("godaddy", {})
    api_key = gc.get("api_key", "")
    api_secret = gc.get("api_secret", "")
    if not api_key or not api_secret:
        return None
    return {"Authorization": f"sso-key {api_key}:{api_secret}", "Content-Type": "application/json"}

def godaddy_domain_info(config):
    """Get domain registration info."""
    headers = godaddy_headers(config)
    if not headers:
        return {"error": "GoDaddy API credentials not configured in ads-config.json"}
    gc = config.get("godaddy", {})
    domain = gc.get("domain", "namooru.com")
    url = f"{GODADDY_API_BASE}/domains/{domain}"
    result, code = http_request("GET", url, headers=headers)
    return result

def godaddy_dns_records(config, record_type=None):
    """Get DNS records for the domain."""
    headers = godaddy_headers(config)
    if not headers:
        return {"error": "GoDaddy API credentials not configured"}
    gc = config.get("godaddy", {})
    domain = gc.get("domain", "namooru.com")
    url = f"{GODADDY_API_BASE}/domains/{domain}/records"
    if record_type:
        url += f"/{record_type}"
    result, code = http_request("GET", url, headers=headers)
    return result

def godaddy_add_dns_record(config, record_type, name, value, ttl=3600):
    """Add a DNS record."""
    headers = godaddy_headers(config)
    if not headers:
        return {"error": "GoDaddy API credentials not configured"}
    gc = config.get("godaddy", {})
    domain = gc.get("domain", "namooru.com")
    url = f"{GODADDY_API_BASE}/domains/{domain}/records"
    data = [{"type": record_type, "name": name, "data": value, "ttl": ttl}]
    result, code = http_request("PATCH", url, headers=headers, json_data=data)
    return result

def godaddy_ssl_check(config):
    """Check SSL certificate status via direct connection."""
    gc = config.get("godaddy", {})
    domain = gc.get("domain", "namooru.com")
    import socket
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain, 443))
            cert = s.getpeercert()
            from datetime import datetime
            expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_left = (expires - datetime.utcnow()).days
            return {
                "domain": domain,
                "issuer": dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "Unknown"),
                "expires": expires.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "status": "CRITICAL" if days_left < 7 else "WARNING" if days_left < 30 else "OK"
            }
    except Exception as e:
        return {"error": str(e), "domain": domain}

def print_godaddy_domain(config):
    """Print domain info."""
    result = godaddy_domain_info(config)
    if "error" in result:
        print(f"  Error: {result['error']}")
        return
    print(f"\n  Domain: {result.get('domain', '?')}")
    print(f"  Status: {result.get('status', '?')}")
    print(f"  Expires: {result.get('expires', '?')}")
    print(f"  Auto-renew: {result.get('renewAuto', '?')}")
    print(f"  Nameservers: {', '.join(result.get('nameServers', []))}")
    print(f"  Privacy: {result.get('privacy', '?')}")

def print_godaddy_dns(config):
    """Print DNS records."""
    result = godaddy_dns_records(config)
    if isinstance(result, dict) and "error" in result:
        print(f"  Error: {result['error']}")
        return
    if not isinstance(result, list):
        print(f"  Unexpected response: {result}")
        return
    print(f"\n  {'Type':<8} {'Name':<25} {'Value':<50} {'TTL'}")
    print(f"  {'─'*8} {'─'*25} {'─'*50} {'─'*8}")
    for r in result:
        rtype = r.get("type", "?")
        name = r.get("name", "?")[:24]
        data = r.get("data", "?")[:49]
        ttl = r.get("ttl", "?")
        print(f"  {rtype:<8} {name:<25} {data:<50} {ttl}")

def print_ssl_check(config):
    """Print SSL certificate status."""
    result = godaddy_ssl_check(config)
    if "error" in result:
        print(f"  SSL Error for {result.get('domain', '?')}: {result['error']}")
        return
    status_icon = "✅" if result["status"] == "OK" else "⚠️" if result["status"] == "WARNING" else "🚨"
    print(f"\n  {status_icon} SSL Certificate for {result['domain']}")
    print(f"  Issuer: {result['issuer']}")
    print(f"  Expires: {result['expires']} ({result['days_left']} days left)")
    print(f"  Status: {result['status']}")


# ══════════════════════════════════════════════════════════════
#  CLI DISPATCH
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    def get_flag(flag, default=None):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                return args[idx + 1]
        return default

    config = load_config()

    # ── Auth Commands ──────────────────────────────────────────
    if cmd == "auth":
        if not args:
            print("Usage: ads_api.py auth google|facebook"); sys.exit(1)
        platform = args[0].lower()
        if platform == "google":
            token = google_get_token(config)
            if token:
                print(f"  Google Ads token OK: {token[:20]}...")
                print(f"  Customer ID: {config['google_ads']['customer_id']}")
            else:
                print("  Google Ads auth FAILED", file=sys.stderr); sys.exit(1)
        elif platform in ("facebook", "fb"):
            info = fb_debug_token(config)
            if info and info.get("is_valid"):
                expires = info.get("expires_at", 0)
                days_left = (expires - time.time()) / 86400 if expires else 0
                print(f"  Facebook token VALID")
                print(f"  App ID: {info.get('app_id')}")
                print(f"  Expires: {datetime.fromtimestamp(expires).strftime('%Y-%m-%d %H:%M') if expires else 'Never'}")
                print(f"  Days remaining: {days_left:.1f}")
                if days_left < 7:
                    print(f"  WARNING: Token expires in {days_left:.1f} days — refresh now!")
            else:
                print(f"  Facebook token INVALID or expired: {info}", file=sys.stderr); sys.exit(1)
        else:
            print(f"  Unknown platform: {platform}. Use 'google' or 'facebook'."); sys.exit(1)

    # ── Google Ads Commands ────────────────────────────────────
    elif cmd == "google":
        if not args:
            print("Usage: ads_api.py google <subcommand>"); sys.exit(1)
        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "campaigns":
            rows = google_campaigns(config)
            if not rows:
                print("  No campaigns found."); sys.exit(0)
            print(f"\n  {'Status':<10} {'Campaign Name':<40} {'ID':<15} {'Budget/Day':>12} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6}")
            print(f"  {'─'*10} {'─'*40} {'─'*15} {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6}")
            for row in rows:
                c = row.get("campaign", {})
                m = row.get("metrics", {})
                b = row.get("campaignBudget", {})
                status = c.get("status", "?")
                print(f"  {status:<10} {c.get('name', '?'):<40} {c.get('id', '?'):<15} {fmt_money(b.get('amountMicros')):>12} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {m.get('conversions', 0):>6}")

        elif subcmd == "metrics":
            if not subargs:
                print("Usage: ads_api.py google metrics CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_metrics(config, cid, days)
            if not rows:
                print(f"  No metrics for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Date':<12} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6} {'Spend':>12}")
            print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            total_clicks, total_impr, total_conv, total_spend = 0, 0, 0, 0
            for row in rows:
                s = row.get("segments", {})
                m = row.get("metrics", {})
                clicks = int(m.get("clicks", 0))
                impr = int(m.get("impressions", 0))
                conv = float(m.get("conversions", 0))
                spend = int(m.get("costMicros", 0))
                total_clicks += clicks; total_impr += impr; total_conv += conv; total_spend += spend
                print(f"  {s.get('date', '?'):<12} {clicks:>8} {impr:>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {conv:>6.0f} {fmt_money(str(spend)):>12}")
            print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            avg_ctr = total_clicks / total_impr if total_impr else 0
            avg_cpc = total_spend / total_clicks / 1_000_000 if total_clicks else 0
            print(f"  {'TOTAL':<12} {total_clicks:>8} {total_impr:>8} {avg_ctr*100:>7.2f}% {f'Rs {avg_cpc:,.2f}':>10} {total_conv:>6.0f} {fmt_money(str(total_spend)):>12}")

        elif subcmd == "keywords":
            if not subargs:
                print("Usage: ads_api.py google keywords CAMPAIGN_ID"); sys.exit(1)
            rows = google_keywords(config, subargs[0])
            if not rows:
                print(f"  No keywords found."); sys.exit(0)
            print(f"\n  {'Keyword':<40} {'Match':<12} {'Status':<10} {'QS':>4} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10}")
            print(f"  {'─'*40} {'─'*12} {'─'*10} {'─'*4} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")
            for row in rows:
                kw = row.get("adGroupCriterion", {})
                keyword = kw.get("keyword", {})
                qi = kw.get("qualityInfo", {})
                m = row.get("metrics", {})
                print(f"  {keyword.get('text', '?'):<40} {keyword.get('matchType', '?'):<12} {kw.get('status', '?'):<10} {qi.get('qualityScore', '-'):>4} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10}")

        elif subcmd == "negatives":
            if not subargs:
                print("Usage: ads_api.py google negatives CAMPAIGN_ID"); sys.exit(1)
            rows = google_negatives(config, subargs[0])
            if not rows:
                print("  No negative keywords found."); sys.exit(0)
            print(f"\n  {'Keyword':<50} {'Match Type':<15}")
            print(f"  {'─'*50} {'─'*15}")
            for row in rows:
                cc = row.get("campaignCriterion", {})
                kw = cc.get("keyword", {})
                print(f"  {kw.get('text', '?'):<50} {kw.get('matchType', '?'):<15}")
            print(f"\n  Total: {len(rows)} negative keywords")

        elif subcmd == "search-terms":
            if not subargs:
                print("Usage: ads_api.py google search-terms CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_search_terms(config, cid, days)
            if not rows:
                print("  No search terms data."); sys.exit(0)
            print(f"\n  {'Search Term':<50} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6} {'Spend':>12}")
            print(f"  {'─'*50} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            for row in rows:
                st = row.get("searchTermView", {})
                m = row.get("metrics", {})
                print(f"  {st.get('searchTerm', '?'):<50} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {m.get('conversions', 0):>6} {fmt_money(m.get('costMicros')):>12}")

        elif subcmd == "ad-groups":
            if not subargs:
                print("Usage: ads_api.py google ad-groups CAMPAIGN_ID"); sys.exit(1)
            rows = google_ad_groups(config, subargs[0])
            if not rows:
                print("  No ad groups found."); sys.exit(0)
            print(f"\n  {'ID':<15} {'Name':<40} {'Status':<10} {'Clicks':>8} {'Impr':>8}")
            for row in rows:
                ag = row.get("adGroup", {})
                m = row.get("metrics", {})
                print(f"  {ag.get('id', '?'):<15} {ag.get('name', '?'):<40} {ag.get('status', '?'):<10} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8}")

        elif subcmd == "ads":
            if not subargs:
                print("Usage: ads_api.py google ads ADGROUP_ID"); sys.exit(1)
            rows = google_ads(config, subargs[0])
            if not rows:
                print("  No ads found."); sys.exit(0)
            for row in rows:
                ad = row.get("adGroupAd", {}).get("ad", {})
                m = row.get("metrics", {})
                print(f"\n  Ad ID: {ad.get('id', '?')} | Status: {row.get('adGroupAd', {}).get('status', '?')}")
                urls = ad.get("finalUrls", [])
                if urls:
                    print(f"  URL: {urls[0]}")
                rsa = ad.get("responsiveSearchAd", {})
                if rsa:
                    headlines = [h.get("text", "") for h in rsa.get("headlines", [])]
                    print(f"  Headlines: {' | '.join(headlines[:5])}")
                print(f"  Clicks: {m.get('clicks', 0)} | Impr: {m.get('impressions', 0)} | CTR: {fmt_pct(m.get('ctr'))} | CPC: {fmt_money(m.get('averageCpc'))}")

        elif subcmd == "budget":
            rows = google_budget(config)
            if not rows:
                print("  No budget data found."); sys.exit(0)
            for row in rows:
                ab = row.get("accountBudget", {})
                print(f"\n  Status: {ab.get('status', '?')}")
                print(f"  Approved limit: {fmt_money(ab.get('approvedSpendingLimitMicros'))}")
                print(f"  Adjusted limit: {fmt_money(ab.get('adjustedSpendingLimitMicros'))}")
                print(f"  Amount served:  {fmt_money(ab.get('amountServedMicros'))}")
                approved = ab.get("approvedSpendingLimitMicros")
                served = ab.get("amountServedMicros")
                if approved and served:
                    remaining = int(approved) - int(served)
                    print(f"  Remaining:      {fmt_money(str(remaining))}")

        elif subcmd == "age-targeting":
            if not subargs:
                print("Usage: ads_api.py google age-targeting CAMPAIGN_ID"); sys.exit(1)
            rows = google_age_targeting(config, subargs[0])
            if not rows:
                print("  No age targeting data."); sys.exit(0)
            print(f"\n  {'Age Range':<25} {'Excluded?':<10}")
            for row in rows:
                cc = row.get("campaignCriterion", {})
                age = cc.get("ageRange", {})
                excluded = "YES" if cc.get("negative") else "no"
                print(f"  {age.get('type', '?'):<25} {excluded:<10}")

        elif subcmd == "recommendations":
            rows = google_recommendations(config)
            if not rows:
                print("  No recommendations available."); sys.exit(0)
            print(f"\n  {'Type':<35} {'Campaign':<30} {'Impact (Impr +)':<15}")
            for row in rows:
                rec = row.get("recommendation", {})
                impact = rec.get("impact", {})
                base = impact.get("baseMetrics", {})
                pot = impact.get("potentialMetrics", {})
                impr_lift = int(pot.get("impressions", 0)) - int(base.get("impressions", 0)) if pot and base else 0
                print(f"  {rec.get('type', '?'):<35} {rec.get('campaign', '?'):<30} {'+' + str(impr_lift) if impr_lift else 'N/A':>15}")

        elif subcmd == "change-history":
            days = int(subargs[0]) if subargs else 7
            rows = google_change_history(config, days)
            if not rows:
                print(f"  No changes in last {days} days."); sys.exit(0)
            print(f"\n  {'Date':<22} {'Resource':<20} {'Operation':<15} {'By':<30}")
            for row in rows:
                ce = row.get("changeEvent", {})
                print(f"  {ce.get('changeDateTime', '?'):<22} {ce.get('changeResourceType', '?'):<20} {ce.get('resourceChangeOperation', '?'):<15} {ce.get('userEmail', ce.get('clientType', '?')):<30}")

        elif subcmd == "impression-share":
            if not subargs:
                print("Usage: ads_api.py google impression-share CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_impression_share(config, cid, days)
            if not rows:
                print(f"  No impression share data for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Date':<12} {'Search IS':>10} {'Budget Lost':>12} {'Rank Lost':>12} {'Top IS':>10} {'Abs Top IS':>12}")
            print(f"  {'─'*12} {'─'*10} {'─'*12} {'─'*12} {'─'*10} {'─'*12}")
            for row in rows:
                s = row.get("segments", {})
                m = row.get("metrics", {})
                print(f"  {s.get('date', '?'):<12} {fmt_pct(m.get('searchImpressionShare')):>10} {fmt_pct(m.get('searchBudgetLostImpressionShare')):>12} {fmt_pct(m.get('searchRankLostImpressionShare')):>12} {fmt_pct(m.get('searchTopImpressionShare')):>10} {fmt_pct(m.get('searchAbsoluteTopImpressionShare')):>12}")

        elif subcmd == "device-metrics":
            if not subargs:
                print("Usage: ads_api.py google device-metrics CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_device_metrics(config, cid, days)
            if not rows:
                print(f"  No device metrics for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Device':<15} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6} {'Spend':>12}")
            print(f"  {'─'*15} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            for row in rows:
                s = row.get("segments", {})
                m = row.get("metrics", {})
                print(f"  {s.get('device', '?'):<15} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {m.get('conversions', 0):>6} {fmt_money(m.get('costMicros')):>12}")

        elif subcmd == "hourly-metrics":
            if not subargs:
                print("Usage: ads_api.py google hourly-metrics CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_hourly_metrics(config, cid, days)
            if not rows:
                print(f"  No hourly metrics for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Hour':<6} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6} {'Spend':>12}")
            print(f"  {'─'*6} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            for row in rows:
                s = row.get("segments", {})
                m = row.get("metrics", {})
                hour = s.get("hour", "?")
                print(f"  {hour:<6} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {m.get('conversions', 0):>6} {fmt_money(m.get('costMicros')):>12}")

        elif subcmd == "geo-metrics":
            if not subargs:
                print("Usage: ads_api.py google geo-metrics CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            rows = google_geo_metrics(config, cid, days)
            if not rows:
                print(f"  No geo metrics for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Location ID':<15} {'Type':<20} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'CPC':>10} {'Conv':>6} {'Spend':>12}")
            print(f"  {'─'*15} {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6} {'─'*12}")
            for row in rows:
                gv = row.get("geographicView", {})
                m = row.get("metrics", {})
                print(f"  {gv.get('countryCriterionId', '?'):<15} {gv.get('locationType', '?'):<20} {m.get('clicks', 0):>8} {m.get('impressions', 0):>8} {fmt_pct(m.get('ctr')):>8} {fmt_money(m.get('averageCpc')):>10} {m.get('conversions', 0):>6} {fmt_money(m.get('costMicros')):>12}")

        elif subcmd == "auction-insights":
            if not subargs:
                print("Usage: ads_api.py google auction-insights CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 30
            rows = google_auction_insights(config, cid, days)
            if not rows:
                print(f"  No auction insights for campaign {cid}."); sys.exit(0)
            print(f"\n  {'Domain':<35} {'Impr Share':>12} {'Overlap Rate':>14} {'Outranking':>12}")
            print(f"  {'─'*35} {'─'*12} {'─'*14} {'─'*12}")
            for row in rows:
                ai = row.get("auctionInsight", {})
                m = row.get("metrics", {})
                print(f"  {ai.get('displayDomain', '?'):<35} {fmt_pct(m.get('auctionInsightSearchImpressionShare')):>12} {fmt_pct(m.get('auctionInsightSearchOverlapRate')):>14} {fmt_pct(m.get('auctionInsightSearchOutrankingShare')):>12}")

        else:
            print(f"Unknown Google subcommand: {subcmd}")
            print("Available: campaigns, metrics, keywords, negatives, search-terms, ad-groups, ads, budget, age-targeting, recommendations, change-history, impression-share, device-metrics, hourly-metrics, geo-metrics, auction-insights")
            sys.exit(1)

    # ── Facebook Ads Commands ──────────────────────────────────
    elif cmd == "fb":
        if not args:
            print("Usage: ads_api.py fb <subcommand>"); sys.exit(1)
        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "campaigns":
            result = fb_campaigns(config)
            if not result or "data" not in result:
                print("  No campaigns found or API error."); sys.exit(1)
            print(f"\n  {'Status':<10} {'Campaign Name':<45} {'ID':<20} {'Budget/Day':>12} {'Objective':<20}")
            print(f"  {'─'*10} {'─'*45} {'─'*20} {'─'*12} {'─'*20}")
            for c in result["data"]:
                status = c.get("effective_status", c.get("status", "?"))
                budget = float(c.get("daily_budget", 0)) / 100
                print(f"  {status:<10} {c.get('name', '?'):<45} {c.get('id', '?'):<20} {f'Rs {budget:,.0f}':>12} {c.get('objective', '?'):<20}")

        elif subcmd == "adsets":
            if not subargs:
                print("Usage: ads_api.py fb adsets CAMPAIGN_ID"); sys.exit(1)
            result = fb_adsets(config, subargs[0])
            if not result or "data" not in result:
                print("  No ad sets found."); sys.exit(1)
            print(f"\n  {'Status':<10} {'Ad Set Name':<45} {'ID':<20} {'Budget/Day':>12}")
            for a in result["data"]:
                budget = float(a.get("daily_budget", 0)) / 100 if a.get("daily_budget") else 0
                print(f"  {a.get('effective_status', '?'):<10} {a.get('name', '?'):<45} {a.get('id', '?'):<20} {f'Rs {budget:,.0f}':>12}")

        elif subcmd == "ads":
            if not subargs:
                print("Usage: ads_api.py fb ads ADSET_ID"); sys.exit(1)
            result = fb_ads_list(config, subargs[0])
            if not result or "data" not in result:
                print("  No ads found."); sys.exit(1)
            for ad in result["data"]:
                print(f"\n  [{ad.get('effective_status', '?')}] {ad.get('name', '?')}")
                print(f"    ID: {ad.get('id', '?')}")
                creative = ad.get("creative", {})
                if creative.get("title"):
                    print(f"    Title: {creative['title']}")
                if creative.get("body"):
                    print(f"    Body: {creative['body'][:80]}...")

        elif subcmd in ("metrics", "adset-metrics", "ad-metrics"):
            if not subargs:
                print(f"Usage: ads_api.py fb {subcmd} OBJECT_ID [DAYS]"); sys.exit(1)
            oid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            result = fb_insights(config, oid, days)
            if not result or "data" not in result or not result["data"]:
                print(f"  No metrics for {oid}."); sys.exit(0)
            for row in result["data"]:
                print(f"\n  ── Metrics (last {days} days) ──")
                print(f"  Impressions: {row.get('impressions', 'N/A')}")
                print(f"  Reach:       {row.get('reach', 'N/A')}")
                print(f"  Frequency:   {row.get('frequency', 'N/A')}")
                print(f"  Clicks:      {row.get('clicks', 'N/A')}")
                print(f"  CTR:         {row.get('ctr', 'N/A')}%")
                print(f"  CPC:         {fmt_fb_money(row.get('cpc'))}")
                print(f"  CPM:         {fmt_fb_money(row.get('cpm'))}")
                print(f"  Spend:       {fmt_fb_money(row.get('spend'))}")
                actions = row.get("actions", [])
                if actions:
                    print(f"  Actions:")
                    for a in actions:
                        print(f"    {a.get('action_type', '?')}: {a.get('value', 0)}")

        elif subcmd == "frequency":
            if not subargs:
                print("Usage: ads_api.py fb frequency CAMPAIGN_ID"); sys.exit(1)
            result = fb_frequency(config, subargs[0])
            if result and "data" in result and result["data"]:
                row = result["data"][0]
                freq = float(row.get("frequency", 0))
                fatigue = "ROTATE NOW" if freq > 3.0 else "WARNING" if freq > 2.5 else "OK"
                print(f"\n  Frequency: {freq:.2f} [{fatigue}]")
                print(f"  Reach:     {row.get('reach', 'N/A')}")
                print(f"  Clicks:    {row.get('clicks', 'N/A')}")
                print(f"  CTR:       {row.get('ctr', 'N/A')}%")
                print(f"  Spend:     {fmt_fb_money(row.get('spend'))}")
            else:
                print("  No frequency data.")

        elif subcmd == "demographics":
            if not subargs:
                print("Usage: ads_api.py fb demographics CAMPAIGN_ID"); sys.exit(1)
            result = fb_demographics(config, subargs[0])
            if result and "data" in result:
                print(f"\n  {'Age':<10} {'Gender':<10} {'Impr':>10} {'Clicks':>8} {'CTR':>8} {'Spend':>12}")
                print(f"  {'─'*10} {'─'*10} {'─'*10} {'─'*8} {'─'*8} {'─'*12}")
                for row in result["data"]:
                    print(f"  {row.get('age', '?'):<10} {row.get('gender', '?'):<10} {row.get('impressions', 0):>10} {row.get('clicks', 0):>8} {row.get('ctr', 'N/A'):>8} {fmt_fb_money(row.get('spend')):>12}")
            else:
                print("  No demographics data.")

        elif subcmd == "placements":
            if not subargs:
                print("Usage: ads_api.py fb placements CAMPAIGN_ID"); sys.exit(1)
            result = fb_placements(config, subargs[0])
            if result and "data" in result:
                print(f"\n  {'Platform':<15} {'Position':<25} {'Impr':>10} {'Clicks':>8} {'CTR':>8} {'Spend':>12}")
                print(f"  {'─'*15} {'─'*25} {'─'*10} {'─'*8} {'─'*8} {'─'*12}")
                for row in result["data"]:
                    print(f"  {row.get('publisher_platform', '?'):<15} {row.get('platform_position', '?'):<25} {row.get('impressions', 0):>10} {row.get('clicks', 0):>8} {row.get('ctr', 'N/A'):>8} {fmt_fb_money(row.get('spend')):>12}")
            else:
                print("  No placement data.")

        elif subcmd == "account-spend":
            days = int(subargs[0]) if subargs else 30
            result = fb_account_spend(config, days)
            if result and "data" in result and result["data"]:
                row = result["data"][0]
                print(f"\n  ── Account Spend (last {days} days) ──")
                print(f"  Total spend:  {fmt_fb_money(row.get('spend'))}")
                print(f"  Impressions:  {row.get('impressions', 'N/A')}")
                print(f"  Clicks:       {row.get('clicks', 'N/A')}")
                print(f"  CTR:          {row.get('ctr', 'N/A')}%")
                print(f"  CPC:          {fmt_fb_money(row.get('cpc'))}")
            else:
                print("  No spend data.")

        elif subcmd == "pixel-events":
            days = int(subargs[0]) if subargs else 7
            result = fb_pixel_events(config, days)
            if result and "data" in result:
                print(f"\n  ── Pixel Events ──")
                for row in result["data"]:
                    print(f"  {row.get('event', '?')}: {row.get('count', 0)}")
            else:
                print("  No pixel data (pixel may not be active).")

        elif subcmd == "pause":
            if not subargs:
                print("Usage: ads_api.py fb pause AD_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "PAUSED")
            if result and result.get("success"):
                print(f"  Paused ad {subargs[0]}")
            else:
                print(f"  Failed to pause: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "resume":
            if not subargs:
                print("Usage: ads_api.py fb resume AD_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "ACTIVE")
            if result and result.get("success"):
                print(f"  Resumed ad {subargs[0]}")
            else:
                print(f"  Failed to resume: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "pause-adset":
            if not subargs:
                print("Usage: ads_api.py fb pause-adset ADSET_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "PAUSED")
            if result and result.get("success"):
                print(f"  Paused ad set {subargs[0]}")
            else:
                print(f"  Failed: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "resume-adset":
            if not subargs:
                print("Usage: ads_api.py fb resume-adset ADSET_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "ACTIVE")
            if result and result.get("success"):
                print(f"  Resumed ad set {subargs[0]}")
            else:
                print(f"  Failed: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "pause-campaign":
            if not subargs:
                print("Usage: ads_api.py fb pause-campaign CAMPAIGN_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "PAUSED")
            if result and result.get("success"):
                print(f"  Paused campaign {subargs[0]}")
            else:
                print(f"  Failed: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "resume-campaign":
            if not subargs:
                print("Usage: ads_api.py fb resume-campaign CAMPAIGN_ID"); sys.exit(1)
            result = fb_update_status(config, subargs[0], "ACTIVE")
            if result and result.get("success"):
                print(f"  Resumed campaign {subargs[0]}")
            else:
                print(f"  Failed: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "update-budget":
            if len(subargs) < 2:
                print("Usage: ads_api.py fb update-budget CAMPAIGN_ID AMOUNT_RS"); sys.exit(1)
            result = fb_update_budget(config, subargs[0], subargs[1])
            if result and result.get("success"):
                print(f"  Updated budget for {subargs[0]} to Rs {subargs[1]}/day")
            else:
                print(f"  Failed: {result}", file=sys.stderr); sys.exit(1)

        elif subcmd == "quality-ranking":
            if not subargs:
                print("Usage: ads_api.py fb quality-ranking AD_ID [DAYS]"); sys.exit(1)
            ad_id = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            result = fb_quality_ranking(config, ad_id, days)
            if result and "data" in result and result["data"]:
                for row in result["data"]:
                    print(f"\n  ── Quality Rankings (last {days} days) ──")
                    print(f"  Quality Ranking:         {row.get('quality_ranking', 'N/A')}")
                    print(f"  Engagement Rate Ranking: {row.get('engagement_rate_ranking', 'N/A')}")
                    print(f"  Conversion Rate Ranking: {row.get('conversion_rate_ranking', 'N/A')}")
                    print(f"  Impressions:             {row.get('impressions', 'N/A')}")
                    print(f"  Clicks:                  {row.get('clicks', 'N/A')}")
                    print(f"  Spend:                   {fmt_fb_money(row.get('spend'))}")
            else:
                print("  No quality ranking data.")

        elif subcmd == "video-metrics":
            if not subargs:
                print("Usage: ads_api.py fb video-metrics AD_ID [DAYS]"); sys.exit(1)
            ad_id = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            result = fb_video_metrics(config, ad_id, days)
            if result and "data" in result and result["data"]:
                for row in result["data"]:
                    print(f"\n  ── Video Metrics (last {days} days) ──")
                    for pct in ["video_p25_watched_actions", "video_p50_watched_actions", "video_p75_watched_actions", "video_p100_watched_actions"]:
                        actions = row.get(pct, [])
                        val = actions[0].get("value", "0") if actions else "0"
                        label = pct.replace("video_", "").replace("_watched_actions", "").upper()
                        print(f"  {label} watched: {val}")
                    print(f"  Impressions: {row.get('impressions', 'N/A')}")
                    print(f"  Spend:       {fmt_fb_money(row.get('spend'))}")
            else:
                print("  No video metrics data.")

        elif subcmd == "ad-review":
            if not subargs:
                print("Usage: ads_api.py fb ad-review AD_ID"); sys.exit(1)
            result = fb_ad_review_status(config, subargs[0])
            if result:
                print(f"\n  ── Ad Review Status ──")
                print(f"  Effective Status:    {result.get('effective_status', 'N/A')}")
                feedback = result.get("ad_review_feedback", {})
                if feedback:
                    global_info = feedback.get("global", {})
                    print(f"  Review Feedback:     {json.dumps(global_info, indent=4) if global_info else 'None'}")
                else:
                    print(f"  Review Feedback:     No issues")
            else:
                print("  Failed to get ad review status.")

        elif subcmd == "cost-unique":
            if not subargs:
                print("Usage: ads_api.py fb cost-unique CAMPAIGN_ID [DAYS]"); sys.exit(1)
            cid = subargs[0]
            days = int(subargs[1]) if len(subargs) > 1 else 7
            result = fb_cost_per_unique(config, cid, days)
            if result and "data" in result and result["data"]:
                for row in result["data"]:
                    print(f"\n  ── Cost Per Unique (last {days} days) ──")
                    print(f"  Cost/Unique Click:  {fmt_fb_money(row.get('cost_per_unique_click'))}")
                    print(f"  Unique Clicks:      {row.get('unique_clicks', 'N/A')}")
                    print(f"  Unique Impressions: {row.get('unique_impressions', 'N/A')}")
                    print(f"  Total Clicks:       {row.get('clicks', 'N/A')}")
                    print(f"  Total Impressions:  {row.get('impressions', 'N/A')}")
                    print(f"  Spend:              {fmt_fb_money(row.get('spend'))}")
            else:
                print("  No cost-per-unique data.")

        else:
            print(f"Unknown FB subcommand: {subcmd}")
            print("Available: campaigns, adsets, ads, metrics, adset-metrics, ad-metrics, frequency, demographics, placements, account-spend, pixel-events, pause, resume, pause-adset, resume-adset, pause-campaign, resume-campaign, update-budget, quality-ranking, video-metrics, ad-review, cost-unique")
            sys.exit(1)

    # ── Google Business Profile ────────────────────────────────
    elif cmd == "gbp":
        if not args:
            print("Usage: ads_api.py gbp <subcommand>")
            print("Available: reviews, reply, insights, posts, create-post, info, account, locations")
            sys.exit(1)
        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "account":
            result = gbp_get_account(config)
            print(json.dumps(result, indent=2) if result else "  Failed to get GBP account")

        elif subcmd == "locations":
            result = gbp_get_locations(config)
            print(json.dumps(result, indent=2) if result else "  Failed to get locations")

        elif subcmd == "reviews":
            print_gbp_reviews(config)

        elif subcmd == "reply":
            if len(subargs) < 2:
                print("Usage: ads_api.py gbp reply REVIEW_NAME \"reply text\""); sys.exit(1)
            result = gbp_reply_review(config, subargs[0], " ".join(subargs[1:]))
            print(json.dumps(result, indent=2) if result else "  Failed to reply")

        elif subcmd == "insights":
            days = int(subargs[0]) if subargs else 7
            result = gbp_get_insights(config, days=days)
            print(json.dumps(result, indent=2) if result else "  Failed to get insights")

        elif subcmd in ("create-post", "post"):
            if not subargs:
                print("Usage: ads_api.py gbp create-post \"Post text\""); sys.exit(1)
            result = gbp_create_post(config, " ".join(subargs))
            print(json.dumps(result, indent=2) if result else "  Failed to create post")

        elif subcmd == "info":
            result = gbp_get_info(config)
            print(json.dumps(result, indent=2) if result else "  Failed to get business info")

        else:
            print(f"Unknown GBP subcommand: {subcmd}")
            print("Available: account, locations, reviews, reply, insights, create-post, info")
            sys.exit(1)

    # ── GoDaddy ────────────────────────────────────────────────
    elif cmd == "godaddy":
        if not args:
            print("Usage: ads_api.py godaddy <subcommand>")
            print("Available: domain, dns, dns-add, ssl")
            sys.exit(1)
        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "domain":
            print_godaddy_domain(config)

        elif subcmd == "dns":
            record_type = subargs[0].upper() if subargs else None
            print_godaddy_dns(config)

        elif subcmd == "dns-add":
            if len(subargs) < 3:
                print("Usage: ads_api.py godaddy dns-add TYPE NAME VALUE [TTL]"); sys.exit(1)
            ttl = int(subargs[3]) if len(subargs) > 3 else 3600
            result = godaddy_add_dns_record(config, subargs[0].upper(), subargs[1], subargs[2], ttl)
            print(f"  Added {subargs[0]} record: {subargs[1]} → {subargs[2]}" if result else "  Failed")

        elif subcmd == "ssl":
            print_ssl_check(config)

        else:
            print(f"Unknown GoDaddy subcommand: {subcmd}")
            print("Available: domain, dns, dns-add, ssl")
            sys.exit(1)

    # ── Cross-Platform ─────────────────────────────────────────
    elif cmd == "summary":
        print_summary(config)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
