---
layout: default
title: "Nepse CANSLIM Screener"
grand_parent: English
parent: Skill Guides
nav_order: 38
lang_peer: /ja/skills/nepse-canslim-screener/
permalink: /en/skills/nepse-canslim-screener/
generated: true
---

# Nepse CANSLIM Screener
{: .no_toc }

CANSLIM-style screening adapted for NEPSE. Combines OHLCV-derived factors (M = market direction, S = supply/demand from volume surge, L = leader via relative strength, I = institutional via large floorsheet trades, N = new highs proxy) with a user-supplied fundamentals CSV (C = current earnings, A = annual earnings) since NEPSE backends do not expose fundamentals. Use when the user asks for NEPSE growth-stock screening, CANSLIM candidates, or William O'Neil style setups on Nepali stocks.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-canslim-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE CANSLIM Screener

---

## 2. Prerequisites

- OHLCV + NEPSE composite index via common.nepse.NepseClient; EPS/sales growth CSV from sharesansar (C and A factors); Reads nepse-uptrend-analyzer JSON for the M factor
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
### Step 2: Run upstream skills first
```

---

## 4. Workflow

### Step 1: Prepare fundamentals CSV (recommended)

Manually export from sharesansar:

```csv
symbol,eps_latest,eps_prior_year,eps_3y_cagr,sales_3y_cagr
NABIL,32.5,28.4,11.5,9.2
NICA,42.1,36.8,14.2,8.1
UPPER,3.8,2.1,32.0,28.5
```

### Step 2: Run upstream skills first

```bash
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
```

### Step 3: Run the CANSLIM screener

```bash
python3 skills/nepse-canslim-screener/scripts/screen_canslim.py \
  --fundamentals-csv data/nepse_fundamentals.csv \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --output-dir reports/

# Strict M gate (only run if STRONG_UPTREND)
python3 skills/nepse-canslim-screener/scripts/screen_canslim.py \
  --fundamentals-csv data/nepse_fundamentals.csv \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --require-strong-uptrend \
  --output-dir reports/
```

### Step 4: Read output

- JSON: `reports/nepse_canslim_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_canslim_<YYYY-MM-DD>.md` with per-candidate component breakdown

---

## 5. Resources

**Scripts:**

- `skills/nepse-canslim-screener/scripts/_path_setup.py`
- `skills/nepse-canslim-screener/scripts/canslim_scorer.py`
- `skills/nepse-canslim-screener/scripts/screen_canslim.py`
