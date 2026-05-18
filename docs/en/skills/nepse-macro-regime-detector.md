---
layout: default
title: "Nepse Macro Regime Detector"
grand_parent: English
parent: Skill Guides
nav_order: 48
lang_peer: /ja/skills/nepse-macro-regime-detector/
permalink: /en/skills/nepse-macro-regime-detector/
generated: true
---

# Nepse Macro Regime Detector
{: .no_toc }

Detect the macro regime affecting NEPSE — NRB monetary policy stance (currently tightening), USD/NPR direction, India Nifty 50 correlation read, Brent oil as import-cost proxy, and gold. Combines macro signals with breadth/sector inputs from other NEPSE skills to produce a regime label (RISK_ON / NEUTRAL / RISK_OFF) and a one-page rationale. Use when the user asks "what's the NEPSE macro regime?", needs context before sizing, or wants a regime-aware exposure recommendation.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-macro-regime-detector){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Macro Regime Detector

---

## 2. Prerequisites

- User-maintained CSV of NRB rate + global macro values (key,value,as_of); Reads JSON from nepse-market-breadth-analyzer and nepse-sector-analyst
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
# Aggregate macro + latest NEPSE breadth/sector reports
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv \
  --reports-dir reports/ \
  --output-dir reports/
```

---

## 4. Workflow

### Step 1: Update the macro CSV

Manually maintain `data/nepse_macro.csv` from public sources:
- NRB rate: nrb.org.np monetary policy archive
- USD/NPR: forex.com.np or similar
- Nifty 50, Brent, gold: tradingeconomics.com or any major financial portal

### Step 2: Run

```bash
# Aggregate macro + latest NEPSE breadth/sector reports
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv \
  --reports-dir reports/ \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_macro_regime_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_macro_regime_<YYYY-MM-DD>.md` with the regime label and contributing signals

---

## 5. Resources

**Scripts:**

- `skills/nepse-macro-regime-detector/scripts/_path_setup.py`
- `skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py`
- `skills/nepse-macro-regime-detector/scripts/macro_regime.py`
