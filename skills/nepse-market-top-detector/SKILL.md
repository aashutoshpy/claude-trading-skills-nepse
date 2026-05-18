---
name: nepse-market-top-detector
description: Aggregate multiple NEPSE-specific top signals (BFI overconcentration, microfinance euphoria, distribution-day count, breadth divergence, IPO/listing frenzy proxy) into a composite top-risk score and warning level. Use when the user asks "is NEPSE topping?", wants to size down before a correction, or runs a periodic top-risk check after an extended uptrend.
---

# NEPSE Market Top Detector

Aggregates outputs from other NEPSE skills + NEPSE-specific structural signals into a single top-risk score (0-100) and warning level (LOW / ELEVATED / HIGH / EXTREME).

## What Signals it Aggregates

| Signal | Source skill | Weight |
|---|---|---:|
| Distribution days | `nepse-ibd-distribution-day-monitor` JSON | 30 |
| Breadth divergence | `nepse-uptrend-analyzer` JSON | 25 |
| Microfinance over-leadership | `nepse-sector-analyst` JSON | 20 |
| BFI overconcentration | composite — top sector accounts for ≥50% of breadth advances | 15 |
| Index ATH proximity | `nepse-uptrend-analyzer` history vs. current ratio | 10 |

(Each signal scored 0-100; final score = weighted average.)

## NEPSE-specific top patterns

| Pattern | Interpretation |
|---|---|
| Microfinance #1 in sector ranking for 2+ weeks | Late-cycle speculation — high top risk |
| Distribution days ≥5 + uptrend ratio falling | Classic O'Neil top warning |
| Hydropower + microfinance both leading + new highs | Often precedes a 10-20% NEPSE correction |
| Banks #1 with ratio in `STRONG_UPTREND` | Healthy bull — low top risk |
| New listings count up sharply (IPO frenzy proxy) | Late-cycle pattern, structural |

## When to Use

- User asks "is NEPSE topping?" or "how much top risk?"
- Periodic check after 3+ months of uptrend
- Before increasing exposure on individual-name screens
- Daily during `STRONG_UPTREND` regimes

## Workflow

### Step 1: Run upstream skills first

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
```

### Step 2: Aggregate

```bash
python3 skills/nepse-market-top-detector/scripts/detect_top.py \
  --reports-dir reports/ --output-dir reports/

# Or specify each input explicitly
python3 skills/nepse-market-top-detector/scripts/detect_top.py \
  --distribution-json reports/nepse_distribution_days_2026-05-17.json \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --sectors-json reports/nepse_sectors_2026-05-17.json \
  --breadth-json reports/nepse_breadth_2026-05-17.json \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_top_risk_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_top_risk_<YYYY-MM-DD>.md` — score, level, contributing signals

## Severity Levels

| Composite score | Level | Action |
|---|---|---|
| 0-30 | LOW | Continue normal sizing |
| 31-55 | ELEVATED | Tighten stops; pause new larger positions |
| 56-75 | HIGH | Reduce exposure; only top-quality setups |
| 76-100 | EXTREME | Raise cash; exit weakest holdings |

## Limitations

- Composite scoring is heuristic, not back-tested across a full NEPSE cycle.
- Weights are NEPSE conventions and should be recalibrated as more post-reform data accumulates.
- Top calls are by nature noisy and prone to false positives — use as ONE input among several.
- Requires the upstream skills to have run; missing inputs degrade the score quality.
