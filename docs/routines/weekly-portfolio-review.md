# Weekly Portfolio Review — Claude Desktop Routine

End-of-week NEPSE portfolio review: P&L, sector concentration, margin warnings, rebalance decisions.

## Schedule

| Field | Value |
|---|---|
| Type | Local Scheduled Task |
| Day | Saturday |
| Time | 10:00 NPT (market closed; relaxed pace) |
| Working directory | Your local clone of this repo |

## Prerequisites

- `data/meroshare_export.csv` exists (raw MeroShare export — see [GETTING_STARTED.md §3.1](../../GETTING_STARTED.md#31-export-your-portfolio-from-meroshare))
- `data/cost_basis.csv` exists (one row per position; copy from `data/cost_basis.csv.example`)
- OHLCV cache is fresh (`scripts/fetch_nepse_snapshot.py` ran during the week)

The wrapper auto-runs `scripts/normalize_meroshare_csv.py` to join the two inputs and produce `data/nepse_portfolio.csv` in the tracker schema. If MeroShare CSV is missing the wrapper exits 2 with a clear message. If cost basis is partial (some symbols missing), the wrapper continues — the tracker just skips P&L for the affected rows.

## What it does

1. Refreshes today's OHLCV (so mark-to-market is current)
2. Runs `nepse-portfolio-tracker` against `data/nepse_portfolio.csv`
3. Reads the position-by-position P&L + sector concentration + margin-distance output
4. Writes a one-page weekly review to `reports/weekly_review_YYYY-MM-DD.md`

## Prompt

```
=========================== BEGIN PROMPT ===========================

You are running the NEPSE Weekly Portfolio Review routine.

STEP 1 — Run the wrapper.

Execute: bash scripts/run_weekly_portfolio_review.sh

If exit code is 2 (portfolio CSV missing), tell the user how to populate
it (export from MeroShare → My Portfolio → save as data/nepse_portfolio.csv)
and stop. If exit code is 1 (other error), report the error and stop.

STEP 2 — Read the latest portfolio report.

Read reports/nepse_portfolio_YYYY-MM-DD.md (today's date or the most
recent if generation skipped today).

STEP 3 — Write the weekly review.

Create reports/weekly_review_YYYY-MM-DD.md with this structure:

# NEPSE Weekly Portfolio Review — YYYY-MM-DD

## P&L snapshot
- Total position count and total NPR invested
- Weekly P&L (% and NPR) if calculable from prior week's report
- Winners (top 3 by % gain) and losers (top 3 by % loss)

## Sector concentration
- % allocated to each of the 13 NEPSE sectors
- Flag any sector >30% of portfolio as "over-concentrated"
- One sentence on whether the concentration matches your regime call
  (e.g., "30% BANKING is fine in a defensive regime, risky in growth")

## Margin posture
- Total margin used (NPR + % of portfolio)
- For each margin position, current distance to maintenance margin call
- Flag any margin position within 10% of call distance as "TIGHTEN OR
  REDUCE THIS WEEK"

## Stop-violations and target hits
For each open position:
  - Has price closed below the original stop? → "EXIT (stop hit)"
  - Has price tagged 1R / 2R / 3R targets? → "Consider trimming N shares"
  - Has the thesis-review date passed? → "Mark reviewed or close"

## This week's action items
A numbered list, max 5 items, in priority order. Each item:
  "<action verb> <symbol> at TMS: <specific instruction>"
For example:
  "Trim 50 shares of NABIL at 540+ (1R target hit)"
  "Reduce UPPER margin position to 50% — call distance at 12%"

If there are no action items, write: "No actions this week. Hold and
monitor."

STEP 4 — Print the review path.

Print ONLY the absolute path to the review file as your final line.

=========================== END PROMPT ===========================
```

## Run manually

```bash
cd /path/to/claude-trading-skills-nepse
bash scripts/run_weekly_portfolio_review.sh
```

## Notes

- The routine **never tells you to buy more** — buy decisions come from the daily morning briefing. The weekly review is about managing what you already hold.
- Margin warnings are conservative — if call distance is under 10%, the review flags it. You decide whether to trim or hold.
- The review file uses absolute dates so re-running on different days produces multiple snapshots, not overwrites. Useful for week-over-week trend tracking.
