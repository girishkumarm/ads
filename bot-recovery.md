# Bot Recovery Guide — Shared Across All Claude Bots

## Bot Processes

| Bot | Working Dir | Start Command | Telegram Config |
|-----|------------|---------------|-----------------|
| Ads Bot | /home/girish/ads | `claude -p "git pull, re-read CLAUDE.md, schedule all 18 crons, start Telegram listener polling every 1 minute. Read memory files."` | Uses /home/girish/claude/notify.py (audience: girish) |
| Stocks Bot | /home/girish/stocks | `claude -p "git pull, re-read CLAUDE.md, schedule all crons, start Telegram listener. Check current market state."` | Uses /home/girish/stocks/notify.py or /home/girish/claude/notify.py |
| Claude Bot | /home/girish/claude | Already running with 1-min Telegram poll cron | Uses /home/girish/claude/notify.py |

## How to Check if a Bot is Running

```bash
# Find all Claude processes and their working directories
ps aux | grep claude | grep -v grep
# Check working directory of a PID
ls -la /proc/<PID>/cwd
```

## How to Restart a Stuck Bot

### Ads Bot
```bash
# Find and kill the ads bot
ps aux | grep claude | grep -v grep  # Find PID with cwd /home/girish/ads
kill <PID>
sleep 3
# Restart
cd /home/girish/ads
nohup claude -p "git pull, re-read CLAUDE.md, schedule all 18 crons from the Scheduled Tasks table, start Telegram listener polling every 1 minute. Read memory files at /home/girish/.claude/projects/-home-girish-ads/memory/ for pending tasks. Start operating immediately." > /home/girish/ads/ads-bot.log 2>&1 &
```

### Stocks Bot
```bash
# Find and kill the stocks bot
ps aux | grep claude | grep -v grep  # Find PID with cwd /home/girish/stocks
kill <PID>
sleep 3
# Restart
cd /home/girish/stocks
nohup claude -p "git pull, re-read CLAUDE.md, schedule all crons, start Telegram listener polling every 1 minute. Check current market state and positions. Read memory files. Start operating immediately." > /home/girish/stocks/stocks-bot.log 2>&1 &
```

## Common Issues

1. **Crons expired** — Claude Code crons auto-expire after 7 days. Bot is running but doing nothing. Fix: restart the bot.
2. **409 Conflict on Telegram** — Two processes polling the same bot token. Fix: kill ALL instances, wait 10s, restart one.
3. **Bot process exists but unresponsive** — Memory/CPU overload. Fix: `kill -9 <PID>`, restart.
4. **Menu bot down** — `curl http://localhost:3100/health`. If down: `nohup node /home/girish/claude/resort-menu-bot/app.js > /home/girish/claude/resort-menu-bot/app.log 2>&1 &`

## Server Info
- IP: 135.181.254.33
- Resort menu app: port 3100
- LiteLLM proxy: port 4000
