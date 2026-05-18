"""Tests for the OHLCV table importer (paste-from-browser bootstrap path)."""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from import_ohlcv_from_table import (
    _parse_date,
    _parse_num,
    merge_into_csv,
    parse_table,
)

# ---- low-level helpers -----------------------------------------------------


def test_parse_date_iso():
    from datetime import date

    assert _parse_date("2026-05-18") == date(2026, 5, 18)
    assert _parse_date("2026/05/18") == date(2026, 5, 18)
    assert _parse_date("18/05/2026") == date(2026, 5, 18)
    assert _parse_date("Garbage") is None
    assert _parse_date("") is None


def test_parse_num_tolerates_commas_and_dashes():
    assert _parse_num("1,225.00") == 1225.0
    assert _parse_num("-") is None
    assert _parse_num("N/A") is None
    assert _parse_num("") is None
    assert _parse_num("100.50") == 100.5


# ---- parse_table -----------------------------------------------------------


SHARESANSAR_HEADER_TSV = (
    "S.No\tDate\tOpen\tHigh\tLow\tClose\t% Change\tVol\tTurnover\n"
    "1\t2026-05-18\t925.00\t950.00\t925.00\t949.90\t0.00\t1,225\t1,143,527.30\n"
    "2\t2026-05-15\t920.00\t930.00\t915.00\t925.00\t-1.50\t2,500\t2,300,000.00\n"
    "3\t2026-05-14\t910.00\t925.00\t908.00\t920.00\t1.10\t1,800\t1,650,000.00\n"
)


def test_parse_sharesansar_tsv_with_header():
    rows = parse_table(SHARESANSAR_HEADER_TSV)
    assert len(rows) == 3
    assert rows[0]["date"] == "2026-05-18"
    assert rows[0]["open"] == "925.00"
    assert rows[0]["high"] == "950.00"
    assert rows[0]["close"] == "949.90"
    assert rows[0]["volume"] == "1225"


def test_parse_handles_comma_separated_format():
    text = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-05-18,925.00,950.00,925.00,949.90,1225\n"
        "2026-05-15,920.00,930.00,915.00,925.00,2500\n"
    )
    rows = parse_table(text)
    assert len(rows) == 2
    assert rows[1]["close"] == "925.00"


def test_parse_handles_whitespace_separated_no_header():
    """When user copies a clean-formatted table without explicit delimiters."""
    text = (
        "2026-05-18    925.00    950.00    925.00    949.90    1225\n"
        "2026-05-15    920.00    930.00    915.00    925.00    2500\n"
    )
    rows = parse_table(text)
    assert len(rows) == 2
    assert rows[0]["date"] == "2026-05-18"


def test_parse_skips_unparseable_rows():
    text = (
        "Date\tOpen\tHigh\tLow\tClose\tVolume\n"
        "2026-05-18\t925.00\t950.00\t925.00\t949.90\t1225\n"
        "not-a-date\t100\t110\t95\t105\t1000\n"          # bad date
        "2026-05-15\tNA\tNA\tNA\tNA\tNA\n"                # missing prices
        "2026-05-14\t910.00\t925.00\t908.00\t920.00\t1800\n"
    )
    rows = parse_table(text)
    dates = [r["date"] for r in rows]
    assert dates == ["2026-05-18", "2026-05-14"]


def test_parse_returns_empty_on_nonsense_input():
    assert parse_table("") == []
    assert parse_table("hello world") == []


# ---- merge_into_csv --------------------------------------------------------


@pytest.fixture
def tmp_csv(tmp_path: Path) -> Path:
    return tmp_path / "ohlcv" / "NABIL.csv"


def test_merge_writes_new_file(tmp_csv: Path):
    rows = parse_table(SHARESANSAR_HEADER_TSV)
    added, updated, unchanged = merge_into_csv(tmp_csv, rows)
    assert (added, updated, unchanged) == (3, 0, 0)
    assert tmp_csv.exists()
    out = list(csv.DictReader(tmp_csv.open()))
    # Sorted ascending
    assert [r["date"] for r in out] == ["2026-05-14", "2026-05-15", "2026-05-18"]


def test_merge_dedupes_idempotent_imports(tmp_csv: Path):
    rows = parse_table(SHARESANSAR_HEADER_TSV)
    merge_into_csv(tmp_csv, rows)
    added, updated, unchanged = merge_into_csv(tmp_csv, rows)
    assert (added, updated, unchanged) == (0, 0, 3)


def test_merge_updates_on_value_change(tmp_csv: Path):
    rows = parse_table(SHARESANSAR_HEADER_TSV)
    merge_into_csv(tmp_csv, rows)
    # Same dates, different close prices
    corrected = (
        "Date\tOpen\tHigh\tLow\tClose\tVolume\n"
        "2026-05-18\t925.00\t950.00\t925.00\t951.00\t1225\n"  # corrected close
        "2026-05-15\t920.00\t930.00\t915.00\t925.00\t2500\n"  # unchanged
    )
    new_rows = parse_table(corrected)
    added, updated, unchanged = merge_into_csv(tmp_csv, new_rows)
    assert (added, updated, unchanged) == (0, 1, 1)
    out = {r["date"]: r for r in csv.DictReader(tmp_csv.open())}
    assert out["2026-05-18"]["close"] == "951.00"


def test_merge_extends_existing_history(tmp_csv: Path):
    # Day 1: just one row
    initial = parse_table(
        "Date\tOpen\tHigh\tLow\tClose\tVolume\n"
        "2026-05-18\t925.00\t950.00\t925.00\t949.90\t1225\n"
    )
    merge_into_csv(tmp_csv, initial)

    # Day 2: backfill 100 historical days via paste
    backfill = parse_table(SHARESANSAR_HEADER_TSV)
    added, updated, unchanged = merge_into_csv(tmp_csv, backfill)
    # 2 are new (May 14, 15); May 18 is unchanged
    assert added == 2
    assert unchanged == 1
    out = list(csv.DictReader(tmp_csv.open()))
    assert len(out) == 3
