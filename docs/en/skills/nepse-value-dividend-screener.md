---
layout: default
title: "Nepse Value Dividend Screener"
grand_parent: English
parent: Skill Guides
nav_order: 58
lang_peer: /ja/skills/nepse-value-dividend-screener/
permalink: /en/skills/nepse-value-dividend-screener/
generated: true
---

# Nepse Value Dividend Screener
{: .no_toc }

Screen NEPSE stocks for high dividend yield + reasonable valuation. NEPSE is dividend-heavy (especially BFIs and microfinance), and cash-plus-bonus dividend yields of 8-15% are common. Use when the user asks for NEPSE dividend candidates, value-yield screening, or income-portfolio construction. Accepts a user-provided dividend CSV because NEPSE backends do not yet expose structured dividend feeds.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-value-dividend-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Value + Dividend Screener

---

## 2. When to Use

- User asks "what NEPSE stocks pay the highest dividend?"
- User wants to build an income portfolio of NEPSE BFIs / insurance
- User asks for value names trading below historical averages
- After `nepse-kanchi-dividend-sop` (Phase 4) identifies candidates and the user wants a market-wide cross-check

---

## 3. Prerequisites

- OHLCV via common.nepse.NepseClient; User-pasted CSV from sharesansar/merolagani (symbol, cash_div_pct, bonus_div_pct)
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
`cash_div_pct` and `bonus_div_pct` are percentages of paid-up share
capital (NEPSE convention). Both contribute to total yield.

### Step 2: Run
```

---

## 5. Workflow

### Step 1: Prepare dividend CSV (recommended)

Manually export from sharesansar.com or merolagani.com:

```csv
symbol,cash_div_pct,bonus_div_pct,reported_at
NABIL,11.0,0.0,2025-12-15
NICA,16.0,4.0,2025-11-22
UPPER,0.0,12.0,2025-10-30
```

`cash_div_pct` and `bonus_div_pct` are percentages of paid-up share
capital (NEPSE convention). Both contribute to total yield.

### Step 2: Run

```bash
# With dividend CSV (preferred)
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --output-dir reports/

# Without CSV — OHLCV-derived only, less accurate
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --output-dir reports/

# Tune yield threshold
python3 skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py \
  --dividends data/nepse_dividends.csv \
  --min-yield 8.0 --top 20 \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_dividends_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_dividends_<YYYY-MM-DD>.md` with sorted candidates

### Step 4: Combine

- Cross-reference with `nepse-margin-eligibility` (Phase 3) — most BFI dividend names are margin-eligible
- Run `nepse-technical-analyst` on the top 3-5 to confirm chart setup before sizing
- Feed JSON to `nepse-kanchi-dividend-sop` (Phase 4) for the full Kanchi workflow

---

## 6. Resources

**Scripts:**

- `skills/nepse-value-dividend-screener/scripts/_path_setup.py`
- `skills/nepse-value-dividend-screener/scripts/dividend_scorer.py`
- `skills/nepse-value-dividend-screener/scripts/screen_nepse_dividends.py`
