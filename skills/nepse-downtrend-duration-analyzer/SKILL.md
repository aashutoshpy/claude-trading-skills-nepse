---
name: nepse-downtrend-duration-analyzer
description: Analyze NEPSE composite index history to identify past downtrends, measure their duration (peak-to-trough and trough-to-recovery), and produce a distribution of historical correction lengths. Use when the user wants context for how long a current NEPSE pullback might last, how prior corrections compare, or what depths are historically typical.
---

# NEPSE Downtrend Duration Analyzer

Reads the NEPSE composite index history, detects peaks and troughs that meet a minimum drawdown threshold (default 10%), and reports:
- Each historical downtrend's start, trough, recovery date, depth, and duration
- A distribution of durations (median, P25, P75, max)
- Where the *current* drawdown sits in that distribution (if one is in progress)

## When to Use

- "How long do NEPSE corrections usually last?"
- "Is this drawdown unusually deep or unusually long?"
- "When should I expect recovery?"
- Sizing decisions during an active correction

## What it Computes

For each historical downtrend (≥ `--min-depth-pct` peak-to-trough drawdown):

| Field | Definition |
|---|---|
| `peak_date` / `peak_close` | The local index high that started the decline |
| `trough_date` / `trough_close` | The local low (deepest point of the decline) |
| `depth_pct` | (trough - peak) / peak × 100 (negative) |
| `decline_days` | Trading days from peak to trough |
| `recovery_date` | First trading day where index ≥ peak again (None if still in drawdown) |
| `recovery_days` | Trading days from trough to recovery (None if still in drawdown) |
| `total_days` | decline_days + recovery_days |

## NEPSE-Specific Notes

- NEPSE post-political-transition history (since late 2025) is short. Pre-2025 corrections used Sun-Thu trading week — durations are not directly comparable to post-2025 (Mon-Fri) corrections in *trading days* but should be similar in *calendar days*.
- The 15% daily price band (since April 2026) means recent corrections may compress vs. historical (single-day moves are larger).
- Microfinance- or hydropower-led corrections can have asymmetric recoveries: index may recover before the lagging sectors do.

## Workflow

### Step 1: Run

```bash
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --output-dir reports/

# Custom drawdown threshold
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --min-depth-pct 7.0 --output-dir reports/

# Long history (more years of data)
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --lookback-days 3650 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_downtrend_history_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_downtrend_history_<YYYY-MM-DD>.md` with the table + distribution

## Limitations

- Peak/trough detection uses a simple local-extrema algorithm with a configurable lookback; major-correction definitions may differ from technical analysts'.
- NEPSE composite index OHLCV must be fetchable via the configured backend.
- Pre-political-transition data is included in the distribution unless excluded with `--since 2025-11-01`. Mixing old (Sun-Thu) and new (Mon-Fri) regimes biases the trading-day count.
