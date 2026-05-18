# NEPSE Routines for Claude Desktop

Automate the five canonical NEPSE workflows using **Claude Desktop Routines** (launched April 2026). Three scheduled routines + one on-demand saved prompt cover the entire trading cycle: daily regime + screener brief, weekly portfolio review, quarterly results review, and a per-trade postmortem.

## What Claude Routines are

Two flavors:

- **Local Scheduled Tasks** — fire a Claude Desktop session on your machine at the scheduled time. Requires the app to be open and the laptop awake.
- **Cloud Routines** — run on Anthropic infrastructure even when your laptop is off. Don't have access to your local files.

**For NEPSE, we use Local Tasks.** Every workflow reads `data/ohlcv/`, `data/nepse_portfolio.csv`, `state/theses/`, or `reports/` — files that live on your laptop. Cloud Routines can't see them.

## Prerequisites

| Item | Check |
|---|---|
| Paid Claude plan | Pro (5 runs/day), Max (15), Team or Enterprise (25). Free tier does not have Routines. |
| Claude Desktop app | Installed and signed in. |
| This repo cloned + bootstrapped | `python3 scripts/bootstrap_ohlcv_from_github.py` has been run at least once (see [GETTING_STARTED.md §1.6](../../GETTING_STARTED.md#16-build-up-your-ohlcv-history)). |
| Laptop awake at fire time | Local Tasks skip the run if the laptop is asleep. Plug in for overnight reliability. |

## The four routines

| Routine | File | Type | Fires | Daily-budget cost |
|---|---|---|---|---|
| Daily morning briefing | [daily-morning-briefing.md](daily-morning-briefing.md) | Scheduled | Mon–Fri 09:00 NPT (before market open) | 1 run/day |
| Weekly portfolio review | [weekly-portfolio-review.md](weekly-portfolio-review.md) | Scheduled | Saturday 10:00 NPT | 1 run/week |
| Quarterly results review | [quarterly-results-review.md](quarterly-results-review.md) | Scheduled × 4/year | ~Dec 1, Mar 1, May 28, Aug 30 | 1 run/quarter |
| Per-trade postmortem | [per-trade-postmortem.md](per-trade-postmortem.md) | Saved prompt (on-demand) | After every position close | 1 run per closed trade |

Total typical daily cost: **1 run** (morning brief). Weekly budget: **~6 runs**. Even on Pro (5/day) this fits with room to spare.

## How to install one

1. Open Claude Desktop. Sidebar → **Routines** → **New routine**.
2. Choose **Local**.
3. Open the corresponding file under [`docs/routines/`](.) (e.g. `daily-morning-briefing.md`).
4. Copy the **entire prompt block** under the "Prompt" heading and paste it into the routine's prompt field.
5. Set the **schedule** to the value listed in that file (e.g. `Mon–Fri 09:00` for the morning brief).
6. Set the **working directory** to your local clone of this repo (the `claude-trading-skills-nepse` folder).
7. Click **Save**.
8. Test it: click **Run now** on the saved routine. After ~30 seconds you should see a new `reports/<routine>_briefing_YYYY-MM-DD.md` file.

Repeat for each routine you want active.

## What each routine produces

| Routine | Output file |
|---|---|
| Daily morning briefing | `reports/morning_briefing_YYYY-MM-DD.md` |
| Weekly portfolio review | `reports/weekly_review_YYYY-MM-DD.md` |
| Quarterly results review | `reports/quarterly_review_YYYY-MM-DD.md` |
| Per-trade postmortem | `state/journal/pm_<thesis_id>.md` |

Every output is an **interpretation + action plan**, not a buy/sell signal. You still place every order manually at your broker. The routines are an "always-on second pair of eyes" that interprets the data the same way [GETTING_STARTED.md §2](../../GETTING_STARTED.md) walks through.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Routine fires but Claude says "no data" | OHLCV cache empty | Run `python3 scripts/bootstrap_ohlcv_from_github.py` once to seed `data/ohlcv/`. |
| "Step failed: sector ranking" inside briefing | Sector-index OHLCV not cached (CSV backend limitation) | Expected; non-fatal. The briefing proceeds without sector data. |
| Routine doesn't fire at scheduled time | Laptop was asleep or Claude Desktop wasn't open | Plug laptop in; keep Claude Desktop running. Or migrate the routine to Cloud Routines (limited — see below). |
| Hit "5 routines/day" cap on Pro | You ran the same routine multiple times | Upgrade to Max (15/day) or wait until midnight reset. |
| Briefing file missing after run completes | Working directory not set in the routine | Edit the routine in Claude Desktop and set Working Directory to your repo path. |

## Why we don't use Cloud Routines

Cloud Routines run on Anthropic infra and never see your local files. Every NEPSE workflow reads local state (`data/`, `state/`, `reports/`). Migrating would require:

- Hosting `data/ohlcv/` somewhere reachable (S3 + scheduled refresher)
- Mirroring `state/theses/` and the trader-memory state machine
- Hosting MeroShare-exported portfolio CSV

That's a deployment project, not a few-line config change. Stick with Local Tasks while you trade from one laptop.

## Manually triggering a routine

Each `.md` in this folder has a **"Run manually"** section showing the equivalent shell command. That's useful when:

- You missed the scheduled time and want to run the routine an hour late
- You want to test a wrapper script change before installing in a routine
- Your laptop was asleep at fire time and you want to catch up

Sources:

- [Schedule recurring tasks in Claude Code Desktop](https://code.claude.com/docs/en/desktop-scheduled-tasks)
- [Anthropic adds routines to redesigned Claude Code](https://9to5mac.com/2026/04/14/anthropic-adds-repeatable-routines-feature-to-claude-code-heres-how-it-works/)
