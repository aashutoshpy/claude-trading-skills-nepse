"""Tests for the NEPSE downtrend detector."""

from datetime import date, timedelta

from downtrend_detector import detect_drawdowns, summarize

from common.nepse.client import Ohlcv


def _bar(day: date, close: float) -> Ohlcv:
    return Ohlcv(day=day, open=close, high=close + 0.5, low=close - 0.5,
                 close=close, volume=10_000)


def _series_from_closes(closes: list[float], d0: date = date(2025, 1, 1)) -> list[Ohlcv]:
    return [_bar(d0 + timedelta(days=i), c) for i, c in enumerate(closes)]


# ---- detection -----------------------------------------------------------


def test_empty_returns_empty():
    assert detect_drawdowns([]) == []


def test_pure_uptrend_no_drawdowns():
    closes = [100 + i * 1.0 for i in range(100)]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    assert drawdowns == []


def test_below_threshold_drawdown_excluded():
    # Peak 100, trough 95 (-5%), recover to 100 — below 10% threshold
    closes = [100] * 5 + [97, 96, 95, 96, 97, 100]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    assert drawdowns == []


def test_completed_drawdown_with_recovery():
    # Peak 100, trough 85 (-15%), recover to 102
    closes = [100, 95, 90, 85, 90, 95, 100, 102]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    assert len(drawdowns) == 1
    d = drawdowns[0]
    assert d.peak_close == 100
    assert d.trough_close == 85
    assert d.depth_pct == -15.0
    assert d.recovery_date is not None
    assert d.total_days is not None


def test_in_progress_drawdown_no_recovery():
    closes = [100, 95, 90, 85, 80, 78]   # still declining
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    assert len(drawdowns) == 1
    d = drawdowns[0]
    assert d.recovery_date is None
    assert d.trough_close == 78


def test_trough_updates_on_new_low():
    # Peak 100, low to 85, brief bounce to 88, lower low to 80, then recover
    closes = [100, 90, 85, 88, 80, 95, 102]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    d = drawdowns[0]
    assert d.trough_close == 80


def test_multiple_drawdowns_separated_by_new_high():
    # Drawdown 1: peak 100 → 85 → 102 (recover)
    # Drawdown 2: peak 102 → 85 → 105 (recover)
    closes = [100, 90, 85, 95, 102,
              98, 90, 85, 95, 105]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    assert len(drawdowns) == 2
    assert all(d.recovery_date is not None for d in drawdowns)


# ---- summarize ----------------------------------------------------------


def test_summary_distribution_metrics():
    # 3 completed drawdowns with declines of 3, 5, 7 days
    closes = [
        100, 95, 90, 85, 95, 100, 102,                 # decline 3
        98, 95, 90, 87, 85, 90, 95, 100, 105,          # decline 5
        100, 95, 90, 85, 82, 80, 78, 76, 85, 95, 110,  # decline 7
    ]
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    s = summarize(drawdowns)
    assert s.historical_count == 3
    assert s.decline_days_median is not None
    assert s.decline_days_max == max(d.decline_days for d in drawdowns)


def test_summary_includes_in_progress():
    closes = [100, 95, 90, 85, 80]   # still declining
    drawdowns = detect_drawdowns(_series_from_closes(closes), min_depth_pct=10.0)
    s = summarize(drawdowns)
    assert s.in_progress is not None
    assert s.historical_count == 0


def test_summary_empty_metrics_for_no_drawdowns():
    s = summarize([])
    assert s.historical_count == 0
    assert s.decline_days_median is None
    assert s.in_progress is None
