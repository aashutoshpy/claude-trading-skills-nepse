# Daily Morning Briefing — Claude Desktop Routine

Daily NEPSE regime check + screener + interpretive action plan, automated.

## Schedule

| Field | Value |
|---|---|
| Type | Local Scheduled Task |
| Days | Mon–Fri |
| Time | 09:00 NPT (= 03:15 UTC) — 90 min before market open at 11:00 NPT |
| Working directory | The path to your local clone of this repo |

## What it does

1. Pulls today's OHLCV snapshot (sharesansar) into `data/ohlcv/`
2. Runs market-breadth, uptrend-ratio, sector-rank, and VCP-screener
3. Reads the four reports and writes a human-readable action plan to `reports/morning_briefing_YYYY-MM-DD.md`

Output style: same as [GETTING_STARTED.md §2](../../GETTING_STARTED.md#2-your-daily-30-minutes-pre-market-before-1100-npt) — regime call, top candidates, one concrete action for today, one thing to watch tomorrow.

## Prompt

Copy everything between the markers and paste into the routine's prompt field.

```
=========================== BEGIN PROMPT ===========================

You are running the NEPSE Daily Morning Briefing routine.

STEP 1 — Run the data pipeline.

Execute: bash scripts/run_morning_briefing.sh

If the exit code is non-zero AND the failure is the fetcher step (1/5),
report the error and stop. Other step failures (breadth/uptrend/sector/vcp)
are non-fatal — proceed with whatever reports were produced.

STEP 2 — Read today's reports.

Read every file in reports/ that ends with `_$(date +%F).md`, specifically:
  - reports/nepse_breadth_YYYY-MM-DD.md   (regime + breadth indicators)
  - reports/nepse_uptrend_YYYY-MM-DD.md   (uptrend ratio + 20-day trajectory)
  - reports/nepse_sectors_YYYY-MM-DD.md   (sector ranking — may be missing)
  - reports/nepse_vcp_YYYY-MM-DD.md       (VCP candidate list)

STEP 3 — Write the briefing.

Create reports/morning_briefing_YYYY-MM-DD.md following this exact structure:

# NEPSE Morning Briefing — YYYY-MM-DD

## Regime call
One of: GO / NO-GO / SELECTIVE.
- GO: breadth is bullish AND uptrend ratio is climbing AND VCP screener
  has at least one valid candidate within ±2% of pivot with score ≥70.
- NO-GO: breadth is bearish OR uptrend ratio is below 30% OR no
  actionable VCP setups today.
- SELECTIVE: mixed signals — list the ambiguity explicitly.

State the regime in one sentence. Quote the two or three numbers that
drove the call (e.g., "% above 200-SMA: 30.1%", "uptrend ratio sliding
46.6% → 30.1% over 4 weeks").

## Candidates (if regime is GO or SELECTIVE)
For each VCP candidate with score ≥60 AND |distance_to_pivot| ≤5%:
- Symbol, sector, score, distance-to-pivot, valid_vcp status, margin-eligible
- One sentence: "Actionable if X" or "Pass because Y"

If regime is NO-GO, write: "No candidates evaluated today — regime says
stand down."

## Today's single action
One sentence — what to do. Most days this is "Do nothing. Don't open a
position." On a GO day it's "Consider a position in <SYMBOL> at <ENTRY>
with stop <STOP>; size with position-sizer." Never propose more than one
action.

## What to watch tomorrow
One or two signals that would change the call. E.g., "Breadth regime
flipping out of BEAR_BROAD" or "VCP score on NABIL climbing above 70".

## Step failures (if any)
If any wrapper step failed, list the step name and what it means for the
briefing's confidence.

STEP 4 — Print the briefing path.

Print ONLY the absolute path to the briefing file as your final line.
Don't print the briefing content again — the user will open the file.

=========================== END PROMPT ===========================
```

## Run manually

Equivalent to the routine, useful for testing or catch-up after a missed schedule:

```bash
cd /path/to/claude-trading-skills-nepse
bash scripts/run_morning_briefing.sh
# Then open a Claude Code session and ask it to interpret the reports
# (or just open the reports yourself — they're plain markdown).
```

## Why this granularity

The original PR1 split `nepse-market-regime-daily` and `nepse-swing-opportunity-daily` into two workflows. We merge them into one routine because:

- The swing decision is gated by the regime call — they're always evaluated together
- One routine fire (1 of your 15 daily budget) covers both
- Claude can decide *inside* the prompt whether to surface candidates based on the regime — cleaner than two routines passing state through `reports/`
