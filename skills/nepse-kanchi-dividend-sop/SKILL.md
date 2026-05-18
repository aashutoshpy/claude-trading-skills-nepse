---
name: nepse-kanchi-dividend-sop
description: NEPSE-specific Kanchi 5-step dividend investing workflow. Screens for high-quality NEPSE dividend payers (commercial banks, life insurance, established microfinance), validates with NEPSE-specific quality checks (dividend cash/bonus history, sector-relative yield, BFI capital adequacy proxy via book value), plans pullback limit-order entries, and schedules post-purchase reviews around the Nepali AGM cycle (Bhadra-Mangsir). Use when the user wants Kanchi-style dividend investing applied to NEPSE.
---

# NEPSE Kanchi Dividend SOP

Adapts Kanchi's 5-step dividend investing method to NEPSE. The framework is universal; the calibration is NEPSE-specific.

## The 5 Steps

1. **Screen** — identify high-quality dividend payers
2. **Deep dive** — validate quality with sector-relative checks
3. **Plan entry** — wait for pullback; set limit orders
4. **Underwrite** — write a one-page memo with invalidation conditions
5. **Monitor** — schedule reviews around the Nepali AGM cycle

## NEPSE-Specific Adaptations

| Step | US (Kanchi original) | NEPSE adaptation |
|---|---|---|
| Screen | Yield ≥3.5%, dividend grower 5y+ | Yield ≥6%, cash+bonus dividend ≥10% of paid-up; BFI / insurance / microfinance |
| Quality check | DGR 5y, payout ratio | Cash/bonus split, BFI capital adequacy (book value > NPR 200 proxy), avoid recent bonus-share gaps |
| Entry timing | Pullback to MA200 or 30-week MA | Pullback to MA200; NEPSE BFI names often correct 15-25% around dividend-record dates — wait for stabilization |
| Underwrite | One-page memo | Same; add Nepali AGM date if known |
| Monitor cadence | Quarterly | Around Nepali fiscal Q-ends (Ashwin/Poush/Chaitra/Ashadh) + AGM season (Bhadra-Mangsir) |

## Dividend Cycle (NEPSE)

NEPSE companies hold AGMs (typically) in **Bhadra–Mangsir** (~Aug-Dec) and pay cash dividends within ~45 days of AGM. Bonus shares are credited to demat accounts in similar windows.

Order of operations during dividend season:
1. **Book-closure (BC) date announced** → trading halts for transfer cut-off
2. **Ex-dividend date** → price adjusts down by dividend amount
3. **AGM date** → dividend formally approved
4. **Cash distribution** → ~30-45 days post-AGM
5. **Bonus credit** → similar timing; demat balance updates

## When to Use

- User wants a repeatable, sector-aware NEPSE dividend buy process
- Building a long-term income portfolio of BFI/insurance/microfinance names
- Re-investing dividend cash post-AGM season
- Pairing with `nepse-value-dividend-screener` outputs for a structured workflow

## Workflow

### Step 1: Screen

Run [nepse-value-dividend-screener](../nepse-value-dividend-screener/):

```bash
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --min-yield 6.0 --output-dir reports/
```

### Step 2: Deep dive (use the helper)

```bash
python3 skills/nepse-kanchi-dividend-sop/scripts/kanchi_quality_check.py \
  --candidates-json reports/nepse_dividends_<date>.json \
  --output-dir reports/
```

The helper computes for each candidate:
- 200-day SMA proximity (entry quality)
- Pullback magnitude from 90-day high
- Cash/bonus split ratio (cash-heavy = preferred)
- A 0-100 Kanchi quality score

### Step 3: Plan entry

For each PASS candidate:
- Set a limit-order entry at 95-98% of current price (pullback target)
- Stop-loss: not used in long-term Kanchi style; instead, define an invalidation condition (e.g., yield falls below 5% AND price > 110% of entry → trim)

### Step 4: Underwrite

Write a one-page memo per the template in [references/kanchi_memo_template.md](references/kanchi_memo_template.md).

### Step 5: Monitor

- Review every Nepali fiscal Q-end and at AGM time
- Use `nepse-kanchi-dividend-review-monitor` (US version's equivalent — not yet ported to NEPSE; manual review for now)

## Output

- `reports/nepse_kanchi_quality_<date>.json` — per-candidate quality scores
- `reports/nepse_kanchi_quality_<date>.md` — human summary with action list

## Resources

- [references/nepse_kanchi_framework.md](references/nepse_kanchi_framework.md) — full framework with NEPSE-specific notes
- [references/kanchi_memo_template.md](references/kanchi_memo_template.md) — one-page underwriting memo

## Limitations

- US tax accounting (Form 1099-DIV, qualified dividends) is N/A — NEPSE uses [nepse-capital-gains-tax-notes](../nepse-capital-gains-tax-notes/)
- Requires `nepse-value-dividend-screener` to have run first
- Dividend history beyond the user-supplied CSV is not available; the helper cannot validate 5-year dividend growth streaks
- Microfinance dividends can fluctuate wildly with regulatory changes; treat the "dividend grower" criterion loosely for microfinance names
