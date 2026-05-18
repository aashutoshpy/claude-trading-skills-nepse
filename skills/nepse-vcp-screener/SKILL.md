---
name: nepse-vcp-screener
description: Screen the NEPSE (Nepal Stock Exchange) universe for Mark Minervini's Volatility Contraction Pattern (VCP). Identifies Stage-2-uptrend stocks forming tight bases with contracting price ranges near a breakout pivot. Use when the user asks for NEPSE VCP screening, tight base / volatility contraction patterns on Nepali stocks, or Stage 2 momentum candidates in NEPSE. NOT for US stocks — use vcp-screener instead.
---

# NEPSE VCP Screener

Adapts Minervini's Volatility Contraction Pattern to the Nepal Stock Exchange. Reads OHLCV via `common.nepse.NepseClient` so it works against either backend (nepalstock.com.np scraper or community library).

## When to Use

- User asks for VCP / Stage 2 / tight-base screening on NEPSE
- User mentions Minervini-style setups in the context of Nepali stocks
- User wants a NEPSE candidate list for swing-trade planning

## Prerequisites

- No API key (NEPSE backends are public). Default backend is the `nepalstock` scraper.
- Choose backend via `NEPSE_BACKEND=nepalstock|community` or `--backend`.
- Optional: rebuild the universe cache via `scripts/refresh_nepse_universe.py` (planned).

## NEPSE-Specific Calibration

The US VCP screener assumes a 10% daily band; NEPSE moved to **15% on April 17, 2026**, which makes single-day moves that used to be "limit" merely mid-range. This skill recalibrates accordingly:

| Parameter | US default | NEPSE default | Why |
|---|---|---|---|
| `--min-contractions` | 2 | 2 | Same — pattern is universal |
| `--max-final-contraction-pct` | 10% | **6%** | NEPSE tight bases compress more in absolute % terms because 15% band lets ranges expand wider |
| `--min-base-days` | 25 | **15** | NEPSE volume is sparse; shorter bases form more often |
| `--avg-volume-min` | varies | **5,000 shares/day** | NEPSE volume is 1-2 orders of magnitude lower than US |
| `--stage2-sma200-rising-days` | 30 | **20** | Adjusted for shorter NEPSE histories |

## Workflow

### Step 1: Run the screener

```bash
# Default: full NEPSE universe, top 30 candidates
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --output-dir reports/

# Specific symbols only
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols NABIL UPPER NICA --output-dir reports/

# Tighter contractions (research/backtest)
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --min-contractions 3 --max-final-contraction-pct 4 \
  --output-dir reports/
```

### Step 2: Review

- JSON: `reports/nepse_vcp_<YYYY-MM-DD>.json` — machine-readable, used by `nepse-breakout-trade-planner`
- Markdown: `reports/nepse_vcp_<YYYY-MM-DD>.md` — human-readable summary

### Step 3: Combine

- Feed JSON to `nepse-breakout-trade-planner` (Phase 3) for manual-entry plans
- Cross-reference candidates against `nepse-margin-eligibility` to know which can be traded on margin
- Run `nepse-technical-analyst` on the top 3-5 with a chart screenshot for visual confirmation

## Output Schema

Each candidate row contains:

```yaml
symbol: NABIL
name: Nabil Bank Limited
sector: BANKING
price: 1245.0
sma_50: 1180.5
sma_200: 1095.2
sma200_extension_pct: 13.7
base_days: 22
contractions: 3
final_contraction_pct: 5.2
pivot_price: 1252.0          # last swing high
distance_to_pivot_pct: 0.6
valid_vcp: true
composite_score: 78          # 0-100
margin_eligible: true        # cross-referenced via registry
```

## Resources

- `references/nepse_vcp_methodology.md` — NEPSE-specific pattern interpretation, why the 15% band changes everything
- See also: [vcp-screener](../vcp-screener/) — US sibling skill

## Limitations

- The NEPSE OHLCV backend endpoints are public but undocumented; the scraper assumes specific JSON shapes that may change. If the screener returns zero candidates unexpectedly, first verify `python3 -c "from common.nepse import NepseClient; print(len(NepseClient.create().list_constituents()))"` returns a non-zero count.
- Pattern detection is descriptive, not predictive. Backtest before sizing.
