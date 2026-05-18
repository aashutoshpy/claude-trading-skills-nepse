"""Tests for the NEPSE CANSLIM scorer."""

from datetime import date, timedelta

from canslim_scorer import (
    Fundamentals,
    parse_fundamentals_csv,
    score_A,
    score_C,
    score_L,
    score_M,
    score_N,
    score_S,
    score_universe,
)

from common.nepse.client import Ohlcv, Security


def _bar(day: date, close: float, volume: int = 10_000, open_: float | None = None) -> Ohlcv:
    o = open_ if open_ is not None else close
    return Ohlcv(day=day, open=o, high=max(o, close) + 0.5, low=min(o, close) - 0.5,
                 close=close, volume=volume)


def _series(days: int, start: float, slope: float, d0: date = date(2025, 1, 1)) -> list[Ohlcv]:
    return [_bar(d0 + timedelta(days=i), start + slope * i) for i in range(days)]


# ---- fundamentals CSV ------------------------------------------------


def test_parse_fundamentals_csv():
    csv = (
        "symbol,eps_latest,eps_prior_year,eps_3y_cagr,sales_3y_cagr\n"
        "NABIL,32.5,28.4,11.5,9.2\n"
        "NICA,42.1,36.8,14.2,8.1\n"
    )
    funds = parse_fundamentals_csv(csv)
    assert funds["NABIL"].eps_latest == 32.5
    assert funds["NABIL"].eps_3y_cagr == 11.5
    # quarterly_eps_growth_pct = (32.5 - 28.4) / 28.4 * 100 = 14.44%
    assert abs(funds["NABIL"].quarterly_eps_growth_pct - 14.44) < 0.01


def test_fundamentals_csv_handles_missing_optional():
    csv = "symbol,eps_latest\nNABIL,32.5\n"
    funds = parse_fundamentals_csv(csv)
    assert funds["NABIL"].eps_latest == 32.5
    assert funds["NABIL"].eps_prior_year is None
    assert funds["NABIL"].quarterly_eps_growth_pct is None


# ---- individual factor scoring ----------------------------------------


def test_C_no_fundamentals_returns_neutral():
    s, r = score_C(None)
    assert s == 50


def test_C_strong_growth():
    s, r = score_C(Fundamentals("X", eps_latest=130, eps_prior_year=100))
    # 30% growth → 90
    assert s == 90


def test_C_caps_at_100pct_growth():
    # 500% growth gets capped at 100% → still in the >=25 bucket → 90
    s, r = score_C(Fundamentals("X", eps_latest=600, eps_prior_year=100))
    assert s == 90


def test_A_strong_cagr():
    s, r = score_A(Fundamentals("X", eps_3y_cagr=30))
    assert s == 90


def test_N_within_3pct_high():
    bars = _series(260, 100, 0.5)
    s, r = score_N(bars)
    # Rising series → current close == 52w high → distance = 0 → 90
    assert s == 90


def test_N_far_below_high():
    bars = _series(260, 200, -0.5)   # falling: high is at day 1
    s, r = score_N(bars)
    assert s == 10


def test_S_volume_surge_high_score():
    # last 5 bars are advance days with 3x avg volume
    base = _series(60, 100, 0.1)
    # Replace last 5 with advance bars on big volume
    d = base[-5].day
    base[-5:] = [
        _bar(d + timedelta(days=i), close=100 + i + 5, volume=50_000, open_=100 + i)
        for i in range(5)
    ]
    s, r = score_S(base)
    # avg_50 ~ 10k; max advance volume = 50k → 5x → score 90
    assert s == 90


def test_L_strong_outperformance():
    sym_bars = _series(100, 100, 1.0)   # +99%
    idx_bars = _series(100, 100, 0.1)   # +9.9%
    s, r = score_L(sym_bars, index_bars=idx_bars)
    # RS spread ~89pp → 90
    assert s == 90


def test_L_no_index_returns_neutral():
    s, r = score_L(_series(100, 100, 0.1), index_bars=None)
    assert s == 50


def test_M_classifications():
    assert score_M("STRONG_UPTREND")[0] == 95
    assert score_M("UPTREND")[0] == 75
    assert score_M("NEUTRAL")[0] == 45
    assert score_M("DOWNTREND")[0] == 10


# ---- aggregator -------------------------------------------------------


def test_universe_skipped_when_downtrend():
    rows = score_universe(
        [Security("X", "X", "BANKING")],
        bars_by_symbol={"X": _series(260, 100, 0.5)},
        index_bars=_series(260, 100, 0.5),
        fundamentals={},
        uptrend_regime="DOWNTREND",
    )
    assert len(rows) == 1
    assert rows[0].skipped is True


def test_universe_skipped_when_strong_uptrend_required_but_only_uptrend():
    rows = score_universe(
        [Security("X", "X", "BANKING")],
        bars_by_symbol={"X": _series(260, 100, 0.5)},
        index_bars=_series(260, 100, 0.5),
        fundamentals={},
        uptrend_regime="UPTREND",
        require_strong_uptrend=True,
    )
    assert rows[0].skipped is True


def test_universe_returns_scored_rows_when_market_ok():
    secs = [Security(f"R{i}", f"R{i}", "BANKING") for i in range(3)]
    bars = {f"R{i}": _series(260, 100, 0.5) for i in range(3)}
    rows = score_universe(
        secs, bars_by_symbol=bars, index_bars=_series(260, 100, 0.1),
        fundamentals={}, uptrend_regime="UPTREND",
    )
    assert all(not r.skipped for r in rows)
    assert all(0 <= r.score <= 100 for r in rows)


def test_universe_enforces_per_sector_cap():
    # 10 names all in BANKING; cap = 3
    secs = [Security(f"B{i}", f"B{i}", "BANKING") for i in range(10)]
    bars = {f"B{i}": _series(260, 100, 0.5) for i in range(10)}
    rows = score_universe(
        secs, bars_by_symbol=bars, index_bars=_series(260, 100, 0.1),
        fundamentals={}, uptrend_regime="UPTREND", max_per_sector=3,
    )
    assert len(rows) == 3
