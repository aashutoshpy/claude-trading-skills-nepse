---
layout: default
title: "Nepse Edge Signal Aggregator"
grand_parent: English
parent: Skill Guides
nav_order: 44
lang_peer: /ja/skills/nepse-edge-signal-aggregator/
permalink: /en/skills/nepse-edge-signal-aggregator/
generated: true
---

# Nepse Edge Signal Aggregator
{: .no_toc }

Aggregate, deduplicate, and prioritize NEPSE edge tickets from nepse-edge-candidate-agent into a ranked signal list. Cross-references the same symbol appearing in multiple detector outputs (signal confluence), filters out stale tickets, and emits a prioritized JSON for nepse-edge-strategy-designer. Use when the user has accumulated edge tickets and wants to know which signals to act on first.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-edge-signal-aggregator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Edge Signal Aggregator

---

## 2. Prerequisites

- Reads YAML tickets from nepse-edge-candidate-agent
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
```

---

## 4. Workflow

### Step 1: Have edge tickets

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/
```

### Step 2: Aggregate

```bash
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ \
  --output-dir reports/

# Filter by max age (default 7 days)
python3 skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py \
  --tickets-dir reports/edge_tickets/ \
  --max-age-days 3 --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_edge_signals_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_edge_signals_<YYYY-MM-DD>.md` — top signals ranked by composite score

---

## 5. Resources

**Scripts:**

- `skills/nepse-edge-signal-aggregator/scripts/_path_setup.py`
- `skills/nepse-edge-signal-aggregator/scripts/aggregate_signals.py`
- `skills/nepse-edge-signal-aggregator/scripts/signal_aggregator.py`
