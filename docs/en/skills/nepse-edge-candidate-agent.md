---
layout: default
title: "Nepse Edge Candidate Agent"
grand_parent: English
parent: Skill Guides
nav_order: 43
lang_peer: /ja/skills/nepse-edge-candidate-agent/
permalink: /en/skills/nepse-edge-candidate-agent/
generated: true
---

# Nepse Edge Candidate Agent
{: .no_toc }

Detect NEPSE-specific anomalies in OHLCV data that may indicate exploitable edges — circuit-day breakouts, monsoon-season hydropower clusters, microfinance turn-around setups, BFI dividend-season pullbacks. Outputs edge tickets (YAML) describing the observed anomaly, candidates, and a hypothesis. Use when the user wants systematic edge discovery for NEPSE strategy research.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-edge-candidate-agent){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Edge Candidate Agent

---

## 2. Prerequisites

- Full-universe OHLCV via common.nepse.NepseClient
- Python 3.9+ recommended

---

## 3. Quick Start

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/

# Run a specific detector only
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py \
  --detector circuit_day_continuation --output-dir reports/edge_tickets/
```

---

## 4. Workflow

### Step 1: Run

```bash
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py --output-dir reports/edge_tickets/

# Run a specific detector only
python3 skills/nepse-edge-candidate-agent/scripts/scan_edges.py \
  --detector circuit_day_continuation --output-dir reports/edge_tickets/
```

### Step 2: Read tickets

- One YAML per ticket in `reports/edge_tickets/<ticket_id>.yaml`
- Summary JSON: `reports/nepse_edge_tickets_<YYYY-MM-DD>.json`

### Step 3: Combine downstream

- Feed tickets to `nepse-edge-signal-aggregator` to prioritize across detectors
- Feed prioritized signals to `nepse-edge-strategy-designer` for backtestable strategy drafts

---

## 5. Resources

**Scripts:**

- `skills/nepse-edge-candidate-agent/scripts/_path_setup.py`
- `skills/nepse-edge-candidate-agent/scripts/edge_detectors.py`
- `skills/nepse-edge-candidate-agent/scripts/scan_edges.py`
