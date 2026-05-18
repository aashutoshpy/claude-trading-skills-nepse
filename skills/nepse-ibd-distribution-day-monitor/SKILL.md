---
name: nepse-ibd-distribution-day-monitor
description: Monitor the NEPSE composite index for IBD-style distribution days — sessions where the index closes down ≥0.2% on higher volume than the prior session. Counts active distribution days in the rolling 25-session window; ≥5 signals institutional distribution risk. Use when the user asks "is the NEPSE rally in danger?", wants top-of-market warning signals, or needs context before increasing exposure.
---

# NEPSE IBD Distribution Day Monitor

Applies William O'Neil's distribution-day framework to the NEPSE composite index. A "distribution day" is a session where the index closes down at least 0.2% on volume HIGHER than the previous session — interpreted as institutional selling. When 4-5+ accumulate within a 25-session rolling window, the market is at heightened top-risk.

## Why this matters for NEPSE

The IBD distribution-day rule is universal (works for any liquid index), but NEPSE has wrinkles:
- NEPSE composite is heavily bank- and hydropower-weighted, so a distribution day often masks a broad small-name decline
- NEPSE moved to a 15% daily price band in April 2026 — single-day moves are mechanically larger, so the 0.2% threshold is unchanged (relative to closing-price magnitude)
- NEPSE has a shorter post-political-transition history (Mon-Fri week since late 2025), so the 25-session lookback only just spans the new regime

## When to Use

- User asks "are there distribution days on NEPSE?"
- User wants top-of-market warning signals before increasing exposure
- Daily monitoring after a long uptrend (≥3 months)
- As an input to `nepse-market-top-detector` (Phase 2)

## Workflow

### Step 1: Run

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --output-dir reports/

# Custom thresholds
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --window 25 --min-down-pct 0.2 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_distribution_days_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_distribution_days_<YYYY-MM-DD>.md`

### Step 3: Combine

- Feed JSON to `nepse-market-top-detector` (Phase 2)
- Cross-check with `nepse-uptrend-analyzer` divergence flag
- Use as a sizing input alongside `nepse-market-breadth-analyzer` regime call

## Interpretation Table

| Active distribution days (last 25 sessions) | Read as |
|---|---|
| 0-2 | Healthy uptrend; no institutional selling |
| 3 | Caution; tighten stops |
| 4 | Heightened risk; pause new positions |
| **≥5** | Institutional distribution likely; reduce exposure |
| ≥6 | Almost always precedes a 5-15% NEPSE correction |

## Expiry Rules (per O'Neil)

- A distribution day "expires" after 25 trading sessions (rolls off the window)
- A distribution day is also cancelled if the index later rallies 5%+ from that day's close (the selling was absorbed)

## Limitations

- Requires NEPSE composite index OHLCV with reliable volume. If the index endpoint returns zero/missing volume, the skill cannot run.
- The 25-session window assumes consistent trading. Post-political-transition NEPSE has had a few session-length changes — interpret historical comparisons carefully.
- O'Neil's framework was developed on US markets where individual-name distribution patterns are visible; NEPSE composite is more BFI-dominated and may show distribution differently from a more diversified index.
