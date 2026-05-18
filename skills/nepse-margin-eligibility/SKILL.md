---
name: nepse-margin-eligibility
description: Check whether a NEPSE ticker is on the 123-name margin-eligible list (live since April 2026), report initial/maintenance margin requirements (30%/20%), and compute margin-call distance for a given position. Use when the user asks "can I trade X on margin?", needs to know how close a margin position is to a margin call, or is reviewing portfolio risk for leveraged names.
---

# NEPSE Margin Eligibility

Small utility skill that wraps the foundation's margin-eligible list and the NEPSE margin rules (30% initial / 20% maintenance) for quick lookups.

## When to Use

- User asks "can I trade <ticker> on margin?"
- User asks "how close to a margin call is my position?"
- Before sizing a position you intend to lever
- Cross-reference from `nepse-portfolio-tracker` to flag positions using margin
- Cross-reference from `nepse-vcp-screener` candidates list to know which can be leveraged

## NEPSE Margin Rules (verified May 2026)

| Rule | Value | Source |
|---|---|---|
| Eligible names | 123 | SEBON margin-eligibility notice (April 2026) |
| Initial margin | 30% (broker finances up to 70%) | Margin Trading Facilitation Procedure 2082 |
| Maintenance margin | 20% (margin call triggered below) | Same |
| Framework effective | 2026-02-13 | SEBON |
| Service go-live | 2026-04-15 (Baisakh 2, 2082) | Stock Brokers Association of Nepal |

All values are loaded from `config/nepse_rules.yaml` and `config/registry.yaml` — when SEBON updates the list or rules, edit the YAML; do NOT touch Python.

## Workflow

### Step 1: Check eligibility

```bash
# Single ticker
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL

# Multiple tickers
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL UPPER NICA
```

Output:
```
NABIL: ELIGIBLE   initial=30%   maintenance=20%
UPPER: ELIGIBLE   initial=30%   maintenance=20%
NICA: NOT_ELIGIBLE
```

### Step 2: Compute margin-call distance for a position

```bash
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL \
  --entry-price 1245.00 \
  --shares 100 \
  --margin-pct 30 \
  --current-price 1180.00
```

Output:
```
NABIL: ELIGIBLE   position cost=NPR 124,500   borrowed=NPR 87,150   equity=NPR 37,350
Current equity (at NPR 1,180.00): NPR 30,850
Margin call triggered below: NPR 1,089.38   (-12.5% from current)
```

## Margin-Call Math

NEPSE margin trading lets you buy shares worth more than your cash by borrowing the rest from the broker.

```
Position cost  = shares × entry_price
Initial equity = position_cost × initial_margin_pct (typically 30%)
Borrowed      = position_cost - initial_equity
Current equity at price P = (shares × P) - borrowed
Maintenance equity threshold = (shares × P_margin_call) × maintenance_margin_pct
Solving for P_margin_call:
  P_margin_call = borrowed / (shares × (1 - maintenance_margin_pct))
```

## Resources

- [references/nepse_margin_rules.md](references/nepse_margin_rules.md) — detailed rule explanation, broker-call mechanics, NEPSE-specific risks

## Limitations

- The eligible-name list lives in `config/registry.yaml`. Until the user populates `margin_eligible_symbols` (currently seeded empty), every check returns NOT_ELIGIBLE. Run the (to-be-built) `scripts/refresh_nepse_registry.py` to populate.
- Real margin trading is broker-specific — some brokers may require higher than the 30% / 20% minima. This skill reports the SEBON regulatory minimum, not your broker's policy.
