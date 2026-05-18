# Quarterly Results Review — Claude Desktop Routine

Fires four times a year, ~6 weeks after each Nepali FY quarter-end, to review what reported and how the market reacted.

## Schedule

Set up **four separate routines**, one per quarter (Claude Desktop doesn't support "fire on these specific dates"; each is a one-shot scheduled task you re-create yearly).

| Quarter | Quarter-end (~) | Routine fires |
|---|---|---|
| Q1 | Ashwin / mid-Oct | **December 1** |
| Q2 | Poush / mid-Jan | **March 1** |
| Q3 | Chaitra / mid-Apr | **May 28** |
| Q4 | Ashadh / mid-Jul | **August 30** |

For each: Type = Local Scheduled Task; Time = 10:00 NPT (any time after market close on the prior day works); Days = the specific date for that year. Re-create the routines each year with updated dates if Nepal calendar shifts.

## What it does

1. Builds the NEPSE quarterly earnings calendar (based on Nepali FY quarter-ends from `config/registry.yaml`)
2. For each ticker in your watchlist (or the starter set), scores its post-results reaction using the 5-factor framework (gap, trend, volume, distance to MA200, distance to MA50)
3. Writes a quarterly review with the top reactions and what they imply for next quarter's positioning

## Prompt

```
=========================== BEGIN PROMPT ===========================

You are running the NEPSE Quarterly Results Review routine.

STEP 1 — Run the wrapper.

Execute: bash scripts/run_quarterly_review.sh

This may take 30–60 seconds because it scores each name individually.
Skipped names (no data, pre-filing) are normal — keep going.

STEP 2 — Read all generated reports.

Read:
  - reports/nepse_earnings_calendar_YYYY-MM-DD.md
  - reports/nepse_earnings_analysis_*.md (one per analyzed ticker)

STEP 3 — Write the quarterly review.

Create reports/quarterly_review_YYYY-MM-DD.md:

# NEPSE Quarterly Results Review — YYYY-MM-DD

## Quarter covered
Which Nepali FY quarter this review reflects (e.g., "FY 2082/83 Q3,
quarter-end ~April 13, statutory filing window closed ~May 13").

## Reactions summary
- Total names with recent prints: N
- High-quality reactions (5-factor score ≥80): list of symbols
- Failed reactions / gap-and-fade (score ≤30): list of symbols

For each high-quality reaction, write one sentence:
  "<SYMBOL>: <one-sentence summary of WHY the reaction was strong —
   was it a gap-up on volume? clean Stage 2 trend? margin-eligible
   liquidity?>"

## Sector heat map
Based on which sectors had the most high-quality reactions:
  - Hot sector(s): "X% of high-quality prints came from <sector>"
  - Cold sector(s): "<sector> had N prints, all low-quality"

## Implications for next quarter
A short list of biases for the next 90 days:
  - Sectors to overweight / underweight
  - Names to add to the watchlist for VCP screening
  - Names to remove (consistently poor reactions)

If your portfolio holds positions in failed-reaction names, flag them
for review in the weekly routine.

STEP 4 — Print the review path.

Print ONLY the absolute path to the review file as your final line.

=========================== END PROMPT ===========================
```

## Run manually

```bash
cd /path/to/claude-trading-skills-nepse
bash scripts/run_quarterly_review.sh
```

## Why four separate routines (not one)

Claude Desktop Routines schedule on a recurring pattern (daily / weekly / monthly), not on specific dates. The four quarter-ends don't fit a clean monthly pattern (every ~3 months but offset). Creating four one-shot scheduled tasks is cleaner than a monthly routine that always fires and then no-ops outside the four windows.

After each fire, the routine **disables itself** (Claude Desktop default for one-shot tasks). At the start of each new year, re-create the four for the upcoming year's quarter-ends.
