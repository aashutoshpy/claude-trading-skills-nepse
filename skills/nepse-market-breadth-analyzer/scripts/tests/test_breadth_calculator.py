"""Tests for the NEPSE breadth calculator."""

from datetime import date, timedelta

from breadth_calculator import BreadthInputs, compute_breadth

from common.nepse.client import Ohlcv, Security


def _bar(day: date, close: float) -> Ohlcv:
    return Ohlcv(day=day, open=close, high=close + 0.5, low=close - 0.5, close=close, volume=10_000)


def _sec(symbol: str, sector_id: str = "BANKING") -> Security:
    return Security(symbol=symbol, name=symbol, sector_id=sector_id)


def _rising_series(days: int, start: float, slope: float) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [_bar(d0 + timedelta(days=i), start + slope * i) for i in range(days)]


def _flat_series(days: int, level: float) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [_bar(d0 + timedelta(days=i), level) for i in range(days)]


def _falling_series(days: int, start: float, slope: float) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [_bar(d0 + timedelta(days=i), start - slope * i) for i in range(days)]


# ---- empty / no-data cases ------------------------------------------------


def test_empty_universe():
    r = compute_breadth([], as_of="2026-05-17")
    assert r.total_universe == 0
    assert r.regime == "UNKNOWN"


def test_filters_out_short_history():
    inputs = [BreadthInputs(_sec("A"), _rising_series(50, 100, 0.4))]
    r = compute_breadth(inputs, as_of="2026-05-17", min_trading_days=150)
    assert r.eligible == 0


# ---- A/D counting ---------------------------------------------------------


def test_advances_and_declines_counted():
    rising = _rising_series(260, 100, 0.4)
    falling = _falling_series(260, 200, 0.4)
    flat = _flat_series(260, 50)
    inputs = [
        BreadthInputs(_sec("RISE"), rising),
        BreadthInputs(_sec("FALL"), falling),
        BreadthInputs(_sec("FLAT"), flat),
    ]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.advances == 1
    assert r.declines == 1
    assert r.unchanged == 1
    assert r.ad_ratio == 1.0


def test_ad_ratio_when_no_declines():
    inputs = [BreadthInputs(_sec(f"R{i}"), _rising_series(260, 100, 0.4)) for i in range(3)]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.advances == 3
    assert r.declines == 0
    assert r.ad_ratio == 999.0


# ---- SMA calculations -----------------------------------------------------


def test_pct_above_50_and_200_sma_for_rising_universe():
    inputs = [BreadthInputs(_sec(f"R{i}"), _rising_series(260, 100, 0.4)) for i in range(10)]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.pct_above_50sma == 100.0
    assert r.pct_above_200sma == 100.0
    assert r.regime == "BULL_BROAD"


def test_pct_above_for_falling_universe():
    inputs = [BreadthInputs(_sec(f"F{i}"), _falling_series(260, 200, 0.4)) for i in range(10)]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.pct_above_50sma == 0.0
    assert r.pct_above_200sma == 0.0
    assert r.regime in ("BEAR_BROAD", "BEAR_NARROW")


# ---- regime classification -----------------------------------------------


def test_regime_neutral_when_mixed():
    # ~50% above each SMA → NEUTRAL
    rising = [BreadthInputs(_sec(f"R{i}"), _rising_series(260, 100, 0.4)) for i in range(5)]
    falling = [BreadthInputs(_sec(f"F{i}"), _falling_series(260, 200, 0.4)) for i in range(5)]
    r = compute_breadth(rising + falling, as_of="2026-05-17")
    assert r.regime == "NEUTRAL"


# ---- new high/low ---------------------------------------------------------


def test_new_52w_high_detected_for_rising():
    inputs = [BreadthInputs(_sec("RISE"), _rising_series(260, 100, 0.4))]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.new_52w_highs == 1
    assert r.new_52w_lows == 0


def test_new_52w_low_detected_for_falling():
    inputs = [BreadthInputs(_sec("FALL"), _falling_series(260, 200, 0.4))]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.new_52w_lows == 1


# ---- sector breakdown -----------------------------------------------------


def test_sector_breakdown_aggregates_per_sector():
    inputs = [
        BreadthInputs(_sec("BANK1", "BANKING"), _rising_series(260, 100, 0.4)),
        BreadthInputs(_sec("BANK2", "BANKING"), _rising_series(260, 100, 0.4)),
        BreadthInputs(_sec("HYDRO1", "HYDROPOWER"), _falling_series(260, 200, 0.4)),
    ]
    r = compute_breadth(inputs, as_of="2026-05-17")
    assert r.sector_breakdown["BANKING"]["advances"] == 2
    assert r.sector_breakdown["BANKING"]["declines"] == 0
    assert r.sector_breakdown["HYDROPOWER"]["declines"] == 1
