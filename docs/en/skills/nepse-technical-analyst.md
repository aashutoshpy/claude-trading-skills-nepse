---
layout: default
title: "Nepse Technical Analyst"
grand_parent: English
parent: Skill Guides
nav_order: 55
lang_peer: /ja/skills/nepse-technical-analyst/
permalink: /en/skills/nepse-technical-analyst/
generated: true
---

# Nepse Technical Analyst
{: .no_toc }

Analyze NEPSE (Nepal Stock Exchange) stock charts from screenshots. Read price action, identify trend stage (Wyckoff / Stage Analysis), find support/resistance, evaluate breakout/breakdown setups, and call out NEPSE-specific microstructure quirks (15% daily band, circuit-hit days, low-liquidity gaps, T+2 settlement). Use when the user uploads a NEPSE chart screenshot and asks for technical analysis. NOT for US stocks — use technical-analyst instead.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-technical-analyst){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Technical Analyst

---

## 2. When to Use

- User uploads a NEPSE stock chart (weekly, daily, or intraday) and asks for analysis
- User asks for NEPSE-specific pattern interpretation (e.g., "is this a Stage 2 breakout?")
- User wants to confirm a screener candidate from `nepse-vcp-screener` or `nepse-sector-analyst`

---

## 3. Prerequisites

- User provides chart screenshot
- Python 3.9+ recommended

---

## 4. Quick Start

Invoke this skill by describing your analysis needs to Claude.

---

## 5. Workflow

See the skill's SKILL.md for the complete workflow.

---

## 6. Resources

**References:**

- `skills/nepse-technical-analyst/references/nepse_chart_quirks.md`
- `skills/nepse-technical-analyst/references/stage_analysis_quick_reference.md`
