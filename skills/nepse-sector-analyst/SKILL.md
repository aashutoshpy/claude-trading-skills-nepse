---
name: nepse-sector-analyst
description: Rank NEPSE's 13 sector indices by recent performance, identify sector rotation, and flag leading/lagging sectors. Computes 1-week / 1-month / 3-month / YTD returns per sector index and ranks them. Accepts a chart screenshot for visual sector-rotation confirmation. Use when the user asks "what NEPSE sectors are leading", wants to find where money is rotating, or needs sector context before drilling into individual names.
---

# NEPSE Sector Analyst

Ranks NEPSE's 13 sector sub-indices (Banking, Development Bank, Finance, Microfinance, Hydropower, Life Insurance, Non-Life Insurance, Hotels & Tourism, Manufacturing, Trading, Mutual Funds, Investment, Others) by trailing returns and flags rotation patterns.

## When to Use

- User asks "which NEPSE sectors are leading?"
- User wants to know whether banks, hydropower, or microfinance is the leader
- User uploads a sector-comparison chart screenshot for visual rotation analysis
- Before drilling into individual names with `nepse-vcp-screener` or `nepse-technical-analyst`

## What it Computes

Per sector index:
- 1-week return (5 trading days)
- 1-month return (~22 trading days)
- 3-month return (~66 trading days)
- YTD return (since Jan 1 of current calendar year)
- Trend stage (Stage 1/2/3/4 per the sector index's own SMAs)
- Rank within the 13 sectors for each timeframe

## NEPSE Sector Universe (verified May 2026)

| Sector ID | Display Name | ~Count | Notes |
|---|---|---:|---|
| BANKING | Commercial Banks | 18 | Highest market cap; dominates composite |
| DEVELOPMENT_BANK | Development Banks | ~17 | More volatile than commercial banks |
| FINANCE | Finance Companies | ~15 | Often follows banks with a lag |
| MICROFINANCE | Microfinance | ~50 | Highest beta on NEPSE; volatile |
| HYDROPOWER | Hydropower | 97 | Largest by count; monsoon-driven cycles |
| LIFE_INSURANCE | Life Insurance | ~15 | Independent of banks; rates-sensitive |
| NON_LIFE_INSURANCE | Non-Life Insurance | ~20 | Independent of banks |
| HOTELS | Hotels & Tourism | 8 | Thin; tourism-cycle proxy |
| MANUFACTURING | Manufacturing & Processing | 26 | Mixed; underlying businesses vary widely |
| TRADING | Trading | 4 | Tiny; rarely actionable |
| MUTUAL_FUNDS | Mutual Funds | ~30 | Closed-end NAV-tracking |
| INVESTMENT | Investment | 7 | Holding companies |
| OTHERS | Others | 10 | Catch-all |

## Workflow

### Step 1: Run

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --output-dir reports/

# Custom lookback windows (defaults: 5d / 22d / 66d / YTD)
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --windows 10,30,90 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_sectors_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_sectors_<YYYY-MM-DD>.md` with ranking tables

### Step 3: Combine

- Use the top-3 sectors as a filter for `nepse-vcp-screener` (focus screen on leaders)
- Cross-check with `nepse-market-breadth-analyzer` sector breakdown for confirmation
- Optional: user uploads a sector chart screenshot — read the visual rotation pattern alongside the numerical ranks

## Rotation Patterns to Recognize

| Pattern | What it usually means |
|---|---|
| Banks leading, hydropower lagging | Risk-off environment; interest-rate optimism |
| Hydropower leading, banks lagging | Risk-on; monsoon / electricity export thesis |
| Microfinance + banks both up | Broad financial-sector strength |
| Microfinance up alone | Speculative / late-cycle (often near tops) |
| Insurance leading | Defensive rotation or rate-cut anticipation |
| All sectors in red except hydropower | Late-cycle defensive concentration |

## Resources

- [references/nepse_sector_dynamics.md](references/nepse_sector_dynamics.md) — sector-by-sector drivers and historical regimes

## Limitations

- Requires sector-index OHLCV. The scraper backend's `_INDEX_IDS` map is unverified against the live `nepalstock.com.np` — first run may need ID tuning.
- Sector indices reflect the COMPOSITION of the sector (market-cap weighted in most cases). A single mega-cap can swing a sector index even if the rest of the sector is flat. Cross-check with per-name breadth.
