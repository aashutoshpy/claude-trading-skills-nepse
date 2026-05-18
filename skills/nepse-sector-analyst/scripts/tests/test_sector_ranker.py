"""Tests for the NEPSE sector ranker."""

from datetime import date, timedelta

from sector_ranker import rank_sectors

from common.nepse.client import Ohlcv


def _series(days: int, start: float, slope: float, d0: date = date(2025, 1, 1)) -> list[Ohlcv]:
    return [
        Ohlcv(day=d0 + timedelta(days=i), open=start + slope * i, high=start + slope * i + 0.5,
              low=start + slope * i - 0.5, close=start + slope * i, volume=10_000)
        for i in range(days)
    ]


def test_rank_orders_by_first_window_return():
    bars = {
        "FAST": _series(260, 100, 1.0),    # +260% over the period
        "SLOW": _series(260, 100, 0.1),    # gentle uptrend
        "FALL": _series(260, 300, -0.5),   # downtrend
    }
    scores = rank_sectors(bars, windows={"1w": 5})
    by_id = {s.sector_id: s for s in scores}
    # 1w returns: FAST > SLOW > FALL
    assert by_id["FAST"].ranks["1w"] == 1
    assert by_id["SLOW"].ranks["1w"] == 2
    assert by_id["FALL"].ranks["1w"] == 3


def test_stage_classification_rising_universe():
    bars = {"BANKING": _series(260, 100, 0.5)}
    scores = rank_sectors(bars, windows={"1w": 5})
    assert scores[0].stage == "STAGE_2"


def test_stage_classification_falling_universe():
    bars = {"HYDROPOWER": _series(260, 300, -0.5)}
    scores = rank_sectors(bars, windows={"1w": 5})
    assert scores[0].stage == "STAGE_4"


def test_unknown_stage_for_short_history():
    bars = {"NEW": _series(50, 100, 0.5)}
    scores = rank_sectors(bars, windows={"1w": 5})
    assert scores[0].stage == "UNKNOWN"


def test_returns_pct_calculated():
    bars = {"FAST": _series(260, 100, 1.0)}
    scores = rank_sectors(bars, windows={"1w": 5})
    # Last close ~ 100 + 259*1 = 359; 5 days earlier ~ 354
    # return = (359 - 354) / 354 * 100 ≈ 1.41%
    r = scores[0].returns_pct["1w"]
    assert 1.3 < r < 1.5


def test_ytd_return_uses_first_bar_of_year():
    today = date(2025, 12, 31)
    bars = {"FAST": _series(260, 100, 1.0)}
    scores = rank_sectors(bars, windows={"1w": 5}, today=today, include_ytd=True)
    assert "ytd" in scores[0].returns_pct


def test_ranks_skip_sectors_missing_a_window():
    bars = {
        "FULL": _series(260, 100, 1.0),
        "SHORT": _series(3, 100, 1.0),    # too short for 5-day return
    }
    scores = rank_sectors(bars, windows={"1w": 5}, include_ytd=False)
    by_id = {s.sector_id: s for s in scores}
    assert "1w" in by_id["FULL"].returns_pct
    assert "1w" not in by_id["SHORT"].returns_pct
    # SHORT shouldn't get a rank in 1w
    assert "1w" not in by_id["SHORT"].ranks
