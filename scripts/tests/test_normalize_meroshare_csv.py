"""Tests for the MeroShare → tracker-schema normalizer.

Real-data fixture mirrors the actual MeroShare export format the user
provided (quoted columns, verbose names, mixed-case headers).
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from normalize_meroshare_csv import (  # noqa: E402
    merge,
    parse_cost_basis_csv,
    parse_meroshare_csv,
)

# ---- fixture data ----------------------------------------------------------


MEROSHARE_CSV_BODY = (
    '"S.N","Scrip","Current Balance","Last Closing Price",'
    '"Value as of Last Closing Price","Last Transaction Price (LTP)",'
    '"Value as of LTP"\n'
    '"1","NI31","7876.0","10.33","81359.08","10.33","81359.08"\n'
    '"2","NICADF","23102.0","10.0","231020.00","10.0","231020.00"\n'
    '"3","SBI","2.0","396.0","792.00","393.40","786.80"\n'
)

COST_BASIS_BODY = (
    "symbol,avg_cost,entry_date,is_margin\n"
    "NI31,10.33,2024-01-20,false\n"
    "NICADF,10.00,2023-08-15,false\n"
    # SBI deliberately missing — drives the partial-output path
)


# ---- parse_meroshare_csv ---------------------------------------------------


def test_parse_meroshare_extracts_symbol_and_shares(tmp_path: Path):
    p = tmp_path / "meroshare.csv"
    p.write_text(MEROSHARE_CSV_BODY)
    rows = parse_meroshare_csv(p)
    assert len(rows) == 3
    assert rows[0]["symbol"] == "NI31"
    assert rows[0]["shares"] == 7876.0
    assert rows[2]["symbol"] == "SBI"
    assert rows[2]["shares"] == 2.0


def test_parse_meroshare_uppercases_and_strips(tmp_path: Path):
    p = tmp_path / "meroshare.csv"
    p.write_text(
        '"S.N","Scrip","Current Balance","Last Closing Price",'
        '"Value as of Last Closing Price","Last Transaction Price (LTP)",'
        '"Value as of LTP"\n'
        '"1","  nabil  ","100","100","10000","100","10000"\n'
    )
    rows = parse_meroshare_csv(p)
    assert rows[0]["symbol"] == "NABIL"  # stripped + uppercased


def test_parse_meroshare_skips_zero_balance_rows(tmp_path: Path):
    p = tmp_path / "meroshare.csv"
    p.write_text(
        '"S.N","Scrip","Current Balance","Last Closing Price",'
        '"Value as of Last Closing Price","Last Transaction Price (LTP)",'
        '"Value as of LTP"\n'
        '"1","NABIL","100","100","10000","100","10000"\n'
        '"2","SOLD","0","100","0","100","0"\n'  # fully sold position
    )
    rows = parse_meroshare_csv(p)
    assert [r["symbol"] for r in rows] == ["NABIL"]


def test_parse_meroshare_rejects_unknown_schema(tmp_path: Path):
    p = tmp_path / "meroshare.csv"
    p.write_text("date,open,high,low,close\n2026-05-18,100,110,95,105\n")
    with pytest.raises(ValueError, match="missing required columns"):
        parse_meroshare_csv(p)


# ---- parse_cost_basis_csv --------------------------------------------------


def test_parse_cost_basis_full_row(tmp_path: Path):
    p = tmp_path / "cb.csv"
    p.write_text(COST_BASIS_BODY)
    cb = parse_cost_basis_csv(p)
    assert set(cb.keys()) == {"NI31", "NICADF"}
    assert cb["NI31"]["avg_cost"] == "10.33"
    assert cb["NI31"]["entry_date"] == "2024-01-20"
    assert cb["NI31"]["is_margin"] == "false"


def test_parse_cost_basis_missing_file_returns_empty(tmp_path: Path):
    assert parse_cost_basis_csv(tmp_path / "does_not_exist.csv") == {}


def test_parse_cost_basis_strips_and_uppercases(tmp_path: Path):
    p = tmp_path / "cb.csv"
    p.write_text("symbol,avg_cost\n  nabil  ,1180.00\n")
    cb = parse_cost_basis_csv(p)
    assert "NABIL" in cb


# ---- merge -----------------------------------------------------------------


def test_merge_full_join_produces_complete_rows(tmp_path: Path):
    meroshare = [
        {"symbol": "NI31", "shares": 7876.0},
        {"symbol": "NICADF", "shares": 23102.0},
    ]
    cb = {
        "NI31": {"avg_cost": "10.33", "entry_date": "2024-01-20", "is_margin": "false"},
        "NICADF": {"avg_cost": "10.00", "entry_date": "2023-08-15", "is_margin": "false"},
    }
    rows, missing = merge(meroshare, cb)
    assert missing == []
    assert len(rows) == 2
    # Sorted by symbol
    assert [r["symbol"] for r in rows] == ["NI31", "NICADF"]
    assert rows[0]["avg_cost"] == "10.33"


def test_merge_partial_emits_blank_basis_and_lists_missing():
    meroshare = [
        {"symbol": "NI31", "shares": 7876.0},
        {"symbol": "NICADF", "shares": 23102.0},
        {"symbol": "SBI", "shares": 2.0},
    ]
    cb = {
        "NI31": {"avg_cost": "10.33", "entry_date": "2024-01-20", "is_margin": "false"},
    }
    rows, missing = merge(meroshare, cb)
    assert missing == ["NICADF", "SBI"]
    by_symbol = {r["symbol"]: r for r in rows}
    assert by_symbol["NI31"]["avg_cost"] == "10.33"
    assert by_symbol["NICADF"]["avg_cost"] == ""
    assert by_symbol["SBI"]["avg_cost"] == ""


def test_merge_integer_shares_render_without_decimal():
    meroshare = [{"symbol": "X", "shares": 100.0}]
    rows, _ = merge(meroshare, {})
    assert rows[0]["shares"] == "100"


def test_merge_fractional_shares_preserved():
    meroshare = [{"symbol": "X", "shares": 7.86}]
    rows, _ = merge(meroshare, {})
    assert rows[0]["shares"] == "7.86"


def test_merge_sort_is_stable_across_runs():
    meroshare = [
        {"symbol": "ZEBRA", "shares": 1.0},
        {"symbol": "ALPHA", "shares": 2.0},
        {"symbol": "MIDDLE", "shares": 3.0},
    ]
    rows, _ = merge(meroshare, {})
    assert [r["symbol"] for r in rows] == ["ALPHA", "MIDDLE", "ZEBRA"]


# ---- end-to-end (subprocess) -----------------------------------------------


SCRIPT = Path(__file__).resolve().parents[1] / "normalize_meroshare_csv.py"


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd,
    )


def test_end_to_end_with_full_basis_exits_zero(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "meroshare_export.csv").write_text(MEROSHARE_CSV_BODY)
    (tmp_path / "data" / "cost_basis.csv").write_text(
        "symbol,avg_cost,entry_date,is_margin\n"
        "NI31,10.33,2024-01-20,false\n"
        "NICADF,10.00,2023-08-15,false\n"
        "SBI,100.00,2022-05-10,false\n"
    )
    result = _run(cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    out_csv = tmp_path / "data" / "nepse_portfolio.csv"
    assert out_csv.exists()
    rows = list(csv.DictReader(out_csv.open()))
    assert len(rows) == 3
    # Tracker schema in exact order
    assert list(rows[0].keys()) == [
        "symbol", "shares", "avg_cost", "entry_date", "is_margin",
    ]


def test_end_to_end_with_partial_basis_exits_three(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "meroshare_export.csv").write_text(MEROSHARE_CSV_BODY)
    (tmp_path / "data" / "cost_basis.csv").write_text(COST_BASIS_BODY)
    result = _run(cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    assert "SBI" in result.stderr  # missing symbol flagged
    out_csv = tmp_path / "data" / "nepse_portfolio.csv"
    assert out_csv.exists()  # output is written even with partial basis


def test_end_to_end_with_missing_meroshare_exits_one(tmp_path: Path):
    result = _run(cwd=tmp_path)  # no data/ dir at all
    assert result.returncode == 1
    assert "not found" in result.stderr.lower()


def test_end_to_end_with_no_cost_basis_file_still_works(tmp_path: Path):
    """Side file is optional — without it, every symbol is 'missing'."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "meroshare_export.csv").write_text(MEROSHARE_CSV_BODY)
    result = _run(cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    assert "Missing cost basis for" in result.stderr
