"""Tests for the NEPSE post-result earnings scorer."""

from datetime import date, timedelta

from earnings_scorer import score_earnings

from common.nepse.client import Ohlcv


def _bar(day: date, open_: float, close: float, volume: int = 10_000) -> Ohlcv:
    return Ohlcv(day=day, open=open_, high=max(open_, close) + 0.5,
                 low=min(open_, close) - 0.5, close=close, volume=volume)


def _uptrend(days: int, start: float = 100.0, slope: float = 0.4) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [_bar(d0 + timedelta(days=i), start + slope * i, start + slope * i) for i in range(days)]


def _downtrend(days: int, start: float = 200.0, slope: float = 0.4) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [_bar(d0 + timedelta(days=i), start - slope * i, start - slope * i) for i in range(days)]


# ---- guardrails ---------------------------------------------------------


def test_short_history_returns_unknown():
    s = score_earnings(_uptrend(50), symbol="X", report_date=date(2025, 2, 1))
    assert s.rating == "UNKNOWN"
    assert s.score == 0


def test_no_post_report_bar_returns_unknown():
    bars = _uptrend(220)
    # report date AFTER series ends
    s = score_earnings(bars, symbol="X", report_date=date(2026, 1, 1))
    assert s.rating == "UNKNOWN"


# ---- factor scoring ----------------------------------------------------


def test_strong_continuation_on_stage2_gap_up_high_volume():
    bars = _uptrend(220)
    # Replace last bar with a gap-up + high volume reaction
    d0 = bars[-1].day + timedelta(days=1)
    prev_close = bars[-1].close
    gap_bar = _bar(d0, open_=prev_close * 1.12, close=prev_close * 1.13, volume=30_000)
    bars.append(gap_bar)
    s = score_earnings(bars, symbol="X", report_date=d0)
    assert s.rating in ("STRONG_CONTINUATION", "CONTINUATION")
    assert s.gap_pct >= 10.0
    assert s.trend_stage == "STAGE_2"
    assert s.volume_surge >= 1.8


def test_fade_risk_on_stage4_gap_down():
    bars = _downtrend(220)
    d0 = bars[-1].day + timedelta(days=1)
    prev_close = bars[-1].close
    gap_bar = _bar(d0, open_=prev_close * 0.88, close=prev_close * 0.87, volume=30_000)
    bars.append(gap_bar)
    s = score_earnings(bars, symbol="X", report_date=d0)
    assert s.rating in ("FADE_RISK", "STRONG_FADE_RISK", "NEUTRAL")
    assert s.gap_pct <= -10.0
    assert s.trend_stage == "STAGE_4"


def test_circuit_limit_note_added_when_near_upper_band():
    bars = _uptrend(220)
    d0 = bars[-1].day + timedelta(days=1)
    prev_close = bars[-1].close
    gap_bar = _bar(d0, open_=prev_close * 1.148, close=prev_close * 1.15, volume=10_000)
    bars.append(gap_bar)
    s = score_earnings(bars, symbol="X", report_date=d0)
    assert any("upper-circuit" in n for n in s.notes)


def test_stage4_note_added():
    bars = _downtrend(220)
    d0 = bars[-1].day + timedelta(days=1)
    prev_close = bars[-1].close
    gap_bar = _bar(d0, open_=prev_close * 1.05, close=prev_close * 1.05, volume=20_000)
    bars.append(gap_bar)
    s = score_earnings(bars, symbol="X", report_date=d0)
    assert any("Stage 4" in n for n in s.notes)


def test_components_carry_values():
    bars = _uptrend(220)
    d0 = bars[-1].day + timedelta(days=1)
    bars.append(_bar(d0, bars[-1].close * 1.05, bars[-1].close * 1.05, volume=20_000))
    s = score_earnings(bars, symbol="X", report_date=d0)
    assert "gap" in s.components and "score" in s.components["gap"]
    assert "trend" in s.components
    assert "volume" in s.components
    assert "ma200" in s.components
    assert "ma50" in s.components


def test_reaction_date_picks_first_bar_at_or_after_report():
    bars = _uptrend(220)
    # Report date matches an existing bar in the series — reaction should be that bar
    target_idx = 210
    s = score_earnings(bars, symbol="X", report_date=bars[target_idx].day)
    assert s.reaction_date == bars[target_idx].day
