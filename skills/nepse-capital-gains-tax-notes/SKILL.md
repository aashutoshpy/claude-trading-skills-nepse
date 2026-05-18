---
name: nepse-capital-gains-tax-notes
description: Compute Nepal capital gains tax on NEPSE share trades (5% long-term for >365-day holdings, 7.5% short-term; proposed uniform 10% flagged as not-enacted). Also documents broker withholding mechanics, exemptions, and exit-timing tax implications. Use when the user asks about NEPSE tax treatment, wants to estimate tax on a trade, or is timing an exit around the 365-day long-term threshold.
---

# NEPSE Capital Gains Tax Notes

Nepal's capital gains tax (CGT) on listed shares is simpler than the US framework but has a meaningful long-term-vs-short-term split. This skill exposes the current rates from `config/nepse_rules.yaml` and a small calculator.

## Current rates (verified May 2026)

| Holding period | CGT rate | Source |
|---|---:|---|
| Long-term (> 365 days) | **5%** | Income Tax Act, Schedule 1, Section 2(8) |
| Short-term (≤ 365 days) | **7.5%** | Same |
| Proposed uniform rate | **10%** (not enacted) | Government policy proposal (status: not enacted as of May 2026) |

Rates come from `config/nepse_rules.yaml` → `capital_gains_tax`. When SEBON / Income Tax Department updates the rates (or the proposed 10% is enacted), edit the YAML.

## Broker withholding

- NEPSE brokers withhold CGT at the source on every sell trade
- For individual investors, the withholding amount is treated as the final tax (no separate return required for the gain itself; you still file your annual return)
- For corporate investors and HNIs above certain thresholds, additional reconciliation may apply — consult a CA

## When to Use

- User asks "how much tax do I owe on this NEPSE trade?"
- User wants to estimate post-tax P&L
- User is deciding whether to sell now (short-term) or wait until the 366th day (long-term)
- Annual tax-planning review

## Workflow

### Step 1: Estimate tax on a single trade

```bash
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --entry-price 1180.00 \
  --exit-price 1340.00 \
  --shares 100 \
  --holding-days 280
```

Output:
```
NABIL: 100 shares  |  cost NPR 118,000  |  proceeds NPR 134,000
  Gross gain: NPR 16,000
  Holding: 280 days → SHORT-TERM (7.5% rate)
  Tax: NPR 1,200 (NPR 12.00/share)
  Net gain: NPR 14,800  |  Net return: 12.54%

  Note: hold for 86 more days (until 2026-08-10) to qualify for the
  5% long-term rate. Tax savings if held: NPR 400 (assumes price holds).
```

### Step 2: Batch estimate from a CSV

```csv
symbol,entry_price,exit_price,shares,entry_date
NABIL,1180.00,1340.00,100,2025-08-15
NICA,725.00,780.00,50,2025-04-10
UPPER,425.00,510.00,200,2024-11-20
```

```bash
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --batch-csv data/trade_estimates.csv
```

## Combining

- **Upstream:** `nepse-portfolio-tracker` (compute on open positions to estimate post-tax exits)
- **Companion:** `nepse-kanchi-dividend-sop` (dividend income tax differs and is covered there)

## Exemptions & special cases

- **Inheritance:** no CGT on inherited shares (treated as gift)
- **Bonus shares:** cost basis = original purchase × dilution factor; holding period inherited from the underlying
- **Right shares:** cost basis = right-share price paid; holding period starts when allotted
- **Capital losses:** offsettable against capital gains in the same fiscal year only (no carryforward as of May 2026)

## Limitations

- Calculator does NOT handle complex cost-basis adjustments (FIFO/LIFO/weighted-average across multiple lots). For multi-lot positions, compute per-lot manually.
- Bonus and right-share basis adjustments require manual calculation; the calculator treats them as cash-equivalent.
- This is informational, not tax advice. Consult a CA for filing-time decisions.
