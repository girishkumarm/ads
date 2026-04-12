#!/bin/bash
# Ads Bot Auto-Restart Script
# Usage: bash /home/girish/ads/start-ads-bot.sh

cd /home/girish/ads

# Pull latest code
git pull 2>/dev/null

# Start Claude Code with the bootstrap prompt
claude -p "$(cat <<'PROMPT'
git pull, re-read CLAUDE.md, schedule all 18 crons from the Scheduled Tasks table, start Telegram listener polling every 1 minute.

Read memory files at /home/girish/.claude/projects/-home-girish-ads/memory/ — especially project_session_state_apr3.md and project_weekend_budget.md for pending tasks.

Key pending items:
1. Sunday Apr 6: Reduce Google Ads budget Rs 5K to Rs 3K (budget resource: customers/2995160429/campaignBudgets/13947907650)
2. Run 20-agent deep review of all ads across Google and Facebook
3. Google Ads API uses google-ads Python library (already pip installed), not REST API
4. Test all APIs (Google Ads, Facebook, GA4) and confirm status via Telegram

Start operating immediately. All state is in memory files and daily reports.
PROMPT
)"
