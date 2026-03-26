# A/B Tests — Active and Completed

## How to create a test
Add a new section below with format:
```
## TEST-{NNN} [PENDING|RUNNING|WINNER_A|WINNER_B|INCONCLUSIVE]
Campaign: {campaign name}
Variant A (Control): AD_ID — "ad description"
Variant B: AD_ID — "ad description"
Primary metric: {cost_per_call|ctr|cpc}
Start: {DATE}
Min duration: 7 days
Min impressions per variant: 1000
```

The `ads-ab-test-manager` agent will manage running tests automatically.

---

*No active tests yet.*
