---
layout: default
title: "Nepse Market Top Detector"
grand_parent: English
parent: Skill Guides
nav_order: 51
lang_peer: /ja/skills/nepse-market-top-detector/
permalink: /en/skills/nepse-market-top-detector/
generated: true
---

# Nepse Market Top Detector
{: .no_toc }

Aggregate multiple NEPSE-specific top signals (BFI overconcentration, microfinance euphoria, distribution-day count, breadth divergence, IPO/listing frenzy proxy) into a composite top-risk score and warning level. Use when the user asks "is NEPSE topping?", wants to size down before a correction, or runs a periodic top-risk check after an extended uptrend.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-market-top-detector){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Market Top Detector

---

## 2. When to Use

- User asks "is NEPSE topping?" or "how much top risk?"
- Periodic check after 3+ months of uptrend
- Before increasing exposure on individual-name screens
- Daily during `STRONG_UPTREND` regimes

---

## 3. Prerequisites

- Reads JSON from nepse-ibd-distribution-day-monitor, nepse-uptrend-analyzer, nepse-sector-analyst, nepse-market-breadth-analyzer
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run upstream skills first

```bash
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
```

### Step 2: Aggregate

```bash
python3 skills/nepse-market-top-detector/scripts/detect_top.py \
  --reports-dir reports/ --output-dir reports/

# Or specify each input explicitly
python3 skills/nepse-market-top-detector/scripts/detect_top.py \
  --distribution-json reports/nepse_distribution_days_2026-05-17.json \
  --uptrend-json reports/nepse_uptrend_2026-05-17.json \
  --sectors-json reports/nepse_sectors_2026-05-17.json \
  --breadth-json reports/nepse_breadth_2026-05-17.json \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_top_risk_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_top_risk_<YYYY-MM-DD>.md` — score, level, contributing signals

---

## 6. Resources

**Scripts:**

- `skills/nepse-market-top-detector/scripts/_path_setup.py`
- `skills/nepse-market-top-detector/scripts/detect_top.py`
- `skills/nepse-market-top-detector/scripts/top_scorer.py`
