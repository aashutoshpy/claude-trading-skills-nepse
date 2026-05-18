---
layout: default
title: "Nepse Market Breadth Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 50
lang_peer: /ja/skills/nepse-market-breadth-analyzer/
permalink: /en/skills/nepse-market-breadth-analyzer/
generated: true
---

# Nepse Market Breadth Analyzer
{: .no_toc }

Compute NEPSE market breadth indicators — advances vs. declines, new 52-week highs/lows, % of constituents above 50-day and 200-day SMAs, sector participation — from the full NEPSE universe via NepseClient. Use when the user asks about NEPSE market health, breadth signals, "is the rally narrow or broad", or wants context for sizing decisions across the whole portfolio.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-market-breadth-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Market Breadth Analyzer

---

## 2. When to Use

- User asks "is the NEPSE rally broad or narrow?"
- User wants to size up/down based on market breadth (call this BEFORE individual-name screens like `nepse-vcp-screener`)
- User asks about new highs/lows or A/D ratio for NEPSE
- Pre-condition for `exposure-coach` (shared US/NEPSE skill) to make exposure recommendations

---

## 3. Prerequisites

- Full-universe OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
# Default: compute breadth for today
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --output-dir reports/

# Backfill a specific date (needs cached or live history)
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --as-of 2026-05-15 --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run

```bash
# Default: compute breadth for today
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --output-dir reports/

# Backfill a specific date (needs cached or live history)
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --as-of 2026-05-15 --output-dir reports/
```

### Step 2: Read the output

- JSON: `reports/nepse_breadth_<YYYY-MM-DD>.json` — machine-readable; used by `exposure-coach` and `nepse-macro-regime-detector`
- Markdown: `reports/nepse_breadth_<YYYY-MM-DD>.md` — human summary with regime call

### Step 3: Combine

- Feed JSON to `nepse-macro-regime-detector` (Phase 2) for full regime context
- Feed to `exposure-coach` (existing market-agnostic skill) for portfolio sizing recommendation
- Use the per-sector breakdown to confirm `nepse-sector-analyst` calls

---

## 6. Resources

**References:**

- `skills/nepse-market-breadth-analyzer/references/nepse_breadth_indicators.md`

**Scripts:**

- `skills/nepse-market-breadth-analyzer/scripts/_path_setup.py`
- `skills/nepse-market-breadth-analyzer/scripts/breadth_calculator.py`
- `skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py`
