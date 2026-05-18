"""Tests for the NEPSE trading calendar."""

from datetime import date, datetime

import pytest

from common.nepse._config import reset_cache
from common.nepse.trading_calendar import NPT, TradingCalendar


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


def cal() -> TradingCalendar:
    return TradingCalendar.load()


# ---- trading days ---------------------------------------------------------


def test_trading_days_are_mon_to_fri():
    c = cal()
    # 2026-05-18 is a Monday; 2026-05-22 is Friday
    assert c.is_trading_day(date(2026, 5, 18)) is True   # Mon
    assert c.is_trading_day(date(2026, 5, 22)) is True   # Fri
    # Saturday + Sunday closed
    assert c.is_trading_day(date(2026, 5, 23)) is False  # Sat
    assert c.is_trading_day(date(2026, 5, 24)) is False  # Sun


def test_sunday_is_NOT_a_trading_day_post_2025_political_change():
    # Regression: before late 2025, NEPSE was Sun-Thu. The plan and
    # config explicitly moved to Mon-Fri. If someone reverts the config,
    # this test catches it.
    c = cal()
    assert c.is_trading_day(date(2026, 5, 24)) is False  # Sunday


def test_next_trading_day_skips_weekend():
    c = cal()
    # Friday 2026-05-22 → next trading day = Monday 2026-05-25
    assert c.next_trading_day(date(2026, 5, 22)) == date(2026, 5, 25)


def test_settlement_t_plus_2_skips_weekend():
    c = cal()
    # Trade on Thursday 2026-05-21 → T+2 lands on Monday 2026-05-25
    # (Friday 22nd + Monday 25th = 2 trading days)
    assert c.settlement_date(date(2026, 5, 21)) == date(2026, 5, 25)


def test_trading_days_between_inclusive():
    c = cal()
    # Mon 2026-05-18 through Fri 2026-05-22 = 5 trading days
    assert c.trading_days_between(date(2026, 5, 18), date(2026, 5, 22)) == 5
    # Includes a weekend
    assert c.trading_days_between(date(2026, 5, 18), date(2026, 5, 25)) == 6


# ---- session hours --------------------------------------------------------


def test_session_open_at_1100_NPT():
    c = cal()
    ts = datetime(2026, 5, 18, 11, 30, tzinfo=NPT)  # Mon 11:30 NPT
    assert c.is_session_open(ts) is True


def test_session_closed_before_1100():
    c = cal()
    ts = datetime(2026, 5, 18, 10, 59, tzinfo=NPT)
    assert c.is_session_open(ts) is False


def test_session_closed_at_1500():
    c = cal()
    ts = datetime(2026, 5, 18, 15, 0, tzinfo=NPT)
    assert c.is_session_open(ts) is False


def test_session_closed_on_weekend():
    c = cal()
    ts = datetime(2026, 5, 23, 12, 0, tzinfo=NPT)  # Sat noon
    assert c.is_session_open(ts) is False


# ---- AMO window (wraps midnight) ------------------------------------------


def test_amo_window_inclusive_of_evening():
    c = cal()
    ts = datetime(2026, 5, 18, 20, 0, tzinfo=NPT)  # 8pm
    assert c.is_amo_window(ts) is True


def test_amo_window_inclusive_of_early_morning():
    c = cal()
    ts = datetime(2026, 5, 19, 5, 0, tzinfo=NPT)  # 5am next day
    assert c.is_amo_window(ts) is True


def test_amo_window_excludes_session_hours():
    c = cal()
    ts = datetime(2026, 5, 18, 12, 0, tzinfo=NPT)  # noon
    assert c.is_amo_window(ts) is False


# ---- circuit breaker ------------------------------------------------------


def test_first_session_5pct_triggers_15min_halt():
    c = cal()
    ts = datetime(2026, 5, 18, 12, 0, tzinfo=NPT)  # in 11-13 window
    cb = c.circuit_breaker_for(ts, 5.5)
    assert cb is not None
    assert cb.action == "halt_15min"


def test_second_session_5pct_does_NOT_trigger_5pct_halt():
    c = cal()
    ts = datetime(2026, 5, 18, 14, 0, tzinfo=NPT)  # in 13-15 window
    # 5% in second half is below the 8% close threshold
    assert c.circuit_breaker_for(ts, 5.5) is None


def test_second_session_8pct_closes_market():
    c = cal()
    ts = datetime(2026, 5, 18, 14, 0, tzinfo=NPT)
    cb = c.circuit_breaker_for(ts, -8.1)
    assert cb is not None
    assert cb.action == "close_for_day"


def test_naive_datetime_rejected():
    c = cal()
    with pytest.raises(ValueError):
        c.is_session_open(datetime(2026, 5, 18, 12, 0))  # no tzinfo
    with pytest.raises(ValueError):
        c.is_amo_window(datetime(2026, 5, 18, 12, 0))
    with pytest.raises(ValueError):
        c.circuit_breaker_for(datetime(2026, 5, 18, 12, 0), 5.0)


# ---- short selling --------------------------------------------------------


def test_short_selling_is_disabled():
    c = cal()
    assert c.short_selling_enabled is False
