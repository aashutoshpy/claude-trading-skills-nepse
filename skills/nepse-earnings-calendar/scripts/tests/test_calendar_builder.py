"""Tests for the NEPSE earnings calendar builder."""

from datetime import date

import pytest
from calendar_builder import (
    build_calendar,
    build_quarter_windows,
    parse_earnings_csv,
)

from common.nepse._config import reset_cache
from common.nepse.registry import Registry


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def registry():
    return Registry.load()


# ---- quarter windows ----------------------------------------------------


def test_q3_window_in_horizon_in_may(registry):
    # Q3 ends ~2026-04-13 → filing deadline ~2026-05-13.
    # As-of 2026-05-17 with 4-week window covers 2026-04-19 through 2026-06-14.
    windows = build_quarter_windows(registry, today=date(2026, 5, 17), weeks_forward=4)
    quarters = {w.quarter for w in windows}
    assert 3 in quarters


def test_audited_q4_flagged_correctly(registry):
    # Q4 ends ~2026-07-16 → 120-day window deadline ~2026-11-13
    windows = build_quarter_windows(
        registry, today=date(2026, 11, 10), weeks_forward=8
    )
    q4 = next((w for w in windows if w.quarter == 4), None)
    assert q4 is not None
    assert q4.is_audited is True


def test_no_windows_when_horizon_is_empty(registry):
    # As-of date long after all FY 2082/83 deadlines
    windows = build_quarter_windows(
        registry, today=date(2027, 6, 1), weeks_forward=4
    )
    assert windows == []


# ---- CSV parsing --------------------------------------------------------


def test_parse_csv_with_announced_and_expected():
    csv = (
        "symbol,quarter,fiscal_year,announced_at,expected_at\n"
        "NABIL,Q2,2082/83,,2026-02-10\n"
        "NICA,Q2,2082/83,2026-02-08,\n"
    )
    rows = parse_earnings_csv(csv)
    by_sym = {r.symbol: r for r in rows}
    assert by_sym["NABIL"].expected_at == date(2026, 2, 10)
    assert by_sym["NABIL"].announced_at is None
    assert by_sym["NICA"].announced_at == date(2026, 2, 8)


def test_parse_csv_skips_empty_symbol():
    csv = "symbol,quarter,fiscal_year,announced_at,expected_at\n,Q1,2082/83,,2026-11-01\n"
    rows = parse_earnings_csv(csv)
    assert rows == []


def test_parse_csv_handles_bad_dates_as_none():
    csv = "symbol,quarter,fiscal_year,announced_at,expected_at\nNABIL,Q2,2082/83,not-a-date,2026-02-10\n"
    rows = parse_earnings_csv(csv)
    assert rows[0].announced_at is None
    assert rows[0].expected_at == date(2026, 2, 10)


# ---- build_calendar -----------------------------------------------------


def test_build_calendar_with_no_csv(registry):
    r = build_calendar(registry, today=date(2026, 5, 17), weeks_forward=4)
    assert r.company_rows == []
    assert len(r.quarter_windows) >= 1


def test_build_calendar_filters_company_rows_to_horizon(registry):
    csv = (
        "symbol,quarter,fiscal_year,announced_at,expected_at\n"
        "INHORIZON,Q3,2082/83,,2026-05-25\n"
        "FAR_FUTURE,Q4,2082/83,,2027-01-01\n"
    )
    rows = parse_earnings_csv(csv)
    r = build_calendar(registry, today=date(2026, 5, 17), weeks_forward=4, company_rows=rows)
    symbols = {row.symbol for row in r.company_rows}
    assert "INHORIZON" in symbols
    assert "FAR_FUTURE" not in symbols


def test_build_calendar_sorts_company_rows_chronologically(registry):
    csv = (
        "symbol,quarter,fiscal_year,announced_at,expected_at\n"
        "LATE,Q3,2082/83,,2026-06-05\n"
        "EARLY,Q3,2082/83,,2026-05-20\n"
    )
    rows = parse_earnings_csv(csv)
    r = build_calendar(registry, today=date(2026, 5, 17), weeks_forward=8, company_rows=rows)
    assert [row.symbol for row in r.company_rows] == ["EARLY", "LATE"]
