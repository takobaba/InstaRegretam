# Instagram Unlike Rate Limits

Empirical data from running InstaRegretam against a real account (June 2026).

## Summary

| Metric | Value |
|--------|-------|
| Total unlikes | 19,272 |
| Total blocks | 10 |
| Days active | 5 (Jun 7–11) |
| Peak hour (no block) | 1,581/hr (26.4/min) |
| Worst block trigger | ~900/hr sustained for 3+ hours |
| Block type | HTTP 429 (Too Many Requests) |
| Block duration | 6–24 hours |

## Full Hourly Timeline

```
Date         Hour   Unlikes   Cumulative   Rate/min   Note
----------------------------------------------------------------
2026-06-07   15:00  58        58           1.0
2026-06-07   16:00  258       316          4.3
2026-06-07   17:00  595       911          9.9
2026-06-07   18:00  341       1,252        5.7
2026-06-07   20:00  223       1,475        3.7
2026-06-07   21:00  237       1,712        4.0
2026-06-08   03:00  217       1,929        3.6
2026-06-08   06:00  362       2,291        6.0
2026-06-08   07:00  92        2,383        1.5
2026-06-08   08:00  410       2,793        6.8
2026-06-08   09:00  736       3,529        12.3
2026-06-08   12:00  529       4,058        8.8
2026-06-08   13:00  284       4,342        4.7
2026-06-09   07:00  90        4,432        1.5
2026-06-09   08:00  753       5,185        12.6
2026-06-09   09:00  974       6,159        16.2
2026-06-09   10:00  975       7,134        16.2
2026-06-09   11:00  922       8,056        15.4       🚨 BLOCKED
2026-06-09   13:00  4         8,060        0.1        🚨 BLOCKED x3
2026-06-10   12:00  899       8,959        15.0
2026-06-10   13:00  1,017     9,976        16.9
2026-06-10   14:00  1,023     10,999       17.1
2026-06-10   15:00  900       11,899       15.0       🚨 BLOCKED
2026-06-10   17:00  95        11,994       1.6
2026-06-10   18:00  194       12,188       3.2
2026-06-10   19:00  612       12,800       10.2       🚨 BLOCKED
2026-06-11   09:00  19        12,819       0.3        🚨 BLOCKED x3
2026-06-11   10:00  496       13,315       8.3
2026-06-11   11:00  598       13,913       10.0       🚨 BLOCKED
2026-06-11   12:00  288       14,201       4.8
2026-06-11   13:00  270       14,471       4.5
2026-06-11   15:00  394       14,865       6.6
2026-06-11   16:00  447       15,312       7.5
2026-06-11   17:00  326       15,638       5.4
2026-06-11   18:00  764       16,402       12.7
2026-06-11   19:00  1,289     17,691       21.5
2026-06-11   20:00  1,581     19,272       26.4
```

## Daily Totals

| Date | Unlikes | Blocks |
|------|---------|--------|
| Jun 7 | 1,712 | 0 |
| Jun 8 | 2,630 | 0 |
| Jun 9 | 3,718 | 4 |
| Jun 10 | 4,740 | 2 |
| Jun 11 | 6,472 | 4 |

## Block Events

| # | Time | Session Unlikes | Speed | Note |
|---|------|----------------|-------|------|
| 1 | Jun 09 11:59 | 3,387 | DIRECT | After 3+ hrs at 15/min |
| 2 | Jun 09 12:58 | 0 | SAFE | Retry during cooldown |
| 3 | Jun 09 13:16 | 0 | SAFE | Retry during cooldown |
| 4 | Jun 09 13:48 | 4 | SAFE | Retry during cooldown |
| 5 | Jun 10 15:53 | 3,815 | DIRECT | After 4 hrs at 15–17/min |
| 6 | Jun 10 19:44 | 528 | DIRECT | Resumed too soon |
| 7 | Jun 11 08:05 | 0 | DIRECT | Still in cooldown |
| 8 | Jun 11 08:19 | 0 | SAFE | Still in cooldown |
| 9 | Jun 11 09:23 | 0 | SAFE | Still in cooldown |
| 10 | Jun 11 11:30 | 798 | DIRECT | After 2 hrs at 10/min |

## Key Observations

1. **Blocks are inconsistent.** Early blocks fired at ~900/hr sustained 3+ hours, but the final session ran 1,289–1,581/hr for 2 hours with zero blocks.
2. **Account "warms up" over time.** Day 1 was cautious (~300/hr avg), by Day 5 the account tolerated 1,500+/hr.
3. **Retrying during cooldown always fails.** Blocks 2–4 and 7–9 all triggered instantly when attempting to resume too early.
4. **Unlike is low-priority for Instagram's anti-abuse system.** 19,272 unlikes in 5 days with only 10 blocks is remarkably lenient.
5. **Rolling window, not fixed daily reset.** The limit appears to be a rolling 24h window — spacing sessions helps.
6. **The `cl.delay_range = [1, 3]` library delay is sufficient** for Direct mode in most cases.

## Recovery Rules

- **First 429**: Stop immediately. Do not retry.
- **Wait time**: At least 12–24 hours before trying again.
- **Resume**: If blocked, wait until the next day. Retrying in the same day extends the block.
- **Retrying during a block extends the block** — never retry 429 responses.

## Notes

- Account was ~10 years old with normal usage history.
- All runs used residential IP (home network).
- Instagram's limits may vary by account age, trust level, and internal changes.
- The `cl.delay_range = [1, 3]` built into instagrapi adds 1–3s between API calls regardless of speed mode.
