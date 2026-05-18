---
layout: default
title: "Nepse Margin Eligibility"
grand_parent: English
parent: Skill Guides
nav_order: 49
lang_peer: /ja/skills/nepse-margin-eligibility/
permalink: /en/skills/nepse-margin-eligibility/
generated: true
---

# Nepse Margin Eligibility
{: .no_toc }

Check whether a NEPSE ticker is on the 123-name margin-eligible list (live since April 2026), report initial/maintenance margin requirements (30%/20%), and compute margin-call distance for a given position. Use when the user asks "can I trade X on margin?", needs to know how close a margin position is to a margin call, or is reviewing portfolio risk for leveraged names.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-margin-eligibility){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Margin Eligibility

---

## 2. When to Use

- User asks "can I trade <ticker> on margin?"
- User asks "how close to a margin call is my position?"
- Before sizing a position you intend to lever
- Cross-reference from `nepse-portfolio-tracker` to flag positions using margin
- Cross-reference from `nepse-vcp-screener` candidates list to know which can be leveraged

---

## 3. Prerequisites

- Reads config/nepse_rules.yaml + config/registry.yaml
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
# Single ticker
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL

# Multiple tickers
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL UPPER NICA
```

---

## 5. Workflow

### Step 1: Check eligibility

```bash
# Single ticker
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL

# Multiple tickers
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL UPPER NICA
```

Output:
```
NABIL: ELIGIBLE   initial=30%   maintenance=20%
UPPER: ELIGIBLE   initial=30%   maintenance=20%
NICA: NOT_ELIGIBLE
```

### Step 2: Compute margin-call distance for a position

```bash
python3 skills/nepse-margin-eligibility/scripts/check_margin.py NABIL \
  --entry-price 1245.00 \
  --shares 100 \
  --margin-pct 30 \
  --current-price 1180.00
```

Output:
```
NABIL: ELIGIBLE   position cost=NPR 124,500   borrowed=NPR 87,150   equity=NPR 37,350
Current equity (at NPR 1,180.00): NPR 30,850
Margin call triggered below: NPR 1,089.38   (-12.5% from current)
```

---

## 6. Resources

**Scripts:**

- `skills/nepse-margin-eligibility/scripts/_path_setup.py`
- `skills/nepse-margin-eligibility/scripts/check_margin.py`
- `skills/nepse-margin-eligibility/scripts/margin_calculator.py`
