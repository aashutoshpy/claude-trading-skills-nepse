---
layout: default
title: "Nepse Stanley Druckenmiller Investment"
grand_parent: English
parent: Skill Guides
nav_order: 54
lang_peer: /ja/skills/nepse-stanley-druckenmiller-investment/
permalink: /en/skills/nepse-stanley-druckenmiller-investment/
generated: true
---

# Nepse Stanley Druckenmiller Investment
{: .no_toc }

Synthesize NEPSE macro, micro, and sentiment signals into a Druckenmiller-style top-down read for NEPSE positioning. Combines NRB monetary policy, USD/NPR, India Nifty correlation, NEPSE breadth, sector rotation, top-risk score, and uptrend regime into a single bias score and recommended portfolio tilt. Use when the user wants a top-down NEPSE thesis, a macro-overlay sizing decision, or a Druckenmiller-style "is the cycle with me" check.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-stanley-druckenmiller-investment){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Stanley Druckenmiller Investment

---

## 2. When to Use

- User asks for a top-down NEPSE thesis
- Quarterly review of overall portfolio tilt
- After a regime shift (NRB rate change, political event, major index move)
- Before a large position change

---

## 3. Prerequisites

- Reads JSON from nepse-macro-regime-detector, nepse-uptrend-analyzer, nepse-market-breadth-analyzer, nepse-sector-analyst, nepse-market-top-detector, nepse-ibd-distribution-day-monitor
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-market-top-detector/scripts/detect_top.py --reports-dir reports/ --output-dir reports/
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run all upstream skills

```bash
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py --output-dir reports/
python3 skills/nepse-ibd-distribution-day-monitor/scripts/count_distribution_days.py --output-dir reports/
python3 skills/nepse-market-top-detector/scripts/detect_top.py --reports-dir reports/ --output-dir reports/
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

### Step 2: Synthesize

```bash
python3 skills/nepse-stanley-druckenmiller-investment/scripts/synthesize_thesis.py \
  --reports-dir reports/ --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_druckenmiller_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_druckenmiller_<YYYY-MM-DD>.md` — bias, tilt, rationale

---

## 6. Resources

**Scripts:**

- `skills/nepse-stanley-druckenmiller-investment/scripts/_path_setup.py`
- `skills/nepse-stanley-druckenmiller-investment/scripts/druck_synthesizer.py`
- `skills/nepse-stanley-druckenmiller-investment/scripts/synthesize_thesis.py`
