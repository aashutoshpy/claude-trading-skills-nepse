---
name: nepse-canslim-screener
description: CANSLIM-style screening adapted for NEPSE. Combines OHLCV-derived factors (M = market direction, S = supply/demand from volume surge, L = leader via relative strength, I = institutional via large floorsheet trades, N = new highs proxy) with a user-supplied fundamentals CSV (C = current earnings, A = annual earnings) since NEPSE backends do not expose fundamentals. Use when the user asks for NEPSE growth-stock screening, CANSLIM candidates, or William O'Neil style setups on Nepali stocks.
---

# NEPSE CANSLIM Screener

Adapts O'Neil's 7-factor CANSLIM framework to NEPSE. Three factors (C, A, N) need fundamentals that NEPSE backends do not expose — so this skill accepts a user-maintained CSV. The other four (S, L, I, M) are computed from OHLCV + breadth/sector outputs.

## What CANSLIM Stands For (NEPSE adaptation)

| Letter | Original | NEPSE input | Source |
|---|---|---|---|
| **C**urrent quarterly EPS | YoY growth in latest quarter | `--fundamentals-csv` (EPS column) | User CSV from sharesansar |
| **A**nnual EPS growth | 3-year EPS CAGR | `--fundamentals-csv` (eps_3y_cagr column) | User CSV |
| **N**ew product / new highs | Price near 52-week high | OHLCV → 52-week high proximity | Auto |
| **S**upply & demand | Volume surge on advance days | OHLCV → volume vs. 50-day avg | Auto |
| **L**eader (relative strength) | RS vs. NEPSE composite | OHLCV + NEPSE index | Auto |
| **I**nstitutional sponsorship | Large floorsheet trades | (Optional) `--floorsheet-day` for floorsheet snapshot | Auto, partial |
| **M**arket direction | NEPSE in uptrend? | `nepse-uptrend-analyzer` JSON | Upstream |

Composite score 0-100 weighted across all 7 factors.

## NEPSE-Specific Notes

- **Hydropower bias risk:** 97 of 284 NEPSE listings are hydropower. Without a sector-aware filter, screens often surface 30+ hydropower names. The skill defaults to a hard per-sector cap (`--max-per-sector 5`).
- **Microfinance growth distortion:** microfinance EPS growth can spike 200%+ on regulatory changes (e.g., interest-cap relaxation). The skill caps EPS growth scoring at 100% so a one-off doesn't dominate.
- **"M" factor is gated by `nepse-uptrend-analyzer`:** if M = `DOWNTREND`, no candidates are returned regardless of score. CANSLIM is a long-only methodology and requires bull-market conditions.

## Workflow

### Step 1: Prepare fundamentals CSV (recommended)

Manually export from sharesansar:

```csv
symbol,eps_latest,eps_prior_year,eps_3y_cagr,sales_3y_cagr
NABIL,32.5,28.4,11.5,9.2
NICA,42.1,36.8,14.2,8.1
UPPER,3.8,2.1,32.0,28.5
```

### Step 2: Run upstream skills first

```bash
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
```

### Step 3: Run the CANSLIM screener

```bash
python3 skills/nepse-canslim-screener/scripts/screen_canslim.py \
  --fundamentals-csv data/nepse_fundamentals.csv \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --output-dir reports/

# Strict M gate (only run if STRONG_UPTREND)
python3 skills/nepse-canslim-screener/scripts/screen_canslim.py \
  --fundamentals-csv data/nepse_fundamentals.csv \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --require-strong-uptrend \
  --output-dir reports/
```

### Step 4: Read output

- JSON: `reports/nepse_canslim_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_canslim_<YYYY-MM-DD>.md` with per-candidate component breakdown

## Limitations

- C and A factors are only as accurate as your fundamentals CSV. Without it, the screener falls back to S+L+N+M (4 of 7 factors) — still useful but less powerful.
- I (institutional) factor is partial — the floorsheet aggregation is a crude proxy for institutional flow. NEPSE has no 13F equivalent.
- Hydropower projects often have very small EPS (single-digit NPR) on a much smaller share base. EPS-based ranks can mislead — favor sales growth and price action for hydropower names.
- Composite weights are NEPSE conventions, not back-tested across a full post-reform NEPSE cycle.
