---
name: nepse-value-dividend-screener
description: Screen NEPSE stocks for high dividend yield + reasonable valuation. NEPSE is dividend-heavy (especially BFIs and microfinance), and cash-plus-bonus dividend yields of 8-15% are common. Use when the user asks for NEPSE dividend candidates, value-yield screening, or income-portfolio construction. Accepts a user-provided dividend CSV because NEPSE backends do not yet expose structured dividend feeds.
---

# NEPSE Value + Dividend Screener

Ranks NEPSE names by dividend yield and a simple value proxy (price-to-book where supplied, otherwise price-vs-200-SMA z-score as a fallback).

## Why this skill differs from `value-dividend-screener` (US sibling)

- **US version** uses FMP for fundamentals (yield, P/E, P/B, payout ratio, sector dividend leadership)
- **NEPSE version** has no equivalent — the `nepalstock` and community backends do not expose structured fundamentals. We work around this two ways:
  1. **User-provided dividend CSV** (preferred): user pastes a CSV from sharesansar or merolagani with columns `symbol,cash_div_pct,bonus_div_pct,reported_at`
  2. **OHLCV-derived yield estimate** (fallback): annualized return-to-trough on the last 3 corrections (a crude proxy for "dividend cushion")
- **NEPSE-specific:** bonus shares are a major component of NEPSE dividends (often larger than the cash portion). The screener combines both.

## When to Use

- User asks "what NEPSE stocks pay the highest dividend?"
- User wants to build an income portfolio of NEPSE BFIs / insurance
- User asks for value names trading below historical averages
- After `nepse-kanchi-dividend-sop` (Phase 4) identifies candidates and the user wants a market-wide cross-check

## Workflow

### Step 1: Prepare dividend CSV (recommended)

Manually export from sharesansar.com or merolagani.com:

```csv
symbol,cash_div_pct,bonus_div_pct,reported_at
NABIL,11.0,0.0,2025-12-15
NICA,16.0,4.0,2025-11-22
UPPER,0.0,12.0,2025-10-30
```

`cash_div_pct` and `bonus_div_pct` are percentages of paid-up share
capital (NEPSE convention). Both contribute to total yield.

### Step 2: Run

```bash
# With dividend CSV (preferred)
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --output-dir reports/

# Without CSV — OHLCV-derived only, less accurate
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --output-dir reports/

# Tune yield threshold
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --min-yield 8.0 --top 20 \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_dividends_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_dividends_<YYYY-MM-DD>.md` with sorted candidates

### Step 4: Combine

- Cross-reference with `nepse-margin-eligibility` (Phase 3) — most BFI dividend names are margin-eligible
- Run `nepse-technical-analyst` on the top 3-5 to confirm chart setup before sizing
- Feed JSON to `nepse-kanchi-dividend-sop` (Phase 4) for the full Kanchi workflow

## Output Schema

```yaml
symbol: NICA
sector: BANKING
price: 745.0
cash_div_pct: 16.0
bonus_div_pct: 4.0
total_div_pct: 20.0           # cash + bonus
yield_pct: 2.68               # total_div_pct * face_value (100) / price
distance_to_sma200_pct: -3.2   # negative = below SMA200 = value-y
margin_eligible: true
notes:
  - dividend_source: csv
  - last_reported: 2025-11-22
```

## NEPSE Dividend Math

NEPSE dividends are expressed as % of paid-up capital (face value =
NPR 100). Yield calculation:

```
total_div_pct = cash_div_pct + bonus_div_pct
yield_pct     = total_div_pct * 100 / current_price
```

Example: NICA pays 16% cash + 4% bonus on NPR 100 face value =
NPR 20 total per share. At market price NPR 745, yield = 20/745 ≈ 2.68%.

Note: bonus dividends are paid in shares, not cash — they dilute
existing holders proportionally but increase share count. Many NEPSE
investors treat them as equivalent to cash because the post-bonus
price reflects the dilution.

## Limitations

- **No structured dividend API** — user CSV is the only reliable source.
  The OHLCV-derived fallback is a poor proxy.
- **Reporting lag** — NEPSE companies announce dividends post-AGM
  (Bhadra-Mangsir). The CSV will be stale immediately after the AGM
  season.
- **Bonus-share back-adjustment** — the EOD price endpoint adjusts for
  bonuses but can lag a session. Cross-check current price against
  sharesansar.com if a dividend ex-date was recent.
