"""Pure-functional NEPSE earnings calendar builder.

Combines statutory FY quarter windows (from `Registry`) with optional
per-company announcement rows (user CSV).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import StringIO

import _path_setup  # noqa: F401

from common.nepse.registry import Registry

# SEBON statutory filing window for unaudited quarterly statements
DEFAULT_FILING_WINDOW_DAYS = 30


@dataclass
class QuarterWindow:
    fy: str
    quarter: int
    ends_on: date
    filing_deadline: date
    is_audited: bool        # True for Q4


@dataclass
class CompanyEarning:
    symbol: str
    quarter: str
    fiscal_year: str
    announced_at: date | None
    expected_at: date | None


@dataclass
class CalendarResult:
    as_of: date
    weeks_forward: int
    quarter_windows: list[QuarterWindow] = field(default_factory=list)
    company_rows: list[CompanyEarning] = field(default_factory=list)


def build_quarter_windows(
    registry: Registry,
    *,
    today: date,
    weeks_forward: int = 4,
    filing_window_days: int = DEFAULT_FILING_WINDOW_DAYS,
) -> list[QuarterWindow]:
    """Return upcoming/recent quarter windows whose filing-deadline is within ±weeks_forward weeks of today.

    Includes the previous quarter if its filing deadline has only just passed
    (still relevant for trade-around-results plays).
    """
    horizon_start = today - timedelta(weeks=4)
    horizon_end = today + timedelta(weeks=weeks_forward)
    out: list[QuarterWindow] = []
    fy = registry.fiscal_year_label
    for q_idx, gregorian_iso in registry.fiscal_quarter_ends:
        try:
            ends_on = date.fromisoformat(gregorian_iso)
        except ValueError:
            continue
        # Q4 is audited and gets a longer (annual) window — give it ~120d
        is_audited = q_idx == 4
        window = 120 if is_audited else filing_window_days
        deadline = ends_on + timedelta(days=window)
        if horizon_start <= deadline <= horizon_end:
            out.append(
                QuarterWindow(
                    fy=fy,
                    quarter=q_idx,
                    ends_on=ends_on,
                    filing_deadline=deadline,
                    is_audited=is_audited,
                )
            )
    return out


def parse_earnings_csv(text: str) -> list[CompanyEarning]:
    out: list[CompanyEarning] = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        sym = (row.get("symbol") or "").strip().upper()
        if not sym:
            continue
        ann = _parse_date(row.get("announced_at"))
        exp = _parse_date(row.get("expected_at"))
        out.append(
            CompanyEarning(
                symbol=sym,
                quarter=(row.get("quarter") or "").strip(),
                fiscal_year=(row.get("fiscal_year") or "").strip(),
                announced_at=ann,
                expected_at=exp,
            )
        )
    return out


def _parse_date(value: str | None) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def build_calendar(
    registry: Registry,
    *,
    today: date,
    weeks_forward: int = 4,
    company_rows: list[CompanyEarning] | None = None,
    filing_window_days: int = DEFAULT_FILING_WINDOW_DAYS,
) -> CalendarResult:
    """Top-level: combine statutory windows + optional company rows."""
    windows = build_quarter_windows(
        registry, today=today, weeks_forward=weeks_forward,
        filing_window_days=filing_window_days,
    )
    rows: list[CompanyEarning] = []
    if company_rows:
        horizon_end = today + timedelta(weeks=weeks_forward)
        for r in company_rows:
            ref = r.expected_at or r.announced_at
            if ref is None:
                continue
            if today - timedelta(weeks=4) <= ref <= horizon_end:
                rows.append(r)
    rows.sort(key=lambda r: r.expected_at or r.announced_at or date.max)
    return CalendarResult(
        as_of=today,
        weeks_forward=weeks_forward,
        quarter_windows=windows,
        company_rows=rows,
    )
