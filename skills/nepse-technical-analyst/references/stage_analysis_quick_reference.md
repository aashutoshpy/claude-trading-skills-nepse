# Stage Analysis Quick Reference (Stan Weinstein)

Compact framework for reading trend stage from a chart. Apply this
first; everything else (VCP, breakouts, support/resistance) is more
useful once stage is established.

## The Four Stages

### Stage 1 — Basing / Accumulation
- Price moves sideways for weeks-to-months
- 30-week (~150-day) MA is flat
- Volume is dull, occasional dry-up
- **Action:** watch for breakout above the basing range on volume

### Stage 2 — Advancing
- Price breaks above the basing range
- 30-week MA turns up
- Price stays above the 30-week MA
- Volume expands on advances, dries up on pullbacks
- **Action:** buy breakouts, buy pullbacks to the 30-week MA. This
  is the only stage where you should hold long-only positions.

### Stage 3 — Top / Distribution
- 30-week MA flattens after a sustained advance
- Price churns near the highs with widening ranges
- Volume divergence: lower highs in price + persistent volume
- **Action:** trim, tighten stops. Do NOT add.

### Stage 4 — Declining
- Price breaks below the 30-week MA
- 30-week MA turns down
- Price stays below the 30-week MA
- Volume expands on declines, dries up on bounces
- **Action:** do nothing. Wait for Stage 1 to form. (NEPSE doesn't
  allow short selling, so Stage 4 is just "stay away.")

## NEPSE-specific Stage Calibration

Stan Weinstein wrote for US markets with 200-day SMAs. NEPSE traders
typically use:

| Indicator | US default | NEPSE default | Why |
|---|---|---|---|
| Trend MA | 30-week (150-day) | **200-day** | Aligns with how NEPSE platforms (Sharesansar, ChukulPro) display their main MA |
| Confirmation MA | 10-week (50-day) | **50-day** | Same |
| Volume regime | shares/day | **NPR turnover/day** | NEPSE share prices vary widely (5 NPR penny stocks to 5000 NPR BFI names); turnover is more comparable |

## Decision Heuristic

| Stage | Confidence | Position bias |
|---|---|---|
| Stage 2, price > 50-SMA > 200-SMA, 200-SMA rising | High | Long-bias |
| Stage 1, price compressed near 200-SMA, low volume | Medium | Watch list |
| Stage 3, price below 50-SMA but above 200-SMA | Low | Exit / no new positions |
| Stage 4, price < 50-SMA < 200-SMA | High | No position (NEPSE long-only) |

## Reading from a chart screenshot

1. Locate the 50-SMA and 200-SMA (most NEPSE charts show them by default)
2. Check the slope of the 200-SMA over the last ~6 weeks
3. Check the price/SMA50/SMA200 stack
4. Map to one of the four stages above
5. If chart shows volume bars, check volume regime in the most recent base/decline

## Reference

- Stan Weinstein, *Secrets for Profiting in Bull and Bear Markets* (1988), ch. 1-3
- Mark Minervini's adaptation in *Trade Like a Stock Market Wizard* (2013), ch. 7
