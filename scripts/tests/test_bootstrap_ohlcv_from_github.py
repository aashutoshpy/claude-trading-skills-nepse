"""Tests for the GitHub-archive bootstrap helper.

Network is never hit — tests build a tiny in-memory tar.gz with a fake
Aabishkar2-format CSV and exercise the transform + iteration logic.
"""

import csv
import io
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bootstrap_ohlcv_from_github import _iter_company_csvs, transform_csv
from import_ohlcv_from_table import merge_into_csv

# ---- transform_csv ---------------------------------------------------------


SAMPLE_AABISHKAR_CSV = (
    "published_date,open,high,low,close,per_change,traded_quantity,traded_amount,status\n"
    "2011-05-15,1091.0,1155.0,1112.0,1155.0,nan,38.0,43057.0,0\n"
    "2011-05-16,1155.0,1193.0,1160.0,1193.0,3.29,156.0,183026.0,0\n"
    "2018-05-02,1017.0,1025.0,996.0,1009.0,-0.39,10811.0,10833777.0,-1\n"
)


def test_transform_drops_unused_columns_and_renames():
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    assert len(rows) == 3
    # Schema: date, open, high, low, close, volume, prev_close
    assert rows[0] == {
        "date": "2011-05-15",
        "open": "1091.00",
        "high": "1155.00",
        "low": "1112.00",
        "close": "1155.00",
        "volume": "38",
        "prev_close": "",
    }


def test_transform_volume_is_integer():
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    # Volume comes in as 38.0; should be normalized to integer
    assert rows[0]["volume"] == "38"
    assert rows[1]["volume"] == "156"


def test_transform_handles_nan_per_change():
    """per_change=nan in the source should not break parsing — that column is dropped anyway."""
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    # All 3 rows have valid OHLC, regardless of per_change=nan in row 1
    assert len(rows) == 3


def test_transform_skips_rows_with_missing_price():
    bad_csv = (
        "published_date,open,high,low,close,per_change,traded_quantity,traded_amount,status\n"
        "2026-05-18,100.0,110.0,95.0,105.0,1.0,1000,100000,0\n"
        "2026-05-17,nan,nan,nan,nan,nan,nan,nan,0\n"   # all NaN — skip
        "not-a-date,100,110,95,105,0,0,0,0\n"           # bad date — skip
        "2026-05-16,98.0,103.0,96.0,100.0,0.5,500,50000,0\n"
    )
    rows = transform_csv(bad_csv)
    assert [r["date"] for r in rows] == ["2026-05-18", "2026-05-16"]


def test_transform_returns_empty_for_unknown_schema():
    """If the CSV doesn't have published_date, we refuse rather than mangle."""
    not_aabishkar = "date,open,high,low,close\n2026-05-18,100,110,95,105\n"
    assert transform_csv(not_aabishkar) == []


def test_transform_handles_empty_input():
    assert transform_csv("") == []
    assert transform_csv("published_date\n") == []


# ---- _iter_company_csvs ----------------------------------------------------


def _build_tarball(files: dict[str, str]) -> bytes:
    """Build an in-memory tar.gz mimicking the GitHub archive layout."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_iter_extracts_only_company_csvs():
    tarball = _build_tarball({
        "nepse-data-main/README.md": "ignore me",
        "nepse-data-main/data/company-wise/NABIL.csv": SAMPLE_AABISHKAR_CSV,
        "nepse-data-main/data/company-wise/UPPER.csv": SAMPLE_AABISHKAR_CSV,
        "nepse-data-main/data/something-else/X.csv": "ignore me",
        "nepse-data-main/src/scrapper.py": "ignore me",
    })
    out = dict(_iter_company_csvs(tarball, "data/company-wise/"))
    assert sorted(out.keys()) == ["NABIL", "UPPER"]
    assert out["NABIL"].startswith("published_date,")


def test_iter_rejects_dotfile_and_overlong_names():
    tarball = _build_tarball({
        "nepse-data-main/data/company-wise/NABIL.csv": SAMPLE_AABISHKAR_CSV,
        "nepse-data-main/data/company-wise/.gitkeep.csv": SAMPLE_AABISHKAR_CSV,  # dot-prefixed → reject
        "nepse-data-main/data/company-wise/X.csv": SAMPLE_AABISHKAR_CSV,        # too short → reject
        "nepse-data-main/data/company-wise/THIS_IS_WAY_TOO_LONG_TO_BE_A_TICKER.csv": SAMPLE_AABISHKAR_CSV,
        "nepse-data-main/data/company-wise/nabilcase.csv": SAMPLE_AABISHKAR_CSV,  # lowercase → upper()'d, kept
    })
    out = dict(_iter_company_csvs(tarball, "data/company-wise/"))
    assert sorted(out.keys()) == ["NABIL", "NABILCASE"]


def test_iter_handles_no_matching_files():
    tarball = _build_tarball({"nepse-data-main/README.md": "x"})
    assert list(_iter_company_csvs(tarball, "data/company-wise/")) == []


# ---- end-to-end transform → merge ------------------------------------------


def test_transform_then_merge_writes_clean_csv(tmp_path: Path):
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    csv_path = tmp_path / "ohlcv" / "NABIL.csv"
    added, updated, unchanged = merge_into_csv(csv_path, rows)
    assert (added, updated, unchanged) == (3, 0, 0)

    out_rows = list(csv.DictReader(csv_path.open()))
    # Sorted ascending by date
    assert [r["date"] for r in out_rows] == ["2011-05-15", "2011-05-16", "2018-05-02"]
    assert out_rows[0]["open"] == "1091.00"
    assert out_rows[0]["close"] == "1155.00"


def test_re_bootstrap_is_idempotent(tmp_path: Path):
    """Running the bootstrap twice should leave the CSV unchanged the second time."""
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    csv_path = tmp_path / "ohlcv" / "NABIL.csv"
    merge_into_csv(csv_path, rows)
    added, updated, unchanged = merge_into_csv(csv_path, rows)
    assert (added, updated, unchanged) == (0, 0, 3)


def test_bootstrap_extends_existing_data(tmp_path: Path):
    """Existing data is preserved; bootstrap adds historical rows behind it."""
    csv_path = tmp_path / "ohlcv" / "NABIL.csv"
    # Pretend the daily fetcher already wrote today's row
    today_row = {
        "date": "2026-05-18", "open": "1200.00", "high": "1220.00",
        "low": "1180.00", "close": "1207.50", "volume": "100000", "prev_close": "1200.00",
    }
    merge_into_csv(csv_path, [today_row])

    # Now bootstrap (which has older history)
    rows = transform_csv(SAMPLE_AABISHKAR_CSV)
    added, updated, unchanged = merge_into_csv(csv_path, rows)
    assert added == 3
    assert unchanged == 0  # today's row stays

    out_rows = list(csv.DictReader(csv_path.open()))
    dates = [r["date"] for r in out_rows]
    # Newest preserved (the daily fetcher's row), oldest from the archive
    assert dates[0] == "2011-05-15"
    assert dates[-1] == "2026-05-18"
    assert out_rows[-1]["close"] == "1207.50"  # daily-fetcher row preserved verbatim
