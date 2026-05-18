"""Tests for the NEPSE dividend scorer."""

from datetime import date, timedelta

from dividend_scorer import (
    DividendRecord,
    parse_dividends_csv,
    score_universe,
    yield_for,
)

from common.nepse.client import Ohlcv, Security


def _bar_series(days: int, close_constant: float) -> list[Ohlcv]:
    d0 = date(2025, 1, 1)
    return [
        Ohlcv(day=d0 + timedelta(days=i), open=close_constant, high=close_constant + 0.5,
              low=close_constant - 0.5, close=close_constant, volume=10_000)
        for i in range(days)
    ]


# ---- CSV parsing ---------------------------------------------------------


def test_parse_csv_basic():
    csv = "symbol,cash_div_pct,bonus_div_pct,reported_at\nNABIL,11.0,0.0,2025-12-15\nNICA,16.0,4.0,2025-11-22\n"
    out = parse_dividends_csv(csv)
    assert "NABIL" in out
    assert out["NABIL"].cash_div_pct == 11.0
    assert out["NABIL"].bonus_div_pct == 0.0
    assert out["NABIL"].total_div_pct == 11.0
    assert out["NABIL"].reported_at == "2025-12-15"
    assert out["NICA"].total_div_pct == 20.0


def test_parse_csv_skips_empty_symbol():
    csv = "symbol,cash_div_pct,bonus_div_pct\n,11.0,0.0\nNABIL,11.0,0.0\n"
    out = parse_dividends_csv(csv)
    assert list(out.keys()) == ["NABIL"]


def test_parse_csv_handles_missing_optional():
    csv = "symbol,cash_div_pct,bonus_div_pct\nNABIL,11.0,0.0\n"
    out = parse_dividends_csv(csv)
    assert out["NABIL"].reported_at is None


def test_parse_csv_normalizes_symbol_to_upper():
    csv = "symbol,cash_div_pct,bonus_div_pct\nnabil,11.0,0.0\n"
    out = parse_dividends_csv(csv)
    assert "NABIL" in out
    assert "nabil" not in out


def test_parse_csv_bad_numeric_skipped():
    csv = "symbol,cash_div_pct,bonus_div_pct\nNABIL,oops,0.0\nNICA,16,4\n"
    out = parse_dividends_csv(csv)
    assert "NABIL" not in out
    assert "NICA" in out


# ---- Yield math ----------------------------------------------------------


def test_yield_formula():
    r = DividendRecord("NICA", 16.0, 4.0)
    # 20 / 745 face_value / price → ~2.68%
    assert yield_for(r, 745.0) == 2.68


def test_yield_zero_price_returns_none():
    r = DividendRecord("X", 10.0, 0.0)
    assert yield_for(r, 0.0) is None


# ---- score_universe ------------------------------------------------------


def test_score_universe_excludes_names_without_dividend_record():
    secs = [Security("A", "A", "BANKING"), Security("B", "B", "BANKING")]
    bars = {"A": _bar_series(260, 100.0), "B": _bar_series(260, 100.0)}
    divs = {"A": DividendRecord("A", 10.0, 0.0)}   # only A has a dividend
    rows = score_universe(secs, bars_by_symbol=bars, dividends=divs, min_yield_pct=0.0)
    assert [r["symbol"] for r in rows] == ["A"]


def test_score_universe_applies_min_yield_filter():
    secs = [Security("HIGH", "H", "BANKING"), Security("LOW", "L", "BANKING")]
    bars = {
        "HIGH": _bar_series(260, 100.0),   # 10% div → 10% yield
        "LOW": _bar_series(260, 1000.0),   # 10% div → 1% yield
    }
    divs = {
        "HIGH": DividendRecord("HIGH", 10.0, 0.0),
        "LOW": DividendRecord("LOW", 10.0, 0.0),
    }
    rows = score_universe(secs, bars_by_symbol=bars, dividends=divs, min_yield_pct=5.0)
    assert [r["symbol"] for r in rows] == ["HIGH"]


def test_score_universe_sorts_by_yield_desc():
    secs = [Security("A", "A", "BANKING"), Security("B", "B", "BANKING")]
    bars = {"A": _bar_series(260, 200.0), "B": _bar_series(260, 100.0)}
    divs = {
        "A": DividendRecord("A", 10.0, 0.0),   # 10*100/200 = 5%
        "B": DividendRecord("B", 10.0, 0.0),   # 10*100/100 = 10%
    }
    rows = score_universe(secs, bars_by_symbol=bars, dividends=divs, min_yield_pct=0.0)
    assert [r["symbol"] for r in rows] == ["B", "A"]


def test_distance_to_sma200_for_constant_price_is_zero():
    secs = [Security("A", "A", "BANKING", margin_eligible=True)]
    bars = {"A": _bar_series(260, 100.0)}
    divs = {"A": DividendRecord("A", 10.0, 0.0)}
    rows = score_universe(secs, bars_by_symbol=bars, dividends=divs, min_yield_pct=0.0)
    assert rows[0]["distance_to_sma200_pct"] == 0.0
    assert rows[0]["margin_eligible"] is True
