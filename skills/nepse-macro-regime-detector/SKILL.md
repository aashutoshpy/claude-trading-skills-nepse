---
name: nepse-macro-regime-detector
description: Detect the macro regime affecting NEPSE — NRB monetary policy stance (currently tightening), USD/NPR direction, India Nifty 50 correlation read, Brent oil as import-cost proxy, and gold. Combines macro signals with breadth/sector inputs from other NEPSE skills to produce a regime label (RISK_ON / NEUTRAL / RISK_OFF) and a one-page rationale. Use when the user asks "what's the NEPSE macro regime?", needs context before sizing, or wants a regime-aware exposure recommendation.
---

# NEPSE Macro Regime Detector

Reads a small set of macro inputs (some seeded from `config/nepse_rules.yaml`, some from a user-supplied CSV for time-varying values) and combines them with breadth and sector outputs to produce a one-page regime call.

## Inputs

| Input | Source | Update cadence |
|---|---|---|
| NRB repo rate | `config/nepse_rules.yaml` → `capital_gains_tax` / NRB section (seed) or `--macro-csv` | Update on each NRB monetary policy meeting (quarterly) |
| NRB rate direction | `--macro-csv` (`rate_direction: easing\|tightening\|neutral`) | Same as above |
| USD/NPR direction | `--macro-csv` (`usd_npr_pct_change_30d`) | Monthly |
| India Nifty 50 ratio | `--macro-csv` (`nifty50_ytd_pct`) | Monthly |
| Brent oil proxy | `--macro-csv` (`brent_ytd_pct`) | Monthly |
| Gold direction | `--macro-csv` (`gold_ytd_pct`) | Monthly |
| NEPSE breadth regime | `reports/nepse_breadth_*.json` (latest) | Daily |
| NEPSE sector leadership | `reports/nepse_sectors_*.json` (latest) | Daily |

## Why no FMP / yfinance integration

The user chose Python-only with the two NEPSE backends; neither covers global macro data. To keep the skill offline-friendly and free, we accept a user-maintained `macro.csv` for the global macro inputs (~5 numbers, updated monthly). NEPSE-specific inputs (NRB, breadth, sectors) come from the foundation + sibling skills.

## CSV format

```csv
key,value,as_of
nrb_repo_pct,5.0,2026-03-30
rate_direction,tightening,2026-03-30
usd_npr_pct_change_30d,-0.8,2026-05-10
nifty50_ytd_pct,12.5,2026-05-10
brent_ytd_pct,8.3,2026-05-10
gold_ytd_pct,18.2,2026-05-10
```

## Workflow

### Step 1: Update the macro CSV

Manually maintain `data/nepse_macro.csv` from public sources:
- NRB rate: nrb.org.np monetary policy archive
- USD/NPR: forex.com.np or similar
- Nifty 50, Brent, gold: tradingeconomics.com or any major financial portal

### Step 2: Run

```bash
# Aggregate macro + latest NEPSE breadth/sector reports
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv \
  --reports-dir reports/ \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_macro_regime_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_macro_regime_<YYYY-MM-DD>.md` with the regime label and contributing signals

## Regime Labels

| Label | Conditions |
|---|---|
| `RISK_ON` | NRB easing OR (NRB neutral + NEPSE breadth BULL_BROAD); favorable global macro |
| `NEUTRAL` | NRB neutral, breadth mixed, global macro mixed |
| `RISK_OFF` | NRB tightening (current state May 2026) + breadth BEAR_* OR distribution-day risk HIGH+ |
| `STAGFLATION` | NRB tightening + Brent up >15% YTD + INR/NPR weakening |

## NEPSE-Specific Macro Notes

- **NRB tightening is the current regime (May 2026):** repo rate stepped from 4.25% (Dec 2025) → 5.0% (Jan-Mar 2026). Bank and finance sectors typically lag in tightening regimes.
- **USD/NPR matters because of imports:** NEPSE-listed manufacturers and traders have NPR-cost / USD-input dynamics. Persistent NPR weakness pressures margins.
- **Nifty 50 correlation:** NEPSE is loosely correlated with India equities (mostly through risk-on/risk-off sentiment, not direct flow). A strong Nifty year often coincides with NEPSE strength but with a lag.
- **Brent matters for imported energy costs:** higher Brent → higher fuel/cement input costs → manufacturing margin pressure.
- **Gold:** rising gold often correlates with NEPSE risk-off (Nepali investors rotate to gold as a defensive asset).

## Limitations

- The macro CSV is manually maintained — staleness is a real risk. The skill flags `as_of` dates more than 35 days old as suspect.
- Regime classifications are heuristic; not back-tested across a full NEPSE cycle.
- Global macro inputs (Nifty, Brent, gold) only capture coarse directional signal; no factor-model decomposition.
