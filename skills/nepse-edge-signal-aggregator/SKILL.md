---
name: nepse-edge-signal-aggregator
description: Aggregate, deduplicate, and prioritize NEPSE edge tickets from nepse-edge-candidate-agent into a ranked signal list. Cross-references the same symbol appearing in multiple detector outputs (signal confluence), filters out stale tickets, and emits a prioritized JSON for nepse-edge-strategy-designer. Use when the user has accumulated edge tickets and wants to know which signals to act on first.
---

# NEPSE Edge Signal Aggregator

Reads a directory of edge tickets (YAML files from `nepse-edge-candidate-agent`), deduplicates same-symbol observations across detectors, and ranks signals by confluence + recency + detector confidence.

## Why

A single symbol can show up in multiple detectors at once (e.g., a hydropower name making a new 30-day high AND hitting upper circuit on heavy volume). Confluence increases conviction.

## Workflow

### Step 1: Have edge tickets

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
```

### Step 2: Aggregate

```bash
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ \
  --output-dir reports/

# Filter by max age (default 7 days)
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ \
  --max-age-days 3 --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_edge_signals_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_edge_signals_<YYYY-MM-DD>.md` — top signals ranked by composite score

## Ranking Formula

```
composite = (confluence × 30) + (recency_score × 25) + (detector_confidence × 25) + (sector_boost × 20)
```

- **confluence**: number of detectors that flagged this symbol (1, 2, 3+)
- **recency_score**: 100 if ticket as_of is today, decays linearly to 0 over max_age_days
- **detector_confidence**: per-detector base score (circuit_day = 80, monsoon_hydro = 70, microfinance_turnaround = 60, bfi_dividend_pullback = 65)
- **sector_boost**: +20 if the symbol's sector currently leads (consumes `nepse-sector-analyst` JSON if available)

Signals scoring ≥75 are flagged ACT; 50-74 are WATCH; <50 are NOISE.

## Output Schema

```yaml
symbol: NABIL
sector: BANKING
composite_score: 82
status: ACT
confluence: 2
detectors_flagged:
  - circuit_day_continuation
  - bfi_dividend_pullback
recency_score: 100
sector_boost: 20
ticket_refs:
  - edge_2026-05-17_circuit_day_continuation_001.yaml
  - edge_2026-05-17_bfi_dividend_pullback_001.yaml
```

## Combining

- **Upstream:** `nepse-edge-candidate-agent`
- **Downstream:** `nepse-edge-strategy-designer` (consume prioritized signals)

## Limitations

- Detector-confidence weights are unbacktested — start values reflect "obvious" reliability ordering
- Confluence weight (30 pts) is heuristic; a single high-quality detector can outscore 2 weak detectors only if recency+sector boosts align
- "Sector boost" requires `nepse-sector-analyst` output to be fresh
