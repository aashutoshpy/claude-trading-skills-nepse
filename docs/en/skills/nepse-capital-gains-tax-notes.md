---
layout: default
title: "Nepse Capital Gains Tax Notes"
grand_parent: English
parent: Skill Guides
nav_order: 39
lang_peer: /ja/skills/nepse-capital-gains-tax-notes/
permalink: /en/skills/nepse-capital-gains-tax-notes/
generated: true
---

# Nepse Capital Gains Tax Notes
{: .no_toc }

Compute Nepal capital gains tax on NEPSE share trades (5% long-term for >365-day holdings, 7.5% short-term; proposed uniform 10% flagged as not-enacted). Also documents broker withholding mechanics, exemptions, and exit-timing tax implications. Use when the user asks about NEPSE tax treatment, wants to estimate tax on a trade, or is timing an exit around the 365-day long-term threshold.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-capital-gains-tax-notes){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Capital Gains Tax Notes

---

## 2. When to Use

- User asks "how much tax do I owe on this NEPSE trade?"
- User wants to estimate post-tax P&L
- User is deciding whether to sell now (short-term) or wait until the 366th day (long-term)
- Annual tax-planning review

---

## 3. Prerequisites

- Reads tax rates from config/nepse_rules.yaml
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --entry-price 1180.00 \
  --exit-price 1340.00 \
  --shares 100 \
  --holding-days 280
```

---

## 5. Workflow

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

---

## 6. Resources

**Scripts:**

- `skills/nepse-capital-gains-tax-notes/scripts/_path_setup.py`
- `skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py`
- `skills/nepse-capital-gains-tax-notes/scripts/tax_calculator.py`
