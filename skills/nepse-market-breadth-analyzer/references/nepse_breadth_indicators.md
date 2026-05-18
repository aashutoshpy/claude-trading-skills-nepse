# NEPSE Breadth Indicators — Interpretation Guide

## Why breadth matters more than the index

The NEPSE composite index is heavily weighted toward commercial banks
(by market cap) and hydropower (by company count). A 2% move in the
index can mask total opposite moves in the rest of the market — for
instance, banks ripping while microfinance and insurance are dumping.
Breadth catches this.

## The five indicators we compute

### 1. Advance/Decline ratio

Same-session count of names closing up vs. down.

| A/D | Read as |
|---|---|
| ≥ 1.5 | Broad strength — most names participating |
| 1.0–1.5 | Healthy advance |
| 0.7–1.0 | Mixed / churn |
| < 0.7 | Broad weakness |

Single-day reads are noisy. Watch the 5-day moving average for trend.

### 2. New 52-week highs / new 52-week lows

| Pattern | Read as |
|---|---|
| New highs rising, new lows < 10 | Healthy bull market |
| New highs falling while index rises | Narrowing leadership (Stage 3 warning) |
| New lows > 20 for 3+ days | Broad weakness developing |
| New lows > 40 | Bear market / capitulation in progress |

NEPSE caveat: a newly-listed hydropower or microfinance name can
record an artificial "new high" on its 5th trading day. The
breadth calculator's 150-day-min filter excludes these from the
denominator, but they can still bias the new-highs count. Verify
suspicious spikes against the listing date.

### 3. % above 50-day SMA

| Reading | Regime |
|---|---|
| ≥ 60% | Bull regime, broad participation |
| 40-60% | Transition / neutral |
| < 40% | Bear regime developing |
| < 25% | Oversold (mean-reversion candidates emerging) |

### 4. % above 200-day SMA

Slower-moving than 50-SMA but more reliable for regime classification.

| Reading | Regime |
|---|---|
| ≥ 55% | Confirmed bull regime |
| 40-55% | Mixed / weakening |
| < 40% | Bear regime |
| Crossover up through 50% on rising A/D | Often marks bull-regime start |

### 5. Sector participation

Per-sector A/D shows where the action is. NEPSE has 13 sectors but
breadth tends to cluster:
- **Banks + finance + microfinance** often move together (interest-rate sensitivity)
- **Hydropower** is its own theme (monsoon, electricity export to India)
- **Insurance** is occasionally a leader independent of banks
- **Hotels + manufacturing + trading** are usually too thin to read

## Regime classification (used by the script)

```
BULL_BROAD  : pct_above_200sma ≥ 55 AND pct_above_50sma ≥ 60
BULL_NARROW : pct_above_200sma ≥ 55 AND pct_above_50sma < 60
NEUTRAL     : in between
BEAR_NARROW : pct_above_200sma < 40 AND ad_ratio ≥ 0.7
BEAR_BROAD  : pct_above_200sma < 40 AND ad_ratio < 0.7
```

## Combining with other skills

- **Feed JSON to `nepse-macro-regime-detector`** for the full regime
  picture (macro + breadth + sector rotation).
- **Feed JSON to `exposure-coach`** (existing market-agnostic skill) for
  portfolio sizing recommendations.
- **Cross-check `nepse-sector-analyst`** outputs — strong sector calls
  should match positive per-sector A/D here.

## Historical caveat

NEPSE has only ~12 months of post-political-transition data as of
May 2026 (weekend changed Sun-Thu → Mon-Fri in late 2025, price band
raised 10% → 15% in April 2026). Regime thresholds calibrated on
pre-2025 NEPSE history may not transfer cleanly. Treat these
thresholds as starting points; recalibrate as more post-reform data
accumulates.
