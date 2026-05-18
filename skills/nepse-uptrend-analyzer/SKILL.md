---
name: nepse-uptrend-analyzer
description: Compute the NEPSE Uptrend Ratio — the percentage of listed names trading above their 200-day SMA — as a single trend-strength gauge. Tracks the 1-year history of the ratio to identify regime shifts, bullish/bearish thresholds, and divergences vs. the NEPSE composite index. Use when the user asks "is NEPSE in an uptrend?", wants a single trend-health number, or needs context for position sizing across the portfolio.
---

# NEPSE Uptrend Analyzer

Computes the NEPSE Uptrend Ratio — what % of the ~284-name NEPSE universe is trading above its 200-day SMA — and tracks its trajectory. A single number that captures broad-market trend strength.

## Why this skill is distinct from `nepse-market-breadth-analyzer`

- `nepse-market-breadth-analyzer` is a daily snapshot of 6+ breadth indicators.
- `nepse-uptrend-analyzer` is a focused single-metric tracker with historical context, designed for regime classification and divergence detection vs. the NEPSE composite.

## When to Use

- User asks "is NEPSE in an uptrend?" or "is the trend healthy?"
- User wants a one-number trend gauge for sizing decisions
- User wants to spot divergence between the index and breadth (often precedes tops)
- Daily ritual before running individual-name screens

## What it Computes

- **Uptrend Ratio (current):** % of eligible names above their 200-day SMA
- **Uptrend Ratio (history):** 1-year daily series of the same metric
- **Regime label:**
  - `STRONG_UPTREND`: ratio ≥ 70%
  - `UPTREND`:        50% ≤ ratio < 70%
  - `NEUTRAL`:        30% ≤ ratio < 50%
  - `DOWNTREND`:      ratio < 30%
- **Divergence flag:** index making new highs while ratio falls (warning)

## Workflow

### Step 1: Run

```bash
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --output-dir reports/

# History window (default: 252 trading days = ~1 year)
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --history-days 504 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_uptrend_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_uptrend_<YYYY-MM-DD>.md` with the regime call, trend, and divergence

### Step 3: Combine

- Feed the regime label to `exposure-coach` (market-agnostic) for portfolio sizing
- Cross-check with `nepse-market-breadth-analyzer` for confirmation
- Use the divergence flag with `nepse-market-top-detector` for top warnings

## NEPSE-Specific Notes

- A regime of `STRONG_UPTREND` on NEPSE often coincides with microfinance euphoria — be especially alert for tops via `nepse-market-top-detector`.
- The 200-day SMA threshold is the same as US, but NEPSE has more low-liquidity names that bias the count. Eligible-only filter (≥150 trading days) keeps this in check.
- Divergence detection compares NEPSE composite index highs vs. uptrend-ratio highs — a 5%+ gap is the classic precursor to Stage 3.

## Limitations

- Like `nepse-market-breadth-analyzer`, requires the full universe to be fetchable. First-run time ~8-10 min; subsequent runs faster via disk cache.
- Historical ratios require historical OHLCV for every name — the full-history series may take longer to backfill.
- Regime thresholds (70/50/30%) are NEPSE conventions and have not been backtested across a full post-2025-reform NEPSE cycle.
