"""Tests for the sharesansar today-share-price fetcher.

Network is never hit — tests inject HTML fixtures via parse_snapshot()
and exercise upsert_bar() against a tmp_path data directory.
"""

import csv
import sys
from datetime import date
from pathlib import Path

import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetch_nepse_snapshot import parse_snapshot, upsert_bar, write_constituents_csv

# ---- table HTML fixtures ---------------------------------------------------


def _row(symbol: str, o: float, h: float, lo: float, c: float, vol: int, prev: float) -> str:
    """Build a single <tr> matching sharesansar's today-share-price column layout
    (24 columns; we fill the ones the parser reads + zeros elsewhere)."""
    cells = [""] * 24
    cells[1] = symbol
    cells[3] = f"{o:.2f}"
    cells[4] = f"{h:.2f}"
    cells[5] = f"{lo:.2f}"
    cells[6] = f"{c:.2f}"
    cells[11] = f"{vol:,}"
    cells[12] = f"{prev:.2f}"
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def _table_html(rows_html: list[str]) -> str:
    return (
        '<html><body><table class="table table-bordered">'
        + "".join(rows_html)
        + "</table></body></html>"
    )


# ---- parse_snapshot --------------------------------------------------------


def test_parses_clean_rows():
    html = _table_html(
        [
            _row("NABIL", 1180.0, 1212.0, 1175.0, 1207.5, 84320, 1180.0),
            _row("UPPER", 425.0, 440.5, 420.0, 438.0, 150000, 425.0),
        ]
    )
    bars = parse_snapshot(html)
    by_symbol = {b["symbol"]: b for b in bars}
    assert "NABIL" in by_symbol and "UPPER" in by_symbol
    assert by_symbol["NABIL"]["close"] == 1207.5
    assert by_symbol["NABIL"]["volume"] == 84320
    assert by_symbol["UPPER"]["high"] == 440.5


def test_skips_non_traded_zero_rows():
    html = _table_html(
        [
            _row("NABIL", 1180.0, 1212.0, 1175.0, 1207.5, 84320, 1180.0),
            _row("ZZZNT", 0.0, 0.0, 0.0, 0.0, 0, 0.0),  # not traded
        ]
    )
    bars = parse_snapshot(html)
    assert {b["symbol"] for b in bars} == {"NABIL"}


def test_skips_invalid_symbol_format():
    html = _table_html(
        [
            _row("NABIL", 1180.0, 1212.0, 1175.0, 1207.5, 84320, 1180.0),
            # Symbols that wouldn't be valid NEPSE tickers
        ]
    )
    # Insert a bogus row with a non-ticker symbol manually
    bogus_row = (
        "<tr>"
        + "<td>99</td><td>not-a-ticker</td>"
        + "".join("<td>0.00</td>" for _ in range(22))
        + "</tr>"
    )
    html = _table_html([_row("NABIL", 1180, 1212, 1175, 1207.5, 84320, 1180), bogus_row])
    bars = parse_snapshot(html)
    assert {b["symbol"] for b in bars} == {"NABIL"}


def test_handles_commas_and_blanks_in_numbers():
    """Sharesansar formats volume as '1,225.00' or '-' for missing."""
    html = _table_html(
        [_row("FOO", 100.5, 110.0, 99.0, 108.0, 1_234_567, 100.5)]
    )
    # Manually inject an "N/A" volume row to make sure the parser tolerates
    bad_row = (
        "<tr>"
        + "<td>2</td><td>BAR</td><td>0</td><td>10.00</td><td>11.00</td>"
        + "<td>9.00</td><td>10.50</td><td>10.50</td><td>0</td><td>0</td>"
        + "<td>10.50</td><td>-</td><td>10.00</td>"
        + "".join("<td>0</td>" for _ in range(11))
        + "</tr>"
    )
    html = _table_html([_row("FOO", 100.5, 110, 99, 108, 1_234_567, 100.5), bad_row])
    bars = parse_snapshot(html)
    by = {b["symbol"]: b for b in bars}
    assert by["FOO"]["volume"] == 1_234_567
    assert by["BAR"]["volume"] == 0  # "-" parses as 0


def test_returns_empty_when_no_table():
    assert parse_snapshot("<html><body><p>oops</p></body></html>") == []


# ---- upsert_bar ------------------------------------------------------------


@pytest.fixture
def ohlcv_dir(tmp_path: Path) -> Path:
    d = tmp_path / "ohlcv"
    d.mkdir()
    return d


def _bar(o=100.0, h=110.0, lo=95.0, c=105.0, vol=10000, prev=100.0) -> dict:
    return {"open": o, "high": h, "low": lo, "close": c, "volume": vol, "prev_close": prev}


def test_upsert_adds_new_csv(ohlcv_dir: Path):
    p = ohlcv_dir / "NABIL.csv"
    status = upsert_bar(p, date(2026, 5, 18), _bar(c=1207.5))
    assert status == "added"
    assert p.exists()
    rows = list(csv.DictReader(p.open()))
    assert rows == [
        {
            "date": "2026-05-18",
            "open": "100.00", "high": "110.00", "low": "95.00",
            "close": "1207.50", "volume": "10000", "prev_close": "100.00",
        }
    ]


def test_upsert_dedupes_same_day(ohlcv_dir: Path):
    p = ohlcv_dir / "NABIL.csv"
    upsert_bar(p, date(2026, 5, 18), _bar(c=1200.0))
    status = upsert_bar(p, date(2026, 5, 18), _bar(c=1200.0))  # exact replay
    assert status == "unchanged"
    rows = list(csv.DictReader(p.open()))
    assert len(rows) == 1


def test_upsert_updates_same_day_when_values_differ(ohlcv_dir: Path):
    p = ohlcv_dir / "NABIL.csv"
    upsert_bar(p, date(2026, 5, 18), _bar(c=1200.0))
    status = upsert_bar(p, date(2026, 5, 18), _bar(c=1220.0))  # late correction
    assert status == "updated"
    rows = list(csv.DictReader(p.open()))
    assert len(rows) == 1
    assert rows[0]["close"] == "1220.00"


def test_upsert_appends_new_day_and_sorts(ohlcv_dir: Path):
    p = ohlcv_dir / "NABIL.csv"
    upsert_bar(p, date(2026, 5, 18), _bar(c=1207.5))
    upsert_bar(p, date(2026, 5, 16), _bar(c=1180.0))  # backfill earlier day
    upsert_bar(p, date(2026, 5, 17), _bar(c=1195.0))
    rows = list(csv.DictReader(p.open()))
    assert [r["date"] for r in rows] == ["2026-05-16", "2026-05-17", "2026-05-18"]


# ---- write_constituents_csv ------------------------------------------------


def test_constituents_grows_over_time(tmp_path: Path):
    # Day 1 snapshot
    write_constituents_csv(tmp_path, [{"symbol": "NABIL"}, {"symbol": "UPPER"}])
    # Day 2 snapshot — UPPER missing (suspended?), NICA new
    write_constituents_csv(tmp_path, [{"symbol": "NABIL"}, {"symbol": "NICA"}])

    rows = sorted(r["symbol"] for r in csv.DictReader((tmp_path / "constituents.csv").open()))
    assert rows == ["NABIL", "NICA", "UPPER"]  # UPPER preserved across snapshots
