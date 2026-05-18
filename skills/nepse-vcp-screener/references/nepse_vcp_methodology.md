# NEPSE VCP Methodology

Mark Minervini's Volatility Contraction Pattern adapted to the Nepal
Stock Exchange. This document explains the changes from the US VCP
screener and why each was necessary.

## What VCP is

A VCP forms when a stock in a Stage 2 uptrend pulls back and consolidates
in successively tighter ranges. The pattern signals that selling
pressure is dwindling and a breakout above the most recent swing high
("the pivot") is statistically likely.

Minervini's core rules (universal):

1. **Stage 2 trend**: price > 50-day SMA > 200-day SMA; 200-SMA must be
   rising.
2. **At least 2 contractions**: each leg measures from a swing high to
   the next swing low.
3. **Narrowing contractions**: each contraction must be tighter than
   the previous one (3% → 6% → 12% is INVALID; 12% → 6% → 3% is the
   canonical pattern).
4. **Tight final contraction**: the most recent contraction should be
   single-digit % — Minervini cites 2-5% on US large-caps.
5. **Volume drying up in the base**: trade should narrow alongside
   price.

## What changes for NEPSE

| Aspect | US calibration | NEPSE calibration | Why |
|---|---|---|---|
| Daily price band | 10% | **15%** (since 2026-04-17) | NEPSE raised the limit; intraday ranges are mechanically wider |
| Typical EOD volume | 100k+ shares | 5k-50k shares for most NEPSE names | Universe size; sparse turnover outside the top 30 BFI/hydropower names |
| Base duration | 25-60 days | 15-40 days | NEPSE bases form faster because the universe rotates quickly |
| SMA-200 rising window | 30 days | 20 days | Shorter histories common on newly-listed hydropower/microfinance names |
| Hydropower over-rep | n/a | watch for it | 97 of 284 listings are hydropower; a sector-blind run will surface mostly hydro candidates. Use `nepse-sector-analyst` to confirm sector strength before sizing |

### Why the 15% band changes pattern thresholds

In a 10%-band market a single-day move that reaches limit is, by
definition, the largest move possible — so a "5% contraction" is half
of what's mechanically achievable. In a 15%-band market the same 5%
contraction is one-third of what's achievable — proportionally tighter
in absolute % but **less rare**. We tighten the final-contraction
threshold from 10% → 6% to compensate.

### Why volume thresholds drop

NEPSE total daily turnover is ~NPR 1-5 billion across all 284 names.
Outside the top-30 by liquidity (commercial banks, top hydropower,
top microfinance) the typical name trades 1k-20k shares per session.
The default `avg_volume_min` is 5,000 shares (vs. tens of thousands
for the US screener) to keep small-but-liquid names in scope.

## Interpreting candidates

| `composite_score` | Read as |
|---|---|
| 80-100 | Textbook setup; watch for breakout volume |
| 70-79 | Strong; size at pivot |
| 60-69 | Developing; watchlist |
| < 60 | Too loose / too far from pivot — monitor only |

`valid_vcp=true` is necessary but not sufficient. Always cross-check
with `nepse-technical-analyst` on a chart screenshot before acting.

## Edge cases / known limitations

- **Newly-listed names**: < 220 trading days of history → automatically
  rejected because Stage 2 needs 200-day SMA.
- **Sparse trading**: names with zero-volume sessions get
  inconsistent swing detection. Consider raising `--avg-volume-min`
  for production screens.
- **Bonus shares / right shares**: NEPSE adjusts EOD prices for
  bonuses and rights, but the EOD endpoint occasionally lags on the
  adjustment day. Expect spurious "huge contraction" candidates the
  day after corporate actions — filter manually.
- **Circuit-hit days**: a name that hits the +15% upper circuit
  records an artificial swing high. The detector treats it as a
  pivot; verify whether the move was a true breakout or a corporate-
  action mark.

## References

- Mark Minervini, *Trade Like a Stock Market Wizard* (2013), Chapter 7
- NEPSE rule changelog: `common/nepse/references/nepse_market_rules_changelog.md`
- US sibling skill: `skills/vcp-screener/`
