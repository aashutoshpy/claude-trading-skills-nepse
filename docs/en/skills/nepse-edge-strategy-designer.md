---
layout: default
title: "Nepse Edge Strategy Designer"
grand_parent: English
parent: Skill Guides
nav_order: 45
lang_peer: /ja/skills/nepse-edge-strategy-designer/
permalink: /en/skills/nepse-edge-strategy-designer/
generated: true
---

# Nepse Edge Strategy Designer
{: .no_toc }

Convert NEPSE edge signals into backtestable strategy YAML drafts — entry rules, exit rules, position sizing, and falsification criteria. Reads prioritized signals from nepse-edge-signal-aggregator and produces one draft per ACT signal, with NEPSE-specific defaults (15% daily band, manual order entry, T+2 settlement, no shorting). Use when the user has prioritized edge signals and wants to formalize them as testable strategy specifications.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-edge-strategy-designer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Edge Strategy Designer

---

## 2. Prerequisites

- Reads nepse-edge-signal-aggregator JSON
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ --output-dir reports/
```

---

## 4. Workflow

### Step 1: Run upstream skills

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ --output-dir reports/
```

### Step 2: Design

```bash
python3 skills/nepse-edge-strategy-designer/scripts/design_strategies.py \
  --signals-json reports/nepse_edge_signals_2026-05-17.json \
  --output-dir reports/strategy_drafts/

# Only ACT-status signals (default)
python3 skills/nepse-edge-strategy-designer/scripts/design_strategies.py \
  --signals-json reports/nepse_edge_signals_2026-05-17.json \
  --include-watch \
  --output-dir reports/strategy_drafts/
```

### Step 3: Review

- One YAML per draft in `reports/strategy_drafts/`
- Summary JSON: `reports/nepse_strategy_drafts_<YYYY-MM-DD>.json`

### Step 4: Hand off

- Feed drafts to your backtester of choice (no NEPSE backtester is bundled — strategy YAML is the deliverable)
- Iterate: tighten/loosen entry rules, adjust risk_pct, re-test

---

## 5. Resources

**Scripts:**

- `skills/nepse-edge-strategy-designer/scripts/_path_setup.py`
- `skills/nepse-edge-strategy-designer/scripts/design_strategies.py`
- `skills/nepse-edge-strategy-designer/scripts/strategy_designer.py`
