---
name: ads-self-renewal
description: Daily 6:50 AM IST — Verify all scheduled tasks exist and are active. Flag any missing tasks for re-creation.
---

## SELF-RENEWAL — SCHEDULED TASK HEALTH CHECK

Working directory: /root/ads
NOTIFICATION: python3 /root/stocks/notify.py
DATE: Run `TZ='Asia/Kolkata' date +%Y-%m-%d` to get today's date.

### STEP 0: No Gate Check

This task ALWAYS runs. It is the guardian of all other tasks.

### STEP 1: Define Expected Tasks

The following scheduled tasks MUST exist and be enabled:

| Task ID | Schedule (cron) | Description |
|---------|----------------|-------------|
| ads-self-renewal | `20 1 * * *` (6:50 AM IST) | This task (self-check) |
| ads-morning-audit | `27 1 * * *` (6:57 AM IST) | Morning 7-agent audit |
| gbp-daily-seo | `0 2 * * *` (7:30 AM IST) | GBP review/insights check |
| ads-creative-health | `0 3 * * 1,4` (8:30 AM Mon/Thu) | URL & UTM validation |
| ads-ab-test-manager | `0 3 * * 1,5` (8:30 AM Mon/Fri) | A/B test setup (Mon) & evaluation (Fri) |
| ads-budget-optimizer | `0 4 * * 1-5` (9:30 AM IST) | Budget shift by efficiency |
| gbp-qa-monitor | `0 5 * * *` (10:30 AM IST) | GBP Q&A monitoring |
| ads-midday-pulse | `30 6 * * 1-5` (12:00 PM IST) | Midday pacing check |
| ads-approval-reminder | `0 8 * * *` (1:30 PM IST) | Pending suggestion follow-up |
| ads-evening-report | `33 12 * * *` (6:03 PM IST) | Evening daily report |
| ads-token-watchdog | `0 18 * * *` (11:30 PM IST) | Auth token health check |
| ads-health-ping | `0 */2 * * *` (every 2 hours) | Quick health checks |
| ads-weekly-review | `17 0 * * 1` (5:47 AM Mon) | Deep weekly analysis |
| godaddy-seo-monitor | `30 0 * * 1` (6:00 AM Mon) | Domain/SSL/DNS audit |
| ads-competitor-watch | `0 21 * * 0` (2:30 AM Sun) | Weekly competitor intel |
| ads-forecast | `0 21 * * 0` (2:30 AM Sun) | Weekly forecast & projections |
| ads-monthly-rollup | `0 22 1 * *` (3:30 AM 1st of month) | Monthly summary report |

### STEP 2: Check Existing Tasks

List all currently scheduled tasks. Compare against the expected list above.

For each expected task:
1. Check if it exists
2. Check if it is enabled (not paused/disabled)
3. Check if the cron expression is correct

### STEP 3: Report Findings

Build a status report:
```
SELF-RENEWAL CHECK — {DATE}

TASK STATUS:
  {TASK_ID}: {FOUND & ENABLED / FOUND BUT DISABLED / MISSING}
  ...

Summary: {X}/{TOTAL} tasks healthy, {Y} missing, {Z} disabled
```

### STEP 4: Alert on Issues

**If any tasks are MISSING:**
```bash
python3 /root/stocks/notify.py send "MISSING SCHEDULED TASKS:

{For each missing task:}
- {TASK_ID}: {DESCRIPTION}

These tasks need to be re-created. Claude Code scheduled tasks expire after 7 days.

Action: Re-create missing tasks using their SKILL.md definitions in /root/ads/server/scheduled-tasks/" --title "Missing Tasks" --priority high --audience girish
```

**If any tasks are DISABLED:**
```bash
python3 /root/stocks/notify.py send "DISABLED SCHEDULED TASKS:

{For each disabled task:}
- {TASK_ID}: {DESCRIPTION}

These tasks exist but are not running. Re-enable them." --title "Disabled Tasks" --priority high --audience girish
```

**If all OK:**
Stay silent — no need to send "all good" daily.

### STEP 5: Auto-Recreate Missing Tasks (If Possible)

If any tasks are missing and their SKILL.md files exist at `/root/ads/server/scheduled-tasks/{TASK_ID}/SKILL.md`, attempt to recreate them with the correct cron expression from the table in Step 1.

Log any re-creations:
```bash
python3 /root/stocks/notify.py send "Auto-recreated {N} missing scheduled tasks:
{List of tasks recreated}

All tasks should now be active." --title "Tasks Restored" --audience girish
```

### CLEANUP
No browser used. No locks. Metadata-only check.
