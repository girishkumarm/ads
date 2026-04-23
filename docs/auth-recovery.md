# Google Auth Recovery Guide

## When this is needed
The ads bot reports any of:
- `Google OAuth failed: {'error': 'invalid_grant', ...}`
- `Request had insufficient authentication scopes` (403)
- Any auth-related failure on `ads_api.py auth google` or `ads_api.py ga4 overview`

## Why it happens
Google OAuth2 refresh tokens become invalid when:
1. **Password change** on `namooruresortsads@gmail.com` — revokes all refresh tokens
2. **6 months of non-use** — Google expires unused refresh tokens
3. **Scope change** — adding a new scope (e.g., `analytics.readonly`) requires a fresh token; the old one still has only the old scopes
4. **Too many tokens** — a Google account is limited to 50 refresh tokens per OAuth client; oldest get revoked
5. **User revoked** access at myaccount.google.com/permissions

The underlying code in `ads_api.py google_get_token()` is correct — it just needs a valid refresh token in `ads-config.json`.

## Recovery procedure

### On the VPS (where the bot runs)

```bash
cd /root/ads
rm -f .ads-token.json   # clear cached access token
# Then edit ads-config.json to paste the new refresh_token (see below)
python3 ads_api.py auth google   # verify it works
python3 ads_api.py google campaigns   # confirm API access
```

### To generate a new refresh token

The bot cannot generate refresh tokens itself (OAuth requires a browser). The user does this from a laptop with a browser:

1. On the laptop, clone/pull the repo and run:
   ```bash
   cd ~/Documents/ads
   python3 oauth_capture.py
   ```
   This starts a local callback server on `http://localhost:8080`.

2. In the **same terminal or separate**, open this URL in a browser (all on one line):
   ```
   https://accounts.google.com/o/oauth2/v2/auth?client_id=406298617381-j58p700q6d2vs2h1fnv2a1hbg1b6fshd.apps.googleusercontent.com&redirect_uri=http://localhost:8080&response_type=code&scope=https://www.googleapis.com/auth/adwords%20https://www.googleapis.com/auth/analytics.readonly&access_type=offline&prompt=consent
   ```

3. Sign in as `namooruresortsads@gmail.com`, click through "Google hasn't verified this app" → Advanced → Continue, then Continue again on the consent screen.

4. Google redirects to `localhost:8080/?code=...`. The `oauth_capture.py` script captures the code, exchanges it for a refresh token, and prints:
   ```
   REFRESH_TOKEN=1//0g...
   ACCESS_TOKEN=ya29...
   ```

5. Copy the `REFRESH_TOKEN=` value.

6. On the VPS, update `ads-config.json`:
   ```json
   {
     "google_ads": {
       ...
       "refresh_token": "PASTE_HERE",
       ...
     }
   }
   ```

7. Delete the cached access token and verify:
   ```bash
   rm -f /root/ads/.ads-token.json
   python3 /root/ads/ads_api.py auth google
   python3 /root/ads/ads_api.py google campaigns
   python3 /root/ads/ads_api.py ga4 overview 7
   ```

## Scopes the token must have

Both are required:
- `https://www.googleapis.com/auth/adwords` — for Google Ads API
- `https://www.googleapis.com/auth/analytics.readonly` — for GA4 Data API

The OAuth URL in step 2 above includes both. If you see "insufficient scopes" errors after updating, the token was likely generated with only the adwords scope — regenerate with the URL above.

## Why `oauth_capture.py` exists
The file in this repo (`oauth_capture.py`) is a minimal one-shot HTTP server:
- Listens on `127.0.0.1:8080` for exactly one GET request
- Parses the `code` query parameter
- Exchanges it for a refresh token via `https://oauth2.googleapis.com/token`
- Prints both tokens to stdout
- Exits after handling one request

It's designed to be run briefly on a laptop (or anywhere with browser access) during token regeneration. It is NOT meant to run on the VPS (no browser there).

## Preventing future breakage
- Don't change the Gmail password on `namooruresortsads@gmail.com` without regenerating the token
- Don't regenerate the OAuth client secret in Google Cloud Console without updating `client_secret` in `ads-config.json`
- The `ads-token-watchdog` scheduled task should check token health daily; if it reports failure, regenerate as above
