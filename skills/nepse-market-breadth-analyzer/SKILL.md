---
name: nepse-market-breadth-analyzer
description: Compute NEPSE market breadth indicators — advances vs. declines, new 52-week highs/lows, % of constituents above 50-day and 200-day SMAs, sector participation — from the full NEPSE universe via NepseClient. Use when the user asks about NEPSE market health, breadth signals, "is the rally narrow or broad", or wants context for sizing decisions across the whole portfolio.
---

# NEPSE Market Breadth Analyzer

Reads the full NEPSE universe (~284 names) via `common.nepse.NepseClient`, computes daily breadth indicators, and emits a regime-aware summary.

## When to Use

- User asks "is the NEPSE rally broad or narrow?"
- User wants to size up/down based on market breadth (call this BEFORE individual-name screens like `nepse-vcp-screener`)
- User asks about new highs/lows or A/D ratio for NEPSE
- Pre-condition for `exposure-coach` (shared US/NEPSE skill) to make exposure recommendations

## What it Computes

| Indicator | Formula | What it tells you |
|---|---|---|
| A/D ratio | advances / declines (same session) | >1.5 = broad strength; <0.7 = broad weakness |
| New 52-wk highs | count of names making a new 252-trading-day high | rising = healthy market; falling while index rises = narrowing |
| New 52-wk lows | count of names making a new 252-trading-day low | >20 = caution; >40 = broad weakness |
| % above 50-SMA | constituents trading above their 50-day SMA | >60% = healthy; <30% = weak |
| % above 200-SMA | constituents trading above their 200-day SMA | >55% = bull regime; <40% = bear regime |
| Sector participation | per-sector A/D | spot rotation (banks weak, hydro strong, etc.) |

## Workflow

### Step 1: Run

```bash
# Default: compute breadth for today
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --output-dir reports/

# Backfill a specific date (needs cached or live history)
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --as-of 2026-05-15 --output-dir reports/
```

### Step 2: Read the output

- JSON: `reports/nepse_breadth_<YYYY-MM-DD>.json` — machine-readable; used by `exposure-coach` and `nepse-macro-regime-detector`
- Markdown: `reports/nepse_breadth_<YYYY-MM-DD>.md` — human summary with regime call

### Step 3: Combine

- Feed JSON to `nepse-macro-regime-detector` (Phase 2) for full regime context
- Feed to `exposure-coach` (existing market-agnostic skill) for portfolio sizing recommendation
- Use the per-sector breakdown to confirm `nepse-sector-analyst` calls

## NEPSE-Specific Calibration

| Threshold | NEPSE default | Why |
|---|---|---|
| New-high lookback | **252 trading days** | Same as US (1 year); NEPSE Mon-Fri = ~250/year |
| % above 50-SMA bull threshold | **60%** | Same as US (broadly tested) |
| % above 200-SMA bull regime | **55%** | Slightly lower than US 60%; NEPSE has more low-liquidity names dragging the count |
| Min trading days required | **150** | Below this, the name is excluded (not enough history for SMAs) |

## Limitations

- Requires the full universe to be fetchable. With the default `nepalstock` backend this means ~284 OHLCV requests; throttle is ~2s/req → expect 8-10 minutes per run. Use `--limit` to cap during testing.
- Names with sparse trading produce noisy SMAs; excluded if < `--min-trading-days`.
- The first run will populate `common/nepse/` disk cache; subsequent runs are much faster.

## Resources

- [references/nepse_breadth_indicators.md](references/nepse_breadth_indicators.md) — interpretation guide, regime thresholds, historical caveats
