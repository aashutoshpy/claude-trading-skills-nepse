"""Tests for the CSV-file backend (offline data path)."""

from datetime import date
from pathlib import Path

import pytest

from common.nepse._config import reset_cache
from common.nepse.backends.csv_file import CsvFileBackend
from common.nepse.client import NepseClient


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Build a small but realistic data/ tree for the backend to read."""
    (tmp_path / "ohlcv").mkdir()
    (tmp_path / "indexes").mkdir()

    # NABIL — 3 bars
    (tmp_path / "ohlcv" / "NABIL.csv").write_text(
        "date,open,high,low,close,volume\n"
        "2026-05-15,1180.00,1212.00,1175.00,1207.50,84320\n"
        "2026-05-16,1207.50,1224.00,1200.00,1218.00,52110\n"
        "2026-05-14,1170.00,1196.00,1165.00,1180.00,61200\n",  # out-of-order date
        encoding="utf-8",
    )
    # UPPER — 2 bars + extra column we should tolerate
    (tmp_path / "ohlcv" / "UPPER.csv").write_text(
        "date,open,high,low,close,volume,turnover\n"
        "2026-05-15,425.00,440.50,420.00,438.00,150000,65700000\n"
        "2026-05-16,438.00,445.00,432.00,440.50,98000,43240000\n",
        encoding="utf-8",
    )
    # NEPSE index
    (tmp_path / "indexes" / "NEPSE.csv").write_text(
        "date,open,high,low,close,volume\n"
        "2026-05-15,2850.00,2880.00,2840.00,2872.00,0\n"
        "2026-05-16,2872.00,2895.00,2860.00,2890.00,0\n",
        encoding="utf-8",
    )
    return tmp_path


def test_get_ohlcv_reads_and_sorts(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    bars = b.get_ohlcv("NABIL", date(2026, 5, 1), date(2026, 5, 31))
    assert [bar.day for bar in bars] == [
        date(2026, 5, 14), date(2026, 5, 15), date(2026, 5, 16),
    ]
    assert bars[0].open == 1170.0
    assert bars[-1].close == 1218.0


def test_get_ohlcv_filters_date_range(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    bars = b.get_ohlcv("NABIL", date(2026, 5, 15), date(2026, 5, 15))
    assert len(bars) == 1
    assert bars[0].day == date(2026, 5, 15)


def test_get_ohlcv_returns_empty_for_missing_symbol(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    assert b.get_ohlcv("XXXXX", date(2026, 1, 1), date(2026, 12, 31)) == []


def test_extra_columns_are_tolerated(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    bars = b.get_ohlcv("UPPER", date(2026, 5, 1), date(2026, 5, 31))
    assert len(bars) == 2
    assert bars[1].close == 440.5


def test_get_index_works(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    bars = b.get_index("NEPSE", date(2026, 1, 1), date(2026, 12, 31))
    assert len(bars) == 2
    assert bars[1].close == 2890.0


def test_get_quote_returns_latest(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    q = b.get_quote("NABIL")
    assert q is not None
    assert q.day == date(2026, 5, 16)
    assert q.close == 1218.0


def test_list_constituents_discovers_from_ohlcv_dir(data_dir: Path):
    b = CsvFileBackend(data_dir=data_dir)
    secs = b.list_constituents()
    symbols = sorted(s.symbol for s in secs)
    assert symbols == ["NABIL", "UPPER"]


def test_list_constituents_picks_up_starter_watchlist(data_dir: Path):
    (data_dir / "nepse_starter_watchlist.txt").write_text(
        "NABIL\nNICA\n# comment\nGBIME\n", encoding="utf-8"
    )
    b = CsvFileBackend(data_dir=data_dir)
    symbols = sorted(s.symbol for s in b.list_constituents())
    # NABIL + UPPER from ohlcv/, NICA + GBIME from watchlist
    assert symbols == ["GBIME", "NABIL", "NICA", "UPPER"]


def test_list_constituents_uses_constituents_csv_when_present(data_dir: Path):
    (data_dir / "constituents.csv").write_text(
        "symbol,name,sector_id,margin_eligible\n"
        "NABIL,Nabil Bank,BANKING,true\n"
        "UPPER,Upper Tamakoshi,HYDROPOWER,false\n",
        encoding="utf-8",
    )
    b = CsvFileBackend(data_dir=data_dir)
    secs = {s.symbol: s for s in b.list_constituents()}
    assert secs["NABIL"].sector_id == "BANKING"
    assert secs["NABIL"].margin_eligible is True
    assert secs["UPPER"].sector_id == "HYDROPOWER"


def test_margin_eligible_falls_back_to_registry(data_dir: Path):
    """Without an explicit margin_eligible column, registry seed is consulted."""
    (data_dir / "constituents.csv").write_text(
        "symbol,name,sector_id\n"
        "NABIL,Nabil Bank,BANKING\n"
        "XYZTEST,Made Up,OTHERS\n",
        encoding="utf-8",
    )
    b = CsvFileBackend(data_dir=data_dir)
    secs = {s.symbol: s for s in b.list_constituents()}
    # NABIL is in the starter margin list shipped in config/registry.yaml
    assert secs["NABIL"].margin_eligible is True
    assert secs["XYZTEST"].margin_eligible is False


def test_nepse_client_create_csv_backend(data_dir: Path, monkeypatch):
    """End-to-end: NEPSE_BACKEND=csv resolves to CsvFileBackend."""
    monkeypatch.setenv("NEPSE_BACKEND", "csv")
    monkeypatch.setenv("NEPSE_CSV_DATA_DIR", str(data_dir))
    c = NepseClient.create()
    assert c.backend_name == "csv"
    bars = c.get_ohlcv("NABIL", date(2026, 5, 1), date(2026, 5, 31))
    assert len(bars) == 3


def test_malformed_rows_are_skipped(data_dir: Path):
    (data_dir / "ohlcv" / "BAD.csv").write_text(
        "date,open,high,low,close,volume\n"
        ",,,,,\n"                                            # blank row
        "2026-05-15,abc,def,ghi,jkl,mno\n"                  # non-numeric
        "2026-05-16,100,110,95,105,1000\n"                  # valid
        "not-a-date,100,110,95,105,1000\n",                 # bad date
        encoding="utf-8",
    )
    b = CsvFileBackend(data_dir=data_dir)
    bars = b.get_ohlcv("BAD", date(2026, 1, 1), date(2026, 12, 31))
    assert len(bars) == 1
    assert bars[0].close == 105.0
