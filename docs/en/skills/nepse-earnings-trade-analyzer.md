---
layout: default
title: "Nepse Earnings Trade Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 42
lang_peer: /ja/skills/nepse-earnings-trade-analyzer/
permalink: /en/skills/nepse-earnings-trade-analyzer/
generated: true
---

# Nepse Earnings Trade Analyzer
{: .no_toc }

Score NEPSE post-quarterly-result reactions using the 5-factor framework (gap %, trend stage, volume surge, distance to MA200, distance to MA50) to identify continuation vs. fade candidates. Calibrated for NEPSE's 15% daily price band and quarterly reporting cycle (Nepali fiscal year). Use after a NEPSE company files its unaudited quarterly statement and the user wants a quantitative read on the post-report move.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-earnings-trade-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Earnings Trade Analyzer

---

## 2. Prerequisites

- OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
# Single ticker post-result analysis
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --symbol NABIL --report-date 2026-05-15 \
  --output-dir reports/

# Batch (CSV of recent filers)
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --batch-csv data/recent_filers.csv --output-dir reports/
```

---

## 4. Workflow

### Step 1: Identify reporting companies

Use `nepse-earnings-calendar` to find companies that recently filed.

### Step 2: Run the analyzer

```bash
# Single ticker post-result analysis
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --symbol NABIL --report-date 2026-05-15 \
  --output-dir reports/

# Batch (CSV of recent filers)
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --batch-csv data/recent_filers.csv --output-dir reports/
```

CSV format:
```csv
symbol,report_date
NABIL,2026-05-15
NICA,2026-05-12
UPPER,2026-05-14
```

### Step 3: Read output

- JSON: `reports/nepse_earnings_analysis_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_earnings_analysis_<YYYY-MM-DD>.md`

---

## 5. Resources

**Scripts:**

- `skills/nepse-earnings-trade-analyzer/scripts/_path_setup.py`
- `skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py`
- `skills/nepse-earnings-trade-analyzer/scripts/earnings_scorer.py`
