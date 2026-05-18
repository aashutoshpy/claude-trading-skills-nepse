"""Tests for the NEPSE uptrend calculator."""

from datetime import date, timedelta

from uptrend_calculator import build_result, compute_uptrend_series, detect_divergence

from common.nepse.client import Ohlcv


def _series(days: int, start: float, slope: float, d0: date = date(2025, 1, 1)) -> list[Ohlcv]:
    return [
        Ohlcv(day=d0 + timedelta(days=i), open=start + slope * i, high=start + slope * i + 0.5,
              low=start + slope * i - 0.5, close=start + slope * i, volume=10_000)
        for i in range(days)
    ]


def test_all_rising_universe_yields_100pct():
    bars = {f"R{i}": _series(260, 100, 0.5) for i in range(5)}
    series = compute_uptrend_series(bars, history_days=10)
    assert all(p.ratio == 100.0 for p in series)


def test_all_falling_universe_yields_0pct():
    bars = {f"F{i}": _series(260, 200, -0.5) for i in range(5)}
    series = compute_uptrend_series(bars, history_days=10)
    assert all(p.ratio == 0.0 for p in series)


def test_mixed_universe_yields_ratio_between_0_and_100():
    bars = {
        **{f"R{i}": _series(260, 100, 0.5) for i in range(3)},
        **{f"F{i}": _series(260, 200, -0.5) for i in range(2)},
    }
    series = compute_uptrend_series(bars, history_days=10)
    last = series[-1]
    assert last.ratio == 60.0   # 3 of 5 above
    assert last.eligible == 5


def test_short_history_names_excluded():
    bars = {
        "LONG": _series(260, 100, 0.5),
        "SHORT": _series(50, 100, 0.5),    # only 50 days
    }
    series = compute_uptrend_series(bars, history_days=10)
    assert series[-1].eligible == 1   # only LONG


def test_regime_classification_in_build_result():
    bars = {f"R{i}": _series(260, 100, 0.5) for i in range(10)}
    r = build_result(bars, today=date(2026, 5, 17), history_days=5)
    assert r.regime == "STRONG_UPTREND"
    assert r.current_ratio == 100.0


def test_regime_neutral_when_mixed():
    bars = {
        **{f"R{i}": _series(260, 100, 0.5) for i in range(2)},
        **{f"F{i}": _series(260, 200, -0.5) for i in range(3)},
    }
    r = build_result(bars, today=date(2026, 5, 17), history_days=5)
    assert r.regime == "NEUTRAL"
    assert r.current_ratio == 40.0


# ---- divergence ----------------------------------------------------------


def test_no_divergence_when_index_and_ratio_aligned():
    bars = {f"R{i}": _series(260, 100, 0.5) for i in range(5)}
    series = compute_uptrend_series(bars, history_days=30)
    # Mock index aligned with ratio: rising
    index = _series(260, 1000, 1.0)
    flag, note = detect_divergence(series, index_series=index, lookback=20)
    assert flag is False


def test_bearish_divergence_detected():
    # Setup: ratio was high earlier in the lookback window but is low now.
    # A flat index gives every day the same close — max() picks the earliest
    # day (when ratio was high). Current close equals that "high" close, so
    # the divergence condition (near-high index + falling ratio) fires.
    bars = {f"R{i}": _series(260, 100, 0.5) for i in range(5)}
    series = compute_uptrend_series(bars, history_days=30)
    n = len(series)
    for i, p in enumerate(series):
        p.ratio = 80.0 if i < n - 5 else 50.0
    d0 = series[0].day
    flat_index = [
        Ohlcv(day=d0 + timedelta(days=i), open=1000.0, high=1000.5, low=999.5,
              close=1000.0, volume=10_000)
        for i in range(n)
    ]
    flag, note = detect_divergence(series, index_series=flat_index, lookback=n)
    assert flag is True, f"expected divergence; note={note}"
    assert "divergence" in note.lower()


def test_divergence_returns_false_when_insufficient_overlap():
    series = compute_uptrend_series({"R": _series(260, 100, 0.5)}, history_days=5)
    # Index series has no overlapping days
    index = _series(10, 1000, 1.0, d0=date(2030, 1, 1))
    flag, note = detect_divergence(series, index_series=index, lookback=20)
    assert flag is False
