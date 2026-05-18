---
name: nepse-stanley-druckenmiller-investment
description: Synthesize NEPSE macro, micro, and sentiment signals into a Druckenmiller-style top-down read for NEPSE positioning. Combines NRB monetary policy, USD/NPR, India Nifty correlation, NEPSE breadth, sector rotation, top-risk score, and uptrend regime into a single bias score and recommended portfolio tilt. Use when the user wants a top-down NEPSE thesis, a macro-overlay sizing decision, or a Druckenmiller-style "is the cycle with me" check.
---

# NEPSE Stanley Druckenmiller Investment

Druckenmiller's framework: top-down, concentrated, large positions when conviction is high; small or no position when it isn't. This skill adapts that decision-making process to NEPSE by combining outputs from several other NEPSE skills into a single bias call and recommended portfolio tilt.

## What it Synthesizes

| Signal | Source | Weight |
|---|---|---:|
| NRB monetary stance | `nepse-macro-regime-detector` JSON | 20 |
| NEPSE composite regime | `nepse-uptrend-analyzer` JSON | 15 |
| Breadth regime | `nepse-market-breadth-analyzer` JSON | 15 |
| Sector leadership clarity | `nepse-sector-analyst` JSON | 10 |
| Top-risk score | `nepse-market-top-detector` JSON | 15 |
| Distribution days | `nepse-ibd-distribution-day-monitor` JSON | 10 |
| USD/NPR direction | `nepse-macro-regime-detector` inputs | 8 |
| India Nifty YTD | `nepse-macro-regime-detector` inputs | 7 |

Total composite score 0-100 → bias label:
- 80-100: **STRONG_BIAS_LONG** — Druckenmiller-style concentrated long
- 60-79: **BIAS_LONG** — overweight, but watch tops
- 40-59: **NEUTRAL** — normal sizing
- 20-39: **BIAS_DEFENSIVE** — reduce exposure, defensive sectors
- 0-19: **STRONG_DEFENSIVE** — cash / minimum exposure (NEPSE long-only constraint)

## Recommended Portfolio Tilt

| Bias | Exposure | Concentration | Sector tilt |
|---|---|---|---|
| STRONG_BIAS_LONG | 90-100% | 5-8 names | top sectors per `nepse-sector-analyst` |
| BIAS_LONG | 70-85% | 8-12 names | favor leaders; some defensive ballast |
| NEUTRAL | 50-70% | 10-15 names | diversified across BFI / hydropower / insurance |
| BIAS_DEFENSIVE | 30-50% | 5-8 names | insurance + top-quality dividend BFIs only |
| STRONG_DEFENSIVE | 0-25% | 0-3 names | cash and one or two defensive positions |

## When to Use

- User asks for a top-down NEPSE thesis
- Quarterly review of overall portfolio tilt
- After a regime shift (NRB rate change, political event, major index move)
- Before a large position change

## Workflow

### Step 1: Run all upstream skills

```bash
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-market-top-detector/scripts/detect_top.py --reports-dir reports/ --output-dir reports/
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

### Step 2: Synthesize

```bash
python3 skills/nepse-stanley-druckenmiller-investment/scripts/synthesize_thesis.py \
  --reports-dir reports/ --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_druckenmiller_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_druckenmiller_<YYYY-MM-DD>.md` — bias, tilt, rationale

## Limitations

- Heuristic composite weights — not a replacement for fundamental judgment
- Requires upstream JSONs to be fresh; the skill flags stale inputs (>3 days old)
- Druckenmiller traded macro futures (long + short, leveraged); NEPSE allows only long-only un-margined positions (margin trading exists for 123 names since April 2026 but not derivatives). The "tilt" is exposure-based, not Druckenmiller-style leverage
- The recommended portfolio tilt is guidance, not financial advice. Sizing decisions are user judgment
