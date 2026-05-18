---
layout: default
title: "Nepse Sector Analyst"
grand_parent: English
parent: Skill Guides
nav_order: 53
lang_peer: /ja/skills/nepse-sector-analyst/
permalink: /en/skills/nepse-sector-analyst/
generated: true
---

# Nepse Sector Analyst
{: .no_toc }

Rank NEPSE's 13 sector indices by recent performance, identify sector rotation, and flag leading/lagging sectors. Computes 1-week / 1-month / 3-month / YTD returns per sector index and ranks them. Accepts a chart screenshot for visual sector-rotation confirmation. Use when the user asks "what NEPSE sectors are leading", wants to find where money is rotating, or needs sector context before drilling into individual names.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-sector-analyst){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Sector Analyst

---

## 2. When to Use

- User asks "which NEPSE sectors are leading?"
- User wants to know whether banks, hydropower, or microfinance is the leader
- User uploads a sector-comparison chart screenshot for visual rotation analysis
- Before drilling into individual names with `nepse-vcp-screener` or `nepse-technical-analyst`

---

## 3. Prerequisites

- Sector-index OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --output-dir reports/

# Custom lookback windows (defaults: 5d / 22d / 66d / YTD)
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --windows 10,30,90 --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --output-dir reports/

# Custom lookback windows (defaults: 5d / 22d / 66d / YTD)
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --windows 10,30,90 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_sectors_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_sectors_<YYYY-MM-DD>.md` with ranking tables

### Step 3: Combine

- Use the top-3 sectors as a filter for `nepse-vcp-screener` (focus screen on leaders)
- Cross-check with `nepse-market-breadth-analyzer` sector breakdown for confirmation
- Optional: user uploads a sector chart screenshot — read the visual rotation pattern alongside the numerical ranks

---

## 6. Resources

**References:**

- `skills/nepse-sector-analyst/references/nepse_sector_dynamics.md`

**Scripts:**

- `skills/nepse-sector-analyst/scripts/_path_setup.py`
- `skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py`
- `skills/nepse-sector-analyst/scripts/sector_ranker.py`
