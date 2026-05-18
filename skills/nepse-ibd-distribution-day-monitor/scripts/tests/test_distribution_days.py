"""Tests for the NEPSE IBD distribution day detector."""

from datetime import date, timedelta

from distribution_days import detect_distribution_days

from common.nepse.client import Ohlcv


def _bar(day: date, close: float, volume: int) -> Ohlcv:
    return Ohlcv(day=day, open=close, high=close + 0.5, low=close - 0.5,
                 close=close, volume=volume)


def _build_index_bars(closes: list[float], volumes: list[int], d0: date = date(2025, 1, 1)) -> list:
    assert len(closes) == len(volumes)
    return [_bar(d0 + timedelta(days=i), c, v) for i, (c, v) in enumerate(zip(closes, volumes))]


def test_empty_returns_unknown():
    r = detect_distribution_days([])
    assert r.severity == "UNKNOWN"
    assert r.active_count == 0


def test_insufficient_history_returns_unknown():
    bars = _build_index_bars([100.0] * 20, [1000] * 20)
    r = detect_distribution_days(bars, window=25)
    assert r.severity == "UNKNOWN"


def test_no_distribution_when_volume_lower_on_down_day():
    # Down day but lower volume → not a distribution day
    closes = [100.0] * 25 + [99.5]
    volumes = [1000] * 25 + [500]
    bars = _build_index_bars(closes, volumes)
    r = detect_distribution_days(bars, window=25)
    assert r.active_count == 0
    assert r.severity == "HEALTHY"


def test_distribution_day_detected_when_volume_higher():
    # Day 25 drops -1% on higher volume
    closes = [100.0] * 25 + [99.0]
    volumes = [1000] * 25 + [1500]
    bars = _build_index_bars(closes, volumes)
    r = detect_distribution_days(bars, window=25)
    assert r.active_count == 1
    assert r.distribution_days[0].pct_change == -1.0
    assert r.distribution_days[0].volume_ratio == 1.5


def test_severity_classification():
    # Build 5 distribution days within the window
    closes = []
    volumes = []
    prev_close = 100.0
    prev_volume = 1000
    closes.append(prev_close)
    volumes.append(prev_volume)
    for _ in range(25):
        new_close = prev_close * 0.99   # -1% each day
        new_volume = prev_volume + 100   # always higher than prior
        closes.append(new_close)
        volumes.append(new_volume)
        prev_close, prev_volume = new_close, new_volume
    bars = _build_index_bars(closes, volumes)
    r = detect_distribution_days(bars, window=25, rally_cancel_pct=100.0)
    # 25 distribution days; severity == DISTRIBUTION
    assert r.active_count == 25
    assert r.severity == "DISTRIBUTION"


def test_rally_cancels_distribution_day():
    # Day 25 is a d-day (-1% on higher vol). Day 26 rallies +6% (cancels).
    closes = [100.0] * 24 + [100.0, 99.0, 105.0]  # 27 bars
    volumes = [1000] * 24 + [1000, 1500, 2000]
    bars = _build_index_bars(closes, volumes)
    r = detect_distribution_days(bars, window=25, rally_cancel_pct=5.0)
    assert any(d.cancelled for d in r.distribution_days)
    assert r.active_count < len(r.distribution_days)


def test_min_down_pct_threshold():
    # Day 25 closes -0.1% — below default 0.2% threshold; not a d-day
    closes = [100.0] * 25 + [99.9]
    volumes = [1000] * 25 + [2000]
    bars = _build_index_bars(closes, volumes)
    r = detect_distribution_days(bars, window=25, min_down_pct=0.2)
    assert r.active_count == 0
    # But with min_down_pct=0.05, it counts
    r2 = detect_distribution_days(bars, window=25, min_down_pct=0.05)
    assert r2.active_count == 1
