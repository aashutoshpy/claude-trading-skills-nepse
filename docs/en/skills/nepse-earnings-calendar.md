---
layout: default
title: "Nepse Earnings Calendar"
grand_parent: English
parent: Skill Guides
nav_order: 41
lang_peer: /ja/skills/nepse-earnings-calendar/
permalink: /en/skills/nepse-earnings-calendar/
generated: true
---

# Nepse Earnings Calendar
{: .no_toc }

Generate a NEPSE quarterly-results calendar from the Nepali fiscal year (FY 2082/83) — listed companies must publish unaudited quarterly statements within 30 days of each quarter-end (Ashwin / Poush / Chaitra / Ashadh). Marks the statutory filing window and accepts a user-supplied dividend/report-date CSV to flag company-specific announcements. Use when the user asks "when does X report?", "what quarterly results are coming?", or wants to plan trades around the NEPSE reporting cycle.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/nepse-earnings-calendar){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# NEPSE Earnings Calendar

---

## 2. When to Use

- User asks "when does the next NEPSE quarterly cycle start?"
- User wants to know when X is reporting (with CSV input)
- Planning trades around reporting season
- As a calendar input to `nepse-earnings-trade-analyzer`

---

## 3. Prerequisites

- Reads Nepali FY quarter-ends from config/registry.yaml; Per-company announcement dates from sharesansar/merolagani
- Python 3.9+ recommended

---

## 4. Quick Start

```bash
`announced_at` = actual filing date (past); `expected_at` = anticipated date (future). Either or both.

### Step 2: Run
```

---

## 5. Workflow

### Step 1: Optional — prepare announcement CSV

Maintain `data/nepse_earnings.csv` from sharesansar/merolagani company-announcements feed:

```csv
symbol,quarter,fiscal_year,announced_at,expected_at
NABIL,Q2,2082/83,,2026-02-10
NICA,Q2,2082/83,2026-02-08,
```

`announced_at` = actual filing date (past); `expected_at` = anticipated date (future). Either or both.

### Step 2: Run

```bash
# Default: 4-week forward calendar from today
python3 skills/nepse-earnings-calendar/scripts/generate_calendar.py \
  --output-dir reports/

# With per-company CSV enrichment
python3 skills/nepse-earnings-calendar/scripts/generate_calendar.py \
  --earnings-csv data/nepse_earnings.csv \
  --output-dir reports/

# Custom forward window
python3 skills/nepse-earnings-calendar/scripts/generate_calendar.py \
  --weeks-forward 8 --output-dir reports/
```

### Step 3: Read output

- JSON: `reports/nepse_earnings_calendar_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_earnings_calendar_<YYYY-MM-DD>.md`

---

## 6. Resources

**Scripts:**

- `skills/nepse-earnings-calendar/scripts/_path_setup.py`
- `skills/nepse-earnings-calendar/scripts/calendar_builder.py`
- `skills/nepse-earnings-calendar/scripts/generate_calendar.py`
