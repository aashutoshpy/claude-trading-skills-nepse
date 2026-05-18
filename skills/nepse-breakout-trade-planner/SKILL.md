---
name: nepse-breakout-trade-planner
description: Convert nepse-vcp-screener candidates into manual-entry breakout trade plans. For each candidate computes entry trigger (pivot break), stop-loss (recent swing low or N% below entry), 1R/2R/3R targets, risk-based share count, and optional AMO (18:00-06:00) queue instructions. Use after nepse-vcp-screener to generate actionable trade plans the user enters manually at their broker.
---

# NEPSE Breakout Trade Planner

Consumes `nepse-vcp-screener` JSON output and emits a per-candidate manual-entry trade plan. Designed for NEPSE's manual-order reality (no brokerage API) and AMO queue (18:00–06:00 next-session window).

## Why a NEPSE-specific planner

The US `breakout-trade-planner` emits Alpaca order templates. NEPSE has no brokerage API, so:
- Entry = trigger price the user sets as a buy stop at their broker (or queues via AMO)
- Stop / targets are calculated values, not order primitives
- Position size is derived from account-level risk %, never from a broker call

## When to Use

- Immediately after `nepse-vcp-screener` produces candidates
- When the user wants concrete entry / stop / target prices for a watchlist
- When planning AMO queue entries for tomorrow's session

## Workflow

### Step 1: Run the VCP screener first

```bash
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --output-dir reports/
```

### Step 2: Plan the trades

```bash
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 \
  --risk-pct 1.0 \
  --output-dir reports/

# Stop-loss method: percent below entry (default 7%) or recent swing low (in JSON)
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 --risk-pct 1.5 \
  --stop-method percent --stop-pct 5.0 \
  --output-dir reports/

# Filter to only valid-VCP, score ≥70
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 --risk-pct 1.0 \
  --min-score 70 --valid-only \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_trade_plans_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_trade_plans_<YYYY-MM-DD>.md` with per-candidate plans

## Plan Schema (per candidate)

```yaml
symbol: NABIL
sector: BANKING
score: 78
entry_trigger: 1252.0          # pivot break — set as buy stop
stop_loss: 1164.36              # entry × (1 - stop_pct/100)
stop_pct: 7.0
risk_per_share: 87.64
shares: 11                      # floored to whole-share constraint
position_cost: 13772.0
position_pct_of_account: 1.38
target_1r: 1339.64              # entry + 1× risk
target_2r: 1427.28
target_3r: 1514.92
amo_instruction: "Queue buy stop at NPR 1252.00 between 18:00 and 06:00 for next session"
margin_eligible: true
warnings:
  - "Distance to pivot 0.6% — entry imminent; double-check stop placement"
```

## NEPSE-Specific Calibration

| Knob | Default | Why |
|---|---|---|
| `--stop-pct` | 7% | Same as US convention — Minervini's 7-8% maximum loss rule |
| Whole-share rounding | floor | NEPSE shares trade in 1-share increments (mutual funds + a few high-priced names are exceptions; ignored here) |
| AMO instruction | always included | Reflects April 2026 rule change permitting 18:00-06:00 queue entries |
| Position cap | 100% of account | No leverage assumed; user adds margin via `nepse-margin-eligibility` |

## Combining

- **Upstream:** `nepse-vcp-screener` (required), `nepse-technical-analyst` (chart confirmation)
- **Downstream:** `nepse-margin-eligibility` (check if leveraging is possible), `trader-memory-core` (register the planned trade as a thesis)

## Limitations

- Stop-loss percent is a heuristic. For NEPSE's 15% daily band, 7% is reasonable but consider tightening on illiquid names where a single gap can blow through the stop.
- Targets at 1R/2R/3R are mechanical — the actual trim/exit plan depends on `nepse-technical-analyst` chart context.
- Whole-share rounding means small accounts may not fill the full risk budget on high-priced names (e.g. BFI names trading >NPR 2000).
