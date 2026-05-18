---
name: nepse-edge-candidate-agent
description: Detect NEPSE-specific anomalies in OHLCV data that may indicate exploitable edges — circuit-day breakouts, monsoon-season hydropower clusters, microfinance turn-around setups, BFI dividend-season pullbacks. Outputs edge tickets (YAML) describing the observed anomaly, candidates, and a hypothesis. Use when the user wants systematic edge discovery for NEPSE strategy research.
---

# NEPSE Edge Candidate Agent

Scans NEPSE OHLCV for anomalies that the standard screeners (VCP, CANSLIM) don't surface. Emits "edge tickets" — small YAML files describing each observation with candidates and a falsifiable hypothesis.

## Anomaly Detectors

| Detector | What it looks for |
|---|---|
| `circuit_day_continuation` | Stocks that hit upper circuit (+14.5%+) with above-average volume in the last 5 sessions; hypothesis: continuation play |
| `monsoon_hydro_cluster` | Hydropower names making new 30-day highs together (May-August window) |
| `microfinance_turnaround` | Microfinance stocks that bounced ≥10% off a 90-day low within the last 5 sessions |
| `bfi_dividend_pullback` | BFI names that gapped down by ~dividend amount in the last 10 sessions (potential ex-div bargains) |

Each detector emits 0-N tickets per run.

## Edge Ticket Schema (YAML)

```yaml
ticket_id: edge_2026-05-17_circuit_day_continuation_001
detector: circuit_day_continuation
as_of: 2026-05-17
description: 3 NEPSE names hit upper circuit on >2x avg volume in last 5 sessions
candidates:
  - symbol: NABIL
    observation:
      circuit_date: 2026-05-15
      circuit_close: 1252.0
      volume_ratio: 2.8
hypothesis: |
  Names that hit upper circuit on heavy volume often follow through with
  continued strength in the next 3-5 sessions. Test: enter at next open,
  exit at 7% gain or 4% stop.
falsification: If 3-session forward return < -5% for the basket, hypothesis fails.
```

## Workflow

### Step 1: Run

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/

# Run a specific detector only
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py \
  --detector circuit_day_continuation --output-dir reports/edge_tickets/
```

### Step 2: Read tickets

- One YAML per ticket in `reports/edge_tickets/<ticket_id>.yaml`
- Summary JSON: `reports/nepse_edge_tickets_<YYYY-MM-DD>.json`

### Step 3: Combine downstream

- Feed tickets to `nepse-edge-signal-aggregator` to prioritize across detectors
- Feed prioritized signals to `nepse-edge-strategy-designer` for backtestable strategy drafts

## Limitations

- Detectors are heuristic — false positives are expected
- Hydropower cluster detector assumes the monsoon-window calendar (May-Aug); off-season runs return empty
- Microfinance turnaround can be noise from regulatory whipsaws
- BFI ex-div detection requires the user to maintain `nepse-value-dividend-screener` CSV; without it, large gap-downs may be tagged as ex-div when they are not
- Long-only constraint: short-side anomalies are not surfaced (NEPSE forbids shorting)
