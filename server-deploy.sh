#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Ads Management System — VPS Setup Script
# Run this on the Hetzner VPS after git pull
# Usage: bash /root/ads/server-deploy.sh
# ═══════════════════════════════════════════════════════════

set -e
cd /root/ads

echo "═══════════════════════════════════════════"
echo "  Ads Management System — VPS Setup"
echo "═══════════════════════════════════════════"

# ── 1. Verify prerequisites ──────────────────────────────
echo ""
echo "[1/6] Checking prerequisites..."

# Check Python
python3 --version || { echo "ERROR: Python3 not found"; exit 1; }

# Check required packages
python3 -c "import requests" 2>/dev/null || pip3 install requests
python3 -c "import curl_cffi" 2>/dev/null || pip3 install curl_cffi
python3 -c "import pyotp" 2>/dev/null || pip3 install pyotp

# Check config files
if [ ! -f "ads-config.json" ]; then
    echo "ERROR: ads-config.json not found!"
    echo "Copy it from your local machine:"
    echo "  scp ~/Documents/ads/ads-config.json root@YOUR_VPS:/root/ads/"
    exit 1
fi

# Check notify.py
if [ ! -f "/root/stocks/notify.py" ]; then
    echo "WARNING: /root/stocks/notify.py not found. Telegram notifications won't work."
fi

echo "  ✓ All prerequisites OK"

# ── 2. Verify API auth ──────────────────────────────────
echo ""
echo "[2/6] Testing API authentication..."

# Test Google Ads
python3 ads_api.py auth google && echo "  ✓ Google Ads OK" || echo "  ✗ Google Ads FAILED (will work after token refresh on VPS)"

# Test Facebook
python3 ads_api.py auth facebook && echo "  ✓ Facebook OK" || echo "  ✗ Facebook FAILED"

# ── 3. Initialize state files ────────────────────────────
echo ""
echo "[3/6] Initializing state files..."

# Create state files if they don't exist
[ -f "ads-suggestions.md" ] || cp ads-suggestions.md ads-suggestions.md 2>/dev/null || echo "# Pending Suggestions" > ads-suggestions.md
[ -f "ads-changes-log.md" ] || cp ads-changes-log.md ads-changes-log.md 2>/dev/null || echo "# Changes Log" > ads-changes-log.md
[ -f "ads-rotation-state.md" ] || echo "# Ad Rotation State — Not yet initialized" > ads-rotation-state.md
[ -f "ads-ab-tests.md" ] || echo "# A/B Tests — No active tests" > ads-ab-tests.md
[ -f "competitor-tracking.md" ] || echo "# Competitor Tracking — No data yet" > competitor-tracking.md
[ -f "ads-metrics-history.json" ] || echo "{}" > ads-metrics-history.json

echo "  ✓ State files ready"

# ── 4. Clone/update strategy repo ────────────────────────
echo ""
echo "[4/6] Updating strategy docs..."

if [ -d "/root/ads-management" ]; then
    cd /root/ads-management && git pull 2>/dev/null && cd /root/ads
    echo "  ✓ ads-management repo updated"
else
    cd /root && git clone https://github.com/girishkumarm/ads-management.git 2>/dev/null && cd /root/ads
    echo "  ✓ ads-management repo cloned"
fi

# ── 5. List all scheduled tasks ──────────────────────────
echo ""
echo "[5/6] Scheduled tasks available:"
echo ""
echo "  ┌─────────────────────────────────────────────────────────────────────┐"
echo "  │ UTC Time    │ IST Time       │ Task                    │ Frequency │"
echo "  ├─────────────────────────────────────────────────────────────────────┤"
echo "  │ 20 1 * * *  │ 6:50 AM        │ ads-self-renewal        │ Daily     │"
echo "  │ 27 1 * * *  │ 6:57 AM        │ ads-morning-audit       │ Daily     │"
echo "  │ 0 2 * * *   │ 7:30 AM        │ gbp-daily-seo           │ Daily     │"
echo "  │ 0 3 * * 1,4 │ 8:30 AM Mon/Th │ ads-creative-health     │ 2x/week  │"
echo "  │ 0 3 * * 1   │ 8:30 AM Mon    │ ads-ab-test-manager     │ Weekly    │"
echo "  │ 0 3 * * 5   │ 8:30 AM Fri    │ ads-ab-test-eval        │ Weekly    │"
echo "  │ 0 4 * * 1-5 │ 9:30 AM wkdays │ ads-budget-optimizer    │ Weekdays  │"
echo "  │ 0 5 * * *   │ 10:30 AM       │ gbp-qa-monitor          │ Daily     │"
echo "  │ 30 6 * * 1-5│ 12:00 PM wkdays│ ads-midday-pulse        │ Weekdays  │"
echo "  │ 0 8 * * *   │ 1:30 PM        │ ads-approval-reminder   │ Daily     │"
echo "  │ 33 12 * * * │ 6:03 PM        │ ads-evening-report      │ Daily     │"
echo "  │ 0 18 * * *  │ 11:30 PM       │ ads-token-watchdog      │ Daily     │"
echo "  │ 0 */2 * * * │ Every 2 hours  │ ads-health-ping         │ Ongoing   │"
echo "  │ * * * * *   │ Every 1 min    │ telegram-listener       │ Ongoing   │"
echo "  │ 17 0 * * 1  │ 5:47 AM Mon    │ ads-weekly-review       │ Weekly    │"
echo "  │ 30 0 * * 1  │ 6:00 AM Mon    │ godaddy-seo-monitor     │ Weekly    │"
echo "  │ 0 21 * * 0  │ 2:30 AM Sun    │ ads-competitor-watch     │ Weekly    │"
echo "  │ 0 21 * * 0  │ 2:30 AM Sun    │ ads-forecast            │ Weekly    │"
echo "  │ 0 22 1 * *  │ 3:30 AM 1st    │ ads-monthly-rollup      │ Monthly   │"
echo "  └─────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Total: 19 scheduled tasks + Telegram listener"

# ── 6. Send startup notification ─────────────────────────
echo ""
echo "[6/6] Sending startup notification..."

if [ -f "/root/stocks/notify.py" ]; then
    python3 /root/stocks/notify.py send "Ads Management System deployed!

✅ 17 agent SKILL.md files
✅ 62 API functions (Google Ads, Facebook, GBP, GoDaddy)
✅ 4 platforms configured
✅ State files initialized

Authority:
• Cafe FB Ads → FULL AUTO
• Resort FB Ads → APPROVAL ONLY
• Google Ads → APPROVAL ONLY
• GBP → AUTO + APPROVAL for replies
• GoDaddy → AUTO checks, ASK for changes

Ready to schedule crons. Run the Claude bot to set up scheduled tasks." --title "Ads Bot Deployed" --priority high
    echo "  ✓ Telegram notification sent"
else
    echo "  ⚠ Skipped (notify.py not found)"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next: Start Claude Code bot on this VPS."
echo "  It will read CLAUDE.md and schedule all crons."
echo ""
echo "  Telegram bot: Girish AdsBot"
echo "  Listener: polls every 1 minute"
echo "═══════════════════════════════════════════"
