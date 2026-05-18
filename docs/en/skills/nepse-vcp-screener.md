---
layout: default
title: "Nepse VCP Screener"
grand_parent: English
parent: Skill Guides
nav_order: 59
lang_peer: /ja/skills/nepse-vcp-screener/
permalink: /en/skills/nepse-vcp-screener/
generated: true
---

# Nepse VCP Screener
{: .no_toc }

Screen the NEPSE (Nepal Stock Exchange) universe for Mark Minervini's Volatility Contraction Pattern (VCP). Identifies Stage-2-uptrend stocks forming tight bases with contracting price ranges near a breakout pivot. Use when the user asks for NEPSE VCP screening, tight base / volatility contraction patterns on Nepali stocks, or Stage 2 momentum candidates in NEPSE. NOT for US stocks — use vcp-screener instead.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-vcp-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE VCP Screener

---

## 2. When to Use

- User asks for VCP / Stage 2 / tight-base screening on NEPSE
- User mentions Minervini-style setups in the context of Nepali stocks
- User wants a NEPSE candidate list for swing-trade planning

---

## 3. Prerequisites

- No API key (NEPSE backends are public). Default backend is the `nepalstock` scraper.
- Choose backend via `NEPSE_BACKEND=nepalstock|community` or `--backend`.
- Optional: rebuild the universe cache via `scripts/refresh_nepse_universe.py` (planned).

---

## 4. Quick Start

```bash
# Default: full NEPSE universe, top 30 candidates
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --output-dir reports/

# Specific symbols only
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols NABIL UPPER NICA --output-dir reports/

# Tighter contractions (research/backtest)
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --min-contractions 3 --max-final-contraction-pct 4 \
  --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run the screener

```bash
# Default: full NEPSE universe, top 30 candidates
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --output-dir reports/

# Specific symbols only
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols NABIL UPPER NICA --output-dir reports/

# Tighter contractions (research/backtest)
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --min-contractions 3 --max-final-contraction-pct 4 \
  --output-dir reports/
```

### Step 2: Review

- JSON: `reports/nepse_vcp_<YYYY-MM-DD>.json` — machine-readable, used by `nepse-breakout-trade-planner`
- Markdown: `reports/nepse_vcp_<YYYY-MM-DD>.md` — human-readable summary

### Step 3: Combine

- Feed JSON to `nepse-breakout-trade-planner` (Phase 3) for manual-entry plans
- Cross-reference candidates against `nepse-margin-eligibility` to know which can be traded on margin
- Run `nepse-technical-analyst` on the top 3-5 with a chart screenshot for visual confirmation

---

## 6. Resources

**References:**

- `skills/nepse-vcp-screener/references/nepse_vcp_methodology.md`

**Scripts:**

- `skills/nepse-vcp-screener/scripts/_path_setup.py`
- `skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py`
- `skills/nepse-vcp-screener/scripts/vcp_detector.py`
