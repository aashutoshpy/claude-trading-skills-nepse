---
layout: default
title: "Nepse Uptrend Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 57
lang_peer: /ja/skills/nepse-uptrend-analyzer/
permalink: /en/skills/nepse-uptrend-analyzer/
generated: true
---

# Nepse Uptrend Analyzer
{: .no_toc }

Compute the NEPSE Uptrend Ratio — the percentage of listed names trading above their 200-day SMA — as a single trend-strength gauge. Tracks the 1-year history of the ratio to identify regime shifts, bullish/bearish thresholds, and divergences vs. the NEPSE composite index. Use when the user asks "is NEPSE in an uptrend?", wants a single trend-health number, or needs context for position sizing across the portfolio.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-uptrend-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Uptrend Analyzer

---

## 2. When to Use

- User asks "is NEPSE in an uptrend?" or "is the trend healthy?"
- User wants a one-number trend gauge for sizing decisions
- User wants to spot divergence between the index and breadth (often precedes tops)
- Daily ritual before running individual-name screens

---

## 3. Prerequisites

- Full-universe OHLCV + composite index via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --output-dir reports/

# History window (default: 252 trading days = ~1 year)
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --history-days 504 --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run

```bash
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --output-dir reports/

# History window (default: 252 trading days = ~1 year)
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --history-days 504 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_uptrend_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_uptrend_<YYYY-MM-DD>.md` with the regime call, trend, and divergence

### Step 3: Combine

- Feed the regime label to `exposure-coach` (market-agnostic) for portfolio sizing
- Cross-check with `nepse-market-breadth-analyzer` for confirmation
- Use the divergence flag with `nepse-market-top-detector` for top warnings

---

## 6. Resources

**Scripts:**

- `skills/nepse-uptrend-analyzer/scripts/_path_setup.py`
- `skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py`
- `skills/nepse-uptrend-analyzer/scripts/uptrend_calculator.py`
