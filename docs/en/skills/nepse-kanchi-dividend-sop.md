---
layout: default
title: "Nepse Kanchi Dividend SOP"
grand_parent: English
parent: Skill Guides
nav_order: 47
lang_peer: /ja/skills/nepse-kanchi-dividend-sop/
permalink: /en/skills/nepse-kanchi-dividend-sop/
generated: true
---

# Nepse Kanchi Dividend SOP
{: .no_toc }

NEPSE-specific Kanchi 5-step dividend investing workflow. Screens for high-quality NEPSE dividend payers (commercial banks, life insurance, established microfinance), validates with NEPSE-specific quality checks (dividend cash/bonus history, sector-relative yield, BFI capital adequacy proxy via book value), plans pullback limit-order entries, and schedules post-purchase reviews around the Nepali AGM cycle (Bhadra-Mangsir). Use when the user wants Kanchi-style dividend investing applied to NEPSE.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-kanchi-dividend-sop){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Kanchi Dividend SOP

---

## 2. When to Use

- User wants a repeatable, sector-aware NEPSE dividend buy process
- Building a long-term income portfolio of BFI/insurance/microfinance names
- Re-investing dividend cash post-AGM season
- Pairing with `nepse-value-dividend-screener` outputs for a structured workflow

---

## 3. Prerequisites

- Reads nepse-value-dividend-screener JSON
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --min-yield 6.0 --output-dir reports/
```

---

## 5. Workflow

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

---

## 6. Resources

**Scripts:**

- `skills/nepse-kanchi-dividend-sop/scripts/_path_setup.py`
- `skills/nepse-kanchi-dividend-sop/scripts/kanchi_quality_check.py`
- `skills/nepse-kanchi-dividend-sop/scripts/kanchi_scorer.py`
