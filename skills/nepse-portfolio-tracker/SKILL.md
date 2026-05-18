---
name: nepse-portfolio-tracker
description: Track a NEPSE portfolio from MeroShare CSV/manual entries. Computes per-position P&L, total exposure, sector concentration, margin usage warnings (cross-referencing the 123-name margin-eligible list), and unrealized gain/loss. Use when the user wants a snapshot of their NEPSE holdings, needs sector-concentration risk analysis, or is reviewing margin exposure across the portfolio.
---

# NEPSE Portfolio Tracker

NEPSE has no brokerage API (TMS systems are web-only). This skill consumes a MeroShare CSV export (or a hand-maintained portfolio CSV) and produces a portfolio snapshot with NEPSE-specific risk reads.

## Why this replaces `portfolio-manager` (US)

- The US `portfolio-manager` uses Alpaca MCP for live holdings.
- NEPSE has no equivalent — the user exports a CSV from MeroShare (https://meroshare.cdsc.com.np) or maintains one manually.
- Margin is brand new (live April 2026) so positions flagged via the margin-eligible list get explicit warnings.

## When to Use

- User wants a snapshot of their NEPSE portfolio
- Periodic review (weekly / monthly) of sector concentration and unrealized P&L
- Margin-exposure audit after the April 2026 framework launch
- Before adding a new position — verify portfolio risk budget

## Portfolio CSV Format

```csv
symbol,shares,avg_cost,entry_date,is_margin
NABIL,100,1180.00,2026-02-15,false
UPPER,200,425.00,2026-03-22,true
NICA,50,725.00,2026-01-10,false
```

`is_margin` defaults to false. If you used broker margin for the position, set true so the skill computes margin-call distance.

## Workflow

### Step 1: Export from MeroShare and normalize

MeroShare's exported CSV uses verbose column names and **omits cost basis** (it doesn't know what you paid). Two-step process:

1. Log into meroshare.cdsc.com.np → My Portfolio → Export. Save as `data/meroshare_export.csv` (NOT `data/nepse_portfolio.csv` — that's the normalizer's output).
2. Copy `data/cost_basis.csv.example` to `data/cost_basis.csv` and add one row per holding with your `avg_cost`, `entry_date`, and `is_margin`.
3. Run the normalizer to join them into the tracker schema:

```bash
python3 scripts/normalize_meroshare_csv.py
# Output: data/nepse_portfolio.csv with symbol, shares, avg_cost, entry_date, is_margin
```

Exit code 0 = ready; 3 = partial (some symbols missing cost basis — the affected rows skip P&L); 1 = MeroShare CSV unreadable.

### Step 2: Run

```bash
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Include latest prices (default uses last close from NepseClient)
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Skip live-price lookup (offline mode — uses avg_cost as "current")
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --no-fetch-prices \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_portfolio_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_portfolio_<YYYY-MM-DD>.md` — per-position table + sector breakdown + risk warnings

## Output Highlights

- **Per-position:** symbol, shares, avg cost, current price, P&L NPR + %, sector, is_margin, margin-call distance (if margin)
- **Totals:** invested cost, current value, unrealized P&L %, position count
- **Sector breakdown:** % of portfolio value per sector, flag if any single sector >40%
- **Margin warnings:** every margin position flagged + each one's distance to its margin call

## Combining

- **Upstream:** `nepse-margin-eligibility` for margin-call math (used internally)
- **Downstream:** `exposure-coach` (existing market-agnostic skill) for sizing recommendations based on portfolio composition
- **Companion:** `trader-memory-core` to register each position as a thesis with rationale

## Limitations

- MeroShare's CSV format is undocumented and may change without notice. The skill accepts the canonical columns above; if MeroShare adds/renames columns, edit the CSV before passing it.
- "Current price" defaults to the most recent OHLCV close via `NepseClient`. For intraday accuracy, MeroShare is the source of truth.
- The skill does NOT execute orders — NEPSE has no broker API. All actions are manual.
