---
layout: default
title: "Nepse Ibd Distribution Day Monitor"
grand_parent: English
parent: Skill Guides
nav_order: 46
lang_peer: /ja/skills/nepse-ibd-distribution-day-monitor/
permalink: /en/skills/nepse-ibd-distribution-day-monitor/
generated: true
---

# Nepse Ibd Distribution Day Monitor
{: .no_toc }

Monitor the NEPSE composite index for IBD-style distribution days — sessions where the index closes down ≥0.2% on higher volume than the prior session. Counts active distribution days in the rolling 25-session window; ≥5 signals institutional distribution risk. Use when the user asks "is the NEPSE rally in danger?", wants top-of-market warning signals, or needs context before increasing exposure.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-ibd-distribution-day-monitor){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE IBD Distribution Day Monitor

---

## 2. When to Use

- User asks "are there distribution days on NEPSE?"
- User wants top-of-market warning signals before increasing exposure
- Daily monitoring after a long uptrend (≥3 months)
- As an input to `nepse-market-top-detector` (Phase 2)

---

## 3. Prerequisites

- NEPSE composite index OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --output-dir reports/

# Custom thresholds
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --window 25 --min-down-pct 0.2 --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --output-dir reports/

# Custom thresholds
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py \
  --window 25 --min-down-pct 0.2 --output-dir reports/
```

### Step 2: Read output

- JSON: `reports/nepse_distribution_days_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_distribution_days_<YYYY-MM-DD>.md`

### Step 3: Combine

- Feed JSON to `nepse-market-top-detector` (Phase 2)
- Cross-check with `nepse-uptrend-analyzer` divergence flag
- Use as a sizing input alongside `nepse-market-breadth-analyzer` regime call

---

## 6. Resources

**Scripts:**

- `skills/nepse-ibd-distribution-day-monitor/scripts/_path_setup.py`
- `skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py`
- `skills/nepse-ibd-distribution-day-monitor/scripts/distribution_days.py`
