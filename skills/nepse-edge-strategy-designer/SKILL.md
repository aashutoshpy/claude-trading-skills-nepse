---
name: nepse-edge-strategy-designer
description: Convert NEPSE edge signals into backtestable strategy YAML drafts — entry rules, exit rules, position sizing, and falsification criteria. Reads prioritized signals from nepse-edge-signal-aggregator and produces one draft per ACT signal, with NEPSE-specific defaults (15% daily band, manual order entry, T+2 settlement, no shorting). Use when the user has prioritized edge signals and wants to formalize them as testable strategy specifications.
---

# NEPSE Edge Strategy Designer

Takes a prioritized signal JSON from `nepse-edge-signal-aggregator` and emits a strategy-draft YAML per ACT signal. Drafts follow a backtest-ready schema.

## Strategy Draft Schema

```yaml
strategy_id: nepse_circuit_day_continuation_2026-05-17
based_on_signal: nepse_NABIL_2026-05-17
hypothesis: "Names that hit upper circuit on heavy volume often continue 3-5 sessions"
universe:
  source: nepse-edge-signal-aggregator
  symbols: [NABIL]
entry:
  trigger: open_after_signal
  filters:
    - "circuit_day_continuation observation present in last 1 session"
    - "sector in leading_sectors per nepse-sector-analyst (optional)"
exit:
  take_profit_pct: 7.0
  stop_loss_pct: 4.0
  time_stop_sessions: 5
sizing:
  method: risk_pct_of_account
  risk_pct: 1.0
  whole_share_rounding: floor
constraints:
  long_only: true            # NEPSE forbids shorting
  daily_price_band_pct: 15.0  # post-April 2026
  settlement_t_plus: 2
  amo_eligible: true          # AMO window 18:00-06:00 (post-April 2026)
falsification:
  metric: forward_3_session_return
  threshold_pct: -5.0
  interpretation: "If basket avg forward 3-session return < -5%, the hypothesis fails"
metadata:
  market: NEPSE
  created_at: 2026-05-17
  draft_status: untested
```

## Workflow

### Step 1: Run upstream skills

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ --output-dir reports/
```

### Step 2: Design

```bash
python3 skills/nepse-edge-strategy-designer/scripts/design_strategies.py \
  --signals-json reports/nepse_edge_signals_2026-05-17.json \
  --output-dir reports/strategy_drafts/

# Only ACT-status signals (default)
python3 skills/nepse-edge-strategy-designer/scripts/design_strategies.py \
  --signals-json reports/nepse_edge_signals_2026-05-17.json \
  --include-watch \
  --output-dir reports/strategy_drafts/
```

### Step 3: Review

- One YAML per draft in `reports/strategy_drafts/`
- Summary JSON: `reports/nepse_strategy_drafts_<YYYY-MM-DD>.json`

### Step 4: Hand off

- Feed drafts to your backtester of choice (no NEPSE backtester is bundled — strategy YAML is the deliverable)
- Iterate: tighten/loosen entry rules, adjust risk_pct, re-test

## NEPSE-Specific Defaults Baked In

| Default | Value | Why |
|---|---|---|
| `long_only` | true | NEPSE forbids short selling |
| `daily_price_band_pct` | 15.0 | Post-April 2026 |
| `settlement_t_plus` | 2 | T+2 settlement |
| `whole_share_rounding` | floor | Most NEPSE names trade in 1-share increments |
| `amo_eligible` | true | AMO window 18:00-06:00 since April 2026 |
| `take_profit_pct` | 7.0 | Minervini-style 1R-ish; tuned for 15% band |
| `stop_loss_pct` | 4.0 | Tighter than US default |
| `time_stop_sessions` | 5 | NEPSE base / breakout cycles are shorter |

All defaults are configurable per detector via per-detector templates baked into the designer.

## Limitations

- No bundled NEPSE backtester — strategy YAML is the deliverable; you must run a backtest separately
- Per-detector templates are minimal heuristics; substantive strategy design requires backtest + iteration
- Falsification metric (3-session forward return) is one of many possible — modify as your research progresses
- "Universe" field captures only the signal's symbol(s); for sector-baseline strategies, expand the universe manually
