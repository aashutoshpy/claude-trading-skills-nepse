---
layout: default
title: "Nepse Breakout Trade Planner"
grand_parent: English
parent: Skill Guides
nav_order: 37
lang_peer: /ja/skills/nepse-breakout-trade-planner/
permalink: /en/skills/nepse-breakout-trade-planner/
generated: true
---

# Nepse Breakout Trade Planner
{: .no_toc }

Convert nepse-vcp-screener candidates into manual-entry breakout trade plans. For each candidate computes entry trigger (pivot break), stop-loss (recent swing low or N% below entry), 1R/2R/3R targets, risk-based share count, and optional AMO (18:00-06:00) queue instructions. Use after nepse-vcp-screener to generate actionable trade plans the user enters manually at their broker.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-breakout-trade-planner){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Breakout Trade Planner

---

## 2. When to Use

- Immediately after `nepse-vcp-screener` produces candidates
- When the user wants concrete entry / stop / target prices for a watchlist
- When planning AMO queue entries for tomorrow's session

---

## 3. Prerequisites

- Reads nepse-vcp-screener JSON output
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --output-dir reports/
```

---

## 5. Workflow

### Step 1: Run the VCP screener first

```bash
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --output-dir reports/
```

### Step 2: Plan the trades

```bash
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 \
  --risk-pct 1.0 \
  --output-dir reports/

# Stop-loss method: percent below entry (default 7%) or recent swing low (in JSON)
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 --risk-pct 1.5 \
  --stop-method percent --stop-pct 5.0 \
  --output-dir reports/

# Filter to only valid-VCP, score ≥70
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_2026-05-17.json \
  --account-size 1000000 --risk-pct 1.0 \
  --min-score 70 --valid-only \
  --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_trade_plans_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_trade_plans_<YYYY-MM-DD>.md` with per-candidate plans

---

## 6. Resources

**Scripts:**

- `skills/nepse-breakout-trade-planner/scripts/_path_setup.py`
- `skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py`
- `skills/nepse-breakout-trade-planner/scripts/trade_planner.py`
