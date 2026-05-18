---
name: nepse-earnings-trade-analyzer
description: Score NEPSE post-quarterly-result reactions using the 5-factor framework (gap %, trend stage, volume surge, distance to MA200, distance to MA50) to identify continuation vs. fade candidates. Calibrated for NEPSE's 15% daily price band and quarterly reporting cycle (Nepali fiscal year). Use after a NEPSE company files its unaudited quarterly statement and the user wants a quantitative read on the post-report move.
---

# NEPSE Earnings Trade Analyzer

NEPSE companies report quarterly under SEBON's T+30 filing rule. After a result drops, prices often move 5-15% in the next 1-3 sessions. This skill scores the post-result reaction with the same 5-factor framework used by the US `earnings-trade-analyzer`, recalibrated for NEPSE's 15% daily band.

## The 5 Factors

| Factor | What it measures | Weight |
|---|---|---:|
| Gap % | Reaction-day open vs. prior close | 20 |
| Trend stage | Stage 2 (uptrend) = bullish, Stage 4 = bearish | 25 |
| Volume surge | Reaction-day volume / 20-day average | 20 |
| Distance to MA200 | Price above MA200 = healthy | 15 |
| Distance to MA50 | Price above MA50 = healthy short-term | 20 |

Composite score 0-100; rating bands:
- 80-100: STRONG_CONTINUATION (likely to extend)
- 60-79: CONTINUATION
- 40-59: NEUTRAL
- 20-39: FADE_RISK
- 0-19: STRONG_FADE_RISK

## NEPSE-Specific Calibration

| Knob | NEPSE default | US default | Reason |
|---|---|---|---|
| Min lookback | 200 trading days | 200 | Same |
| Gap thresholds | ≥10% strong / 4-10% normal / <4% weak | ≥5% strong / 2-5% normal / <2% weak | 15% NEPSE band makes 4% gaps mid-range, 10%+ is the upper-circuit-like signal |
| Volume surge cutoff | ≥1.8× 20-day avg = bullish | ≥2.0× = bullish | NEPSE volume is sparse; relaxed |
| Reaction window | 1-3 sessions post-report | same | NEPSE intraday is less informative; daily close drives the read |

## Workflow

### Step 1: Identify reporting companies

Use `nepse-earnings-calendar` to find companies that recently filed.

### Step 2: Run the analyzer

```bash
# Single ticker post-result analysis
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --symbol NABIL --report-date 2026-05-15 \
  --output-dir reports/

# Batch (CSV of recent filers)
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --batch-csv data/recent_filers.csv --output-dir reports/
```

CSV format:
```csv
symbol,report_date
NABIL,2026-05-15
NICA,2026-05-12
UPPER,2026-05-14
```

### Step 3: Read output

- JSON: `reports/nepse_earnings_analysis_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_earnings_analysis_<YYYY-MM-DD>.md`

## Combining

- **Upstream:** `nepse-earnings-calendar` (Phase 3) to find filers
- **Downstream:** `nepse-breakout-trade-planner` for actionable plans on STRONG_CONTINUATION names
- **Validation:** `nepse-technical-analyst` on the chart for the top 2-3 results

## Limitations

- Requires accurate `--report-date`. The skill uses the next trading day's open as the reaction-open.
- A 15% upper-circuit gap is mechanically capped — the analyzer flags it but cannot distinguish "true blowout reaction" from "circuit-limited reaction".
- Bonus/right-share gaps are NOT earnings reactions — cross-reference corporate-action history before sizing on a STRONG_CONTINUATION score.
- Composite weights are NEPSE conventions, not back-tested across a full post-reform cycle.
