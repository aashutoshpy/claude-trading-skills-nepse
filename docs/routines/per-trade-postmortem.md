# Per-Trade Postmortem — Saved Prompt

Fires **on-demand** every time you close a NEPSE position. Not on a schedule — event-driven.

## How to use

1. Place the exit order at your broker. Wait for fill.
2. Open Claude Desktop, start a new chat in your repo's project.
3. Paste the prompt below, filling in the angle-bracketed fields.
4. Claude runs the close + postmortem + tax calculation chain and writes a journal entry to `state/journal/`.

Total time: under 2 minutes including data entry.

## Why this is a saved prompt, not a scheduled routine

It's inherently event-driven — you only need it when you've actually closed something. A scheduled routine would either fire when there's nothing to do (wasted run from your daily budget) or fail because you forgot to close a thesis.

The saved-prompt approach: one-click insertion, one-line edit, run.

## Prompt template

```
=========================== BEGIN PROMPT ===========================

I just closed a NEPSE position. Please run the close + postmortem +
tax-estimate chain.

Inputs:
  - Symbol: <NABIL>
  - Thesis ID: <th_nabil_vcp_20260301_a3f1>   (find via `thesis_store.py list`)
  - Exit price: <540.50>
  - Exit date: <2026-05-18>
  - Exit reason: <target_hit | stop_hit | time_stop | manual>
  - Shares closed (full position): <yes | no — partial of N shares>
  - Entry price (for tax estimate): <425.00>
  - Entry date (for tax estimate): <2025-12-15>

Run, in order:

STEP 1 — Close (or trim) the thesis.

If full close:
  python3 skills/trader-memory-core/scripts/thesis_store.py \
    --state-dir state/theses/ close <THESIS_ID> \
    --exit-reason <reason> --actual-price <exit_price> \
    --actual-date <exit_date>

If partial trim:
  python3 skills/trader-memory-core/scripts/thesis_store.py \
    --state-dir state/theses/ trim <THESIS_ID> \
    --shares-sold <N> --price <exit_price> --date <exit_date>

STEP 2 — Generate the postmortem.

python3 skills/trader-memory-core/scripts/thesis_review.py \
  --state-dir state/theses/ postmortem <THESIS_ID>

This writes state/journal/pm_<THESIS_ID>.md.

STEP 3 — Estimate the tax.

Compute holding days = exit_date - entry_date.

python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --symbol <SYMBOL> \
  --entry-price <entry_price> --exit-price <exit_price> \
  --shares <total_shares_closed> --holding-days <N>

Report:
  - Long-term (>365 days) or short-term?
  - Tax amount in NPR
  - Net gain after tax
  - If short-term: how many more days you'd have needed to qualify for LT

STEP 4 — Append your reflection.

At the end of state/journal/pm_<THESIS_ID>.md (which Step 2 created),
append a section "## Honest reflection" with:
  - What worked in this trade
  - What didn't (entry too high? stop too tight? thesis was wrong?)
  - One specific thing to do differently next time

Be ruthless and brief. This is for your future self — sugarcoating
defeats the purpose.

STEP 5 — Print outputs.

Print the path to:
  - The updated thesis YAML in state/theses/
  - The postmortem markdown in state/journal/

=========================== END PROMPT ===========================
```

## Run manually (without Claude)

You can do the same chain by hand:

```bash
# Close
python3 skills/trader-memory-core/scripts/thesis_store.py \
  --state-dir state/theses/ close $TID \
  --exit-reason target_hit --actual-price 540.50 --actual-date 2026-05-18

# Postmortem template
python3 skills/trader-memory-core/scripts/thesis_review.py \
  --state-dir state/theses/ postmortem $TID

# Tax
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --symbol NABIL --entry-price 425.00 --exit-price 540.50 \
  --shares 235 --holding-days 154
```

Then open `state/journal/pm_<thesis_id>.md` in your editor and write the "Honest reflection" section yourself.

## Why ruthless honesty matters

The single most valuable file in this system over time is your journal of postmortems. Pattern-recognition across 50 trades is what separates a profitable trader from a break-even one. If you sugarcoat the "what went wrong" section, you'll repeat the mistake. Make it specific:

- Bad: "Stop was too tight."
- Good: "I used a 5% stop in a name with 8% ATR. Got stopped on day 2 of a normal pullback. Next time, use ATR-multiple stops for high-volatility names, not flat-percent stops."

The second version is something you can actually act on next trade.
