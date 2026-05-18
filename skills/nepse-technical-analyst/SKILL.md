---
name: nepse-technical-analyst
description: Analyze NEPSE (Nepal Stock Exchange) stock charts from screenshots. Read price action, identify trend stage (Wyckoff / Stage Analysis), find support/resistance, evaluate breakout/breakdown setups, and call out NEPSE-specific microstructure quirks (15% daily band, circuit-hit days, low-liquidity gaps, T+2 settlement). Use when the user uploads a NEPSE chart screenshot and asks for technical analysis. NOT for US stocks — use technical-analyst instead.
---

# NEPSE Technical Analyst

Chart-image-driven technical analysis specifically tuned for NEPSE. The methodology is universal (Stage Analysis, Wyckoff, swing-trading frameworks), but NEPSE microstructure makes pattern interpretation different in important ways.

## When to Use

- User uploads a NEPSE stock chart (weekly, daily, or intraday) and asks for analysis
- User asks for NEPSE-specific pattern interpretation (e.g., "is this a Stage 2 breakout?")
- User wants to confirm a screener candidate from `nepse-vcp-screener` or `nepse-sector-analyst`

## What to do when invoked

1. **Identify the ticker and timeframe** from the chart. Note if multiple timeframes are present (weekly + daily is best).
2. **Stage Analysis** — call out:
   - Stage 1 (accumulation, flat base, no trend)
   - Stage 2 (uptrend, price > 50-SMA > 200-SMA, 200-SMA rising)
   - Stage 3 (distribution, topping action)
   - Stage 4 (downtrend, price < 50-SMA < 200-SMA, 200-SMA falling)
3. **Identify recent swings**: most recent swing high, swing low, current pullback depth.
4. **Find pivots / breakout points** using prior swing highs and base resistance.
5. **Note volume profile** — is volume drying up in the base (bullish for breakout) or expanding into the decline (bearish)?
6. **Call out NEPSE-specific quirks** (see [references/nepse_chart_quirks.md](references/nepse_chart_quirks.md)):
   - Circuit-hit bars (a +15% / -15% bar is a circuit, not a normal candle)
   - Bonus/right share gap-downs (corporate actions, not selling)
   - Multi-day no-trade gaps on illiquid names (interpret with caution)
   - Saturday-Sunday weekend gaps (NEPSE moved to Mon-Fri in late 2025)
7. **Produce a scenario plan**: bull, bear, and neutral cases with trigger prices.
8. **Save a report** to `reports/nepse_tech_<symbol>_<YYYY-MM-DD>.md` using the template structure below.

## Report Structure

```markdown
# NEPSE Technical Analysis — <SYMBOL>
**As of:** YYYY-MM-DD    **Timeframe:** weekly + daily

## Stage Analysis
[Stage 1/2/3/4 + justification]

## Trend & Moving Averages
- Price: NPR <X>
- 50-SMA: <X>    (price <above/below>)
- 200-SMA: <X>   (price <above/below>, 200-SMA <rising/falling/flat>)

## Key Levels
- Recent swing high (pivot): NPR <X>
- Recent swing low: NPR <X>
- Major support: NPR <X>
- Major resistance: NPR <X>

## Pattern Notes
[VCP, cup-and-handle, flag, head-and-shoulders, etc.]
[Note circuit hits, corporate-action gaps explicitly]

## Volume Profile
[drying up / expanding / inconclusive]

## Scenarios
- **Bull**: trigger above NPR <X>, target NPR <Y>, invalidation NPR <Z>
- **Bear**: trigger below NPR <X>, target NPR <Y>, invalidation NPR <Z>
- **Neutral**: range NPR <X>–<Y>, wait for resolution

## Risk Notes
- Margin eligible: <yes/no>  (cross-reference via `nepse-margin-eligibility` if available)
- Liquidity: <high/medium/low>  (note avg daily volume from chart)
- Next quarterly result expected: ~<date>  (Nepali FY 2082/83 → Gregorian)
```

## Resources

- [references/nepse_chart_quirks.md](references/nepse_chart_quirks.md) — what NEPSE-specific phenomena look like on a chart and how to interpret them
- [references/stage_analysis_quick_reference.md](references/stage_analysis_quick_reference.md) — Stan Weinstein's 4-stage framework, condensed

## Combining

- After `nepse-vcp-screener` → run this on the top 3-5 candidates for visual confirmation
- After `nepse-sector-analyst` → use this on the lead names in a leading sector
- Before `nepse-breakout-trade-planner` → produce the scenario plan that feeds the trade plan

## Limitations

- Chart-image only — the skill does not fetch data. The user must supply a screenshot.
- Stage Analysis is descriptive, not predictive. Always check `nepse-macro-regime-detector` for market-wide regime before sizing on individual-stock setups.
