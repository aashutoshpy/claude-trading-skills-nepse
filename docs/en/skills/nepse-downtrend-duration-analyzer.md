---
layout: default
title: "Nepse Downtrend Duration Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 40
lang_peer: /ja/skills/nepse-downtrend-duration-analyzer/
permalink: /en/skills/nepse-downtrend-duration-analyzer/
generated: true
---

# Nepse Downtrend Duration Analyzer
{: .no_toc }

Analyze NEPSE composite index history to identify past downtrends, measure their duration (peak-to-trough and trough-to-recovery), and produce a distribution of historical correction lengths. Use when the user wants context for how long a current NEPSE pullback might last, how prior corrections compare, or what depths are historically typical.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-downtrend-duration-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Downtrend Duration Analyzer

---

## 2. When to Use

- "How long do NEPSE corrections usually last?"
- "Is this drawdown unusually deep or unusually long?"
- "When should I expect recovery?"
- Sizing decisions during an active correction

---

## 3. Prerequisites

- NEPSE composite index OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --output-dir reports/

# Custom drawdown threshold
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --min-depth-pct 7.0 --output-dir reports/

# Long history (more years of data)
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --lookback-days 3650 --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run

```bash
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --output-dir reports/

# Custom drawdown threshold
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --min-depth-pct 7.0 --output-dir reports/

# Long history (more years of data)
python3 skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py \
  --lookback-days 3650 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_downtrend_history_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_downtrend_history_<YYYY-MM-DD>.md` with the table + distribution

---

## 6. Resources

**Scripts:**

- `skills/nepse-downtrend-duration-analyzer/scripts/_path_setup.py`
- `skills/nepse-downtrend-duration-analyzer/scripts/analyze_downtrends.py`
- `skills/nepse-downtrend-duration-analyzer/scripts/downtrend_detector.py`
