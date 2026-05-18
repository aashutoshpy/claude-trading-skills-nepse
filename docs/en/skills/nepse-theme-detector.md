---
layout: default
title: "Nepse Theme Detector"
grand_parent: English
parent: Skill Guides
nav_order: 56
lang_peer: /ja/skills/nepse-theme-detector/
permalink: /en/skills/nepse-theme-detector/
generated: true
---

# Nepse Theme Detector
{: .no_toc }

Detect emerging NEPSE investment themes by combining sector-rotation signals (from nepse-sector-analyst), breadth participation, and optional user-supplied theme tickers (e.g., "monsoon hydropower play", "rate-cut financials"). Outputs a ranked list of active themes with constituent names. Use when the user asks "what themes are working on NEPSE?", wants to align positions with the dominant narrative, or needs a thematic basket suggestion.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-theme-detector){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Theme Detector

---

## 2. Prerequisites

- Reads nepse-sector-analyst, nepse-market-breadth-analyzer, nepse-macro-regime-detector, nepse-uptrend-analyzer JSON; Optional user-supplied themes added to the built-in library
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
# Optional:
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

---

## 4. Workflow

### Step 1: Run upstream skills

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
# Optional:
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

### Step 2: Run the theme detector

```bash
# Default — use built-in themes
python3 skills/nepse-theme-detector/scripts/detect_themes.py \
  --reports-dir reports/ --output-dir reports/

# Bring your own themes
python3 skills/nepse-theme-detector/scripts/detect_themes.py \
  --reports-dir reports/ \
  --themes-csv data/my_nepse_themes.csv \
  --output-dir reports/
```

User CSV format:
```csv
theme_id,display_name,symbols,rationale
my_hydro,Custom Hydropower Basket,"UPPER,NHPC,BPCL",Monsoon thesis
```

### Step 3: Read output

- JSON: `reports/nepse_themes_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_themes_<YYYY-MM-DD>.md` — themes ranked by activity score

---

## 5. Resources

**Scripts:**

- `skills/nepse-theme-detector/scripts/_path_setup.py`
- `skills/nepse-theme-detector/scripts/detect_themes.py`
- `skills/nepse-theme-detector/scripts/theme_engine.py`
