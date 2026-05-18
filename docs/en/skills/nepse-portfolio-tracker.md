---
layout: default
title: "Nepse Portfolio Tracker"
grand_parent: English
parent: Skill Guides
nav_order: 52
lang_peer: /ja/skills/nepse-portfolio-tracker/
permalink: /en/skills/nepse-portfolio-tracker/
generated: true
---

# Nepse Portfolio Tracker
{: .no_toc }

Track a NEPSE portfolio from MeroShare CSV/manual entries. Computes per-position P&L, total exposure, sector concentration, margin usage warnings (cross-referencing the 123-name margin-eligible list), and unrealized gain/loss. Use when the user wants a snapshot of their NEPSE holdings, needs sector-concentration risk analysis, or is reviewing margin exposure across the portfolio.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-portfolio-tracker){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Portfolio Tracker

---

## 2. When to Use

- User wants a snapshot of their NEPSE portfolio
- Periodic review (weekly / monthly) of sector concentration and unrealized P&L
- Margin-exposure audit after the April 2026 framework launch
- Before adding a new position — verify portfolio risk budget

---

## 3. Prerequisites

- Hand-maintained or MeroShare-exported portfolio CSV; Optional live-price lookup via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Include latest prices (default uses last close from NepseClient)
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Skip live-price lookup (offline mode — uses avg_cost as "current")
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --no-fetch-prices \
  --output-dir reports/
```

---

## 5. Workflow

### Step 1: Export from MeroShare

Log into meroshare.cdsc.com.np → My Portfolio → Export. Save as `data/nepse_portfolio.csv`. (Or maintain manually.)

### Step 2: Run

```bash
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Include latest prices (default uses last close from NepseClient)
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/

# Skip live-price lookup (offline mode — uses avg_cost as "current")
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --no-fetch-prices \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_portfolio_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_portfolio_<YYYY-MM-DD>.md` — per-position table + sector breakdown + risk warnings

---

## 6. Resources

**Scripts:**

- `skills/nepse-portfolio-tracker/scripts/_path_setup.py`
- `skills/nepse-portfolio-tracker/scripts/portfolio_aggregator.py`
- `skills/nepse-portfolio-tracker/scripts/track_portfolio.py`
