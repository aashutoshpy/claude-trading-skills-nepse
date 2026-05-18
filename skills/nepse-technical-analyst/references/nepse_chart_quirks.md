# NEPSE Chart Quirks — What to Watch For

This document catalogs phenomena that show up on NEPSE charts and have
no clean US equivalent. Mis-reading them as conventional patterns
produces bad trades.

## 1. Circuit-hit bars (±15% daily band, post-April 2026)

A bar that hits the upper or lower circuit is a **mechanical mark**,
not a normal price action signal.

- **Looks like:** an outsized green/red candle, often a doji-like body
  at the limit price (further buying / selling is queued, no fills).
- **What it means:** demand or supply exceeded the band; the day's
  print is a clearing-price floor (upper circuit) or ceiling (lower
  circuit), not equilibrium.
- **How to read:**
  - **Upper circuit on day 1 of a base breakout** = strong breakout
    confirmation. Volume is misleading (often capped). Wait for next
    session to size.
  - **Upper circuit during a runaway move** (third or fourth
    consecutive circuit) = chase-risk. The next session frequently
    gaps and reverses.
  - **Lower circuit on a break of base support** = institutional
    distribution. Do NOT bottom-fish; the next session typically
    extends.
- **Detection on a chart:** any green candle that closes near the
  high with a body ≥14.5% of prior close is almost certainly a
  circuit hit.

## 2. Bonus-share and right-share gaps

NEPSE companies (especially BFIs and microfinance) frequently issue
bonus shares and rights. On the ex-date the price adjusts down.

- **Looks like:** a clean gap-down (sometimes 10-40%) on average or
  light volume, often with no surrounding bearish action.
- **What it means:** a corporate action, NOT selling pressure. The
  EOD endpoint usually back-adjusts historical bars, but the
  adjustment can lag by a session.
- **How to read:** treat the gap as zero-information. Use the
  POST-adjustment price for everything (SMAs, swing analysis,
  contraction depth).
- **Verification:** check the company's announcements section on
  sharesansar.com or merolagani.com for the ex-date.

## 3. Multi-day no-trade gaps

Outside the top ~50 names by liquidity, many NEPSE stocks have
sessions with zero trades.

- **Looks like:** flat bars at the prior close, or missing bars
  entirely if the chart skips no-trade days.
- **What it means:** no price discovery happened. Patterns built
  around these bars (e.g., a "swing low" on a zero-volume day) are
  artifacts.
- **How to read:** require ≥50 traded sessions in the last 100 calendar
  days before trusting pattern analysis on a NEPSE name.

## 4. Saturday-Sunday weekend gaps

NEPSE moved to a Mon–Fri week in late 2025 (was Sun–Thu). On older
charts you may see Sunday bars; on charts since November 2025 you
should not.

- **Looks like:** a gap between Friday's close and Monday's open.
  This is the normal weekend gap (same as US markets); do not
  over-interpret.
- **Old charts (pre-Nov 2025):** the gap would be between Thursday
  close and Sunday open instead. If a chart shows Friday bars in
  early 2025 and Monday bars in late 2025, that's the transition.

## 5. Pre-opening price moves (10:30–10:55)

NEPSE has a pre-opening auction window with a 3% price band (raised
from 2% in April 2026).

- **Looks like:** the first daily bar's open may differ from the
  prior close by up to 3% before any continuous trading.
- **How to read:** treat the open price as a "post-auction" mark,
  not the first traded price.

## 6. AMO (After-Market Order) overhang

Since April 2026, orders can be placed between 18:00 NPT and 06:00
NPT for the next session.

- **Looks like:** opens that gap up or down sharply on news or
  global cues, with the gap holding through the morning.
- **How to read:** AMO queues can produce strong directional opens
  that fade by mid-session. Wait at least 30 minutes after the 11:00
  open before judging the day's trend.

## 7. NEPSE index pump/dump days

The NEPSE composite index is heavily weighted toward commercial banks
(highest market cap) and hydropower (largest by company count).

- **Looks like:** the index moves +/- 2-3% but the move is driven
  by a single sector while everything else is flat.
- **How to read:** always look at sector indices (banking, hydropower,
  microfinance) alongside the composite. Use `nepse-sector-analyst`
  for sector-level reads.

## 8. Margin trading (live since April 2026)

The 123 margin-eligible names can now experience margin-call cascades.

- **Looks like:** a 1-2 day sharp decline followed by a sharper
  3rd-day capitulation, then a snap-back.
- **How to read:** the capitulation candle is often a buyable
  selling-climax. But this pattern has only existed for ~1 month of
  NEPSE history as of May 2026 — apply judgment, not historical
  pattern confidence.
