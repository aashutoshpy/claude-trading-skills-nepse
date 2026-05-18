"""Tests for the NEPSE VCP detector.

Synthetic OHLCV: we construct bar sequences with known properties
(Stage 2 uptrend with narrowing contractions vs. flat / broken)
so the detector's behavior is deterministic.
"""

from datetime import date, timedelta

from vcp_detector import VcpParameters, detect_vcp

from common.nepse.client import Ohlcv


def _bar(day: date, open_: float, high: float, low: float, close: float, volume: int = 10_000) -> Ohlcv:
    return Ohlcv(day=day, open=open_, high=high, low=low, close=close, volume=volume)


def _make_uptrend(days: int, start: float = 100.0, slope: float = 0.4) -> list[Ohlcv]:
    """Deterministic Stage-2 uptrend: linear rise + small intraday range."""
    bars = []
    d0 = date(2025, 1, 1)
    for i in range(days):
        close = start + slope * i
        bars.append(_bar(d0 + timedelta(days=i), open_=close - 0.2, high=close + 0.3, low=close - 0.3, close=close))
    return bars


def _append_vcp_base(
    base_start_close: float,
    contractions_pct: list[float],
    *,
    days_per_leg: int = 6,
    start_day: date,
    volume: int = 10_000,
) -> list[Ohlcv]:
    """Append a realistic VCP base.

    `contractions_pct` is oldest-first. A real VCP has:
      - A roughly fixed pivot level (each swing high near the same price)
      - Ascending swing lows (each low higher than the previous low — base
        is "tightening upward", not collapsing downward)
      - Narrowing legs when read oldest→newest

    For each contraction p[i]:
        swing_high_i = pivot                        (each high touches resistance)
        swing_low_i  = pivot * (1 - p[i] / 100)     (low is p% below pivot)

    The final approach rises from the last swing low back toward the pivot.
    """
    bars: list[Ohlcv] = []
    day_cursor = start_day
    pivot = base_start_close * 1.05            # pivot just above current price
    last_close = base_start_close

    for pct in contractions_pct:
        # rise to the pivot (swing high)
        for i in range(days_per_leg):
            close = last_close + (pivot - last_close) * (i + 1) / days_per_leg
            bars.append(_bar(day_cursor, close - 0.2, close + 0.3, close - 0.3, close, volume))
            day_cursor += timedelta(days=1)
        # fall to the swing low (p% below pivot)
        swing_low = pivot * (1.0 - pct / 100.0)
        for i in range(days_per_leg):
            close = pivot - (pivot - swing_low) * (i + 1) / days_per_leg
            bars.append(_bar(day_cursor, close + 0.2, close + 0.2, close - 0.3, close, volume))
            day_cursor += timedelta(days=1)
        last_close = swing_low

    # final approach: rise from last swing low back to ~98% of pivot
    target = pivot * 0.98
    for i in range(days_per_leg):
        close = last_close + (target - last_close) * (i + 1) / days_per_leg
        bars.append(_bar(day_cursor, close - 0.2, close + 0.2, close - 0.2, close, volume))
        day_cursor += timedelta(days=1)
    return bars


# ---- stage-2 gate ---------------------------------------------------------


def test_detect_empty_bars_returns_invalid():
    r = detect_vcp([])
    assert r.valid_vcp is False
    assert "no bars" in r.reasons


def test_short_history_rejected_as_not_stage2():
    bars = _make_uptrend(50)
    r = detect_vcp(bars)
    assert r.valid_vcp is False
    assert r.contractions == 0


def test_flat_price_history_not_stage2():
    flat = [_bar(date(2025, 1, 1) + timedelta(days=i), 100, 100.5, 99.5, 100) for i in range(260)]
    r = detect_vcp(flat)
    assert r.valid_vcp is False


# ---- VCP detection on synthetic uptrend + base ---------------------------


def test_valid_vcp_with_narrowing_contractions():
    bars = _make_uptrend(240, start=80.0, slope=0.4)
    bars += _append_vcp_base(
        base_start_close=bars[-1].close,
        contractions_pct=[12.0, 8.0, 4.0],
        days_per_leg=4,
        start_day=bars[-1].day + timedelta(days=1),
    )
    r = detect_vcp(bars, VcpParameters(min_contractions=3, max_final_contraction_pct=6.0))
    assert r.valid_vcp, f"expected valid VCP; reasons={r.reasons}"
    assert r.contractions >= 3
    assert r.final_contraction_pct is not None and r.final_contraction_pct <= 6.0
    assert r.composite_score >= 60


def test_non_narrowing_contractions_invalid_but_scored():
    # Contractions get wider, not narrower
    bars = _make_uptrend(240, start=80.0, slope=0.4)
    bars += _append_vcp_base(
        base_start_close=bars[-1].close,
        contractions_pct=[4.0, 8.0, 12.0],
        days_per_leg=4,
        start_day=bars[-1].day + timedelta(days=1),
    )
    r = detect_vcp(bars, VcpParameters(min_contractions=3, max_final_contraction_pct=6.0))
    assert r.valid_vcp is False
    assert any("not narrowing" in s for s in r.reasons)


def test_low_volume_invalidates_otherwise_good_pattern():
    bars = _make_uptrend(240, start=80.0, slope=0.4)
    bars += _append_vcp_base(
        base_start_close=bars[-1].close,
        contractions_pct=[12.0, 8.0, 4.0],
        days_per_leg=4,
        start_day=bars[-1].day + timedelta(days=1),
        volume=100,  # well under default 5,000 min
    )
    r = detect_vcp(bars, VcpParameters(min_contractions=3, max_final_contraction_pct=6.0))
    assert r.valid_vcp is False
    assert any("avg volume" in s for s in r.reasons)


def test_final_contraction_over_threshold_invalid():
    bars = _make_uptrend(240, start=80.0, slope=0.4)
    bars += _append_vcp_base(
        base_start_close=bars[-1].close,
        contractions_pct=[14.0, 12.0, 10.0],   # narrowing but final = 10% > 6%
        days_per_leg=4,
        start_day=bars[-1].day + timedelta(days=1),
    )
    r = detect_vcp(bars, VcpParameters(min_contractions=3, max_final_contraction_pct=6.0))
    assert r.valid_vcp is False
    assert any("final contraction" in s for s in r.reasons)


# ---- parameter knobs ------------------------------------------------------


def test_relaxing_min_contractions_accepts_two_legs():
    bars = _make_uptrend(240, start=80.0, slope=0.4)
    bars += _append_vcp_base(
        base_start_close=bars[-1].close,
        contractions_pct=[8.0, 4.0],
        days_per_leg=4,
        start_day=bars[-1].day + timedelta(days=1),
    )
    r2 = detect_vcp(bars, VcpParameters(min_contractions=2))
    assert r2.valid_vcp
    r3 = detect_vcp(bars, VcpParameters(min_contractions=3))
    assert r3.valid_vcp is False
