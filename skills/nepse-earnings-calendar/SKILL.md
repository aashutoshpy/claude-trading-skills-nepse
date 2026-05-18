---
name: nepse-earnings-calendar
description: Generate a NEPSE quarterly-results calendar from the Nepali fiscal year (FY 2082/83) — listed companies must publish unaudited quarterly statements within 30 days of each quarter-end (Ashwin / Poush / Chaitra / Ashadh). Marks the statutory filing window and accepts a user-supplied dividend/report-date CSV to flag company-specific announcements. Use when the user asks "when does X report?", "what quarterly results are coming?", or wants to plan trades around the NEPSE reporting cycle.
---

# NEPSE Earnings Calendar

NEPSE companies report quarterly per the Nepali fiscal year (Shrawan→Ashadh). SEBON requires unaudited quarterly statements within ~30 days of each quarter-end. There is no machine-readable feed of per-company filing dates, so this skill:

1. Generates the statutory filing window for each Nepali FY quarter (from `config/registry.yaml`)
2. Optionally enriches with a user-supplied CSV of known announcement dates

## When to Use

- User asks "when does the next NEPSE quarterly cycle start?"
- User wants to know when X is reporting (with CSV input)
- Planning trades around reporting season
- As a calendar input to `nepse-earnings-trade-analyzer`

## Nepali FY 2082/83 quarter-ends (verified)

| Quarter | Ends (Nepali) | Ends (Gregorian) | Statutory filing deadline (T+30) |
|---|---|---|---|
| Q1 | Ashwin | ~2025-10-17 | ~2025-11-16 |
| Q2 | Poush | ~2026-01-14 | ~2026-02-13 |
| Q3 | Chaitra | ~2026-04-13 | ~2026-05-13 |
| Q4 (audited) | Ashadh | ~2026-07-16 | annual report by Mangsir (~Nov) |

Quarters Q1-Q3 are unaudited; Q4 = full-year audited report (longer window).

## Workflow

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

## Output

Quarterly windows always appear. Per-company rows appear only if the CSV provides them.

## Limitations

- No machine-readable filing-date feed for NEPSE; the per-company calendar is only as complete as the user's CSV.
- Audited Q4 reports often slip the statutory November deadline; treat the deadline as guidance, not certainty.
- The Bikram Sambat → Gregorian conversion uses the values seeded in `config/registry.yaml`. When BS→Gregorian shifts (rarely, but possible for FY edge cases), edit the YAML.
