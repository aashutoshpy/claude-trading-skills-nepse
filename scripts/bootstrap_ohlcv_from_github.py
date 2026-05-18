#!/usr/bin/env python3
"""One-shot bootstrap of `data/ohlcv/` from a public NEPSE OHLCV archive.

Why this exists:
    Our `NEPSE_BACKEND=csv` workflow needs ~200 trading days of OHLCV per
    name before the VCP screener can detect a base. Building that history
    via the daily fetcher (`scripts/fetch_nepse_snapshot.py`) takes ~10
    calendar months. Importing per-name via the paste tool
    (`scripts/import_ohlcv_from_table.py`) is faster but tedious.

    `Aabishkar2/nepse-data` is a community-maintained GitHub repo that
    publishes per-symbol NEPSE OHLCV CSVs going back to 2011, auto-refreshed
    5×/day via GitHub Actions. This script downloads that archive in one
    HTTP round-trip and converts each CSV into our `data/ohlcv/` schema.

    Data attribution:
        Source: https://github.com/Aabishkar2/nepse-data  (MIT-licensed)
        Maintained by Aabishkar2; daily-updated via GitHub Actions.
        Sourced from sharesansar.com.

Schema mapping (`Aabishkar2/nepse-data` → our `CsvFileBackend` format):
    published_date   →  date
    open             →  open
    high             →  high
    low              →  low
    close            →  close
    traded_quantity  →  volume
    per_change       →  (dropped — not used)
    traded_amount    →  (dropped — not used)
    status           →  (dropped — not used)
    (no source)      →  prev_close   (left blank; CsvFileBackend treats as optional)

Usage:
    python3 scripts/bootstrap_ohlcv_from_github.py
    python3 scripts/bootstrap_ohlcv_from_github.py --symbols NABIL UPPER NICA
    python3 scripts/bootstrap_ohlcv_from_github.py --max-symbols 10 --dry-run
    python3 scripts/bootstrap_ohlcv_from_github.py --data-dir custom/path/
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import tarfile
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

# Reuse the de-dup merge helper we built for the paste-importer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_ohlcv_from_table import merge_into_csv  # noqa: E402

_DEFAULT_REPO = "Aabishkar2/nepse-data"
_DEFAULT_BRANCH = "main"
_DEFAULT_PATH_PREFIX = "data/company-wise/"
_USER_AGENT = "claude-trading-skills-nepse/bootstrap-ohlcv"

# Aabishkar2 CSV column → our schema column. Drop any column not listed.
_COL_MAP = {
    "published_date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "traded_quantity": "volume",
}


def _download_tarball(repo: str, branch: str) -> bytes:
    """Single round-trip — fetch the whole repo tarball."""
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _iter_company_csvs(tarball_bytes: bytes, path_prefix: str):
    """Yield (symbol, csv_text) tuples for every per-company CSV in the tarball."""
    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            # member.name looks like: nepse-data-main/data/company-wise/NABIL.csv
            if path_prefix not in member.name or not member.name.endswith(".csv"):
                continue
            symbol = Path(member.name).stem.upper()
            if not re.match(r"^[A-Z][A-Z0-9]{1,15}$", symbol):
                continue
            fobj = tar.extractfile(member)
            if fobj is None:
                continue
            yield symbol, fobj.read().decode("utf-8", errors="ignore")


def transform_csv(csv_text: str) -> list[dict]:
    """Parse Aabishkar2-format CSV and yield rows in our `data/ohlcv/` schema."""
    rows: list[dict] = []
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        return rows
    # Normalize source headers (the repo uses snake_case; be tolerant of variations).
    source_keys = {k.lower().strip(): k for k in reader.fieldnames if k}
    if "published_date" not in source_keys:
        return rows  # unknown schema — skip rather than mangle

    for row in reader:
        out: dict[str, str] = {
            "date": "", "open": "", "high": "", "low": "",
            "close": "", "volume": "", "prev_close": "",
        }
        skip = False
        for src_name, dst_name in _COL_MAP.items():
            src_key = source_keys.get(src_name)
            if not src_key:
                continue
            raw = (row.get(src_key) or "").strip()
            if dst_name == "date":
                if not raw or not re.match(r"^\d{4}-\d{2}-\d{2}", raw):
                    skip = True
                    break
                out["date"] = raw[:10]
            elif dst_name == "volume":
                try:
                    out["volume"] = str(int(float(raw))) if raw else "0"
                except ValueError:
                    out["volume"] = "0"
            else:
                # Price column: skip rows with empty / nan / non-numeric
                if not raw or raw.lower() in ("nan", "na", "n/a", "-"):
                    skip = True
                    break
                try:
                    out[dst_name] = f"{float(raw):.2f}"
                except ValueError:
                    skip = True
                    break
        if not skip and out["date"]:
            rows.append(out)
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--source-repo", default=_DEFAULT_REPO,
                   help=f"GitHub repo to pull from (default: {_DEFAULT_REPO})")
    p.add_argument("--branch", default=_DEFAULT_BRANCH,
                   help=f"Branch to download (default: {_DEFAULT_BRANCH})")
    p.add_argument("--path-prefix", default=_DEFAULT_PATH_PREFIX,
                   help="Subdirectory inside the tarball that holds the CSVs.")
    p.add_argument("--data-dir", default="data",
                   help="Root of the local CSV cache (default: data/)")
    p.add_argument("--symbols", nargs="*",
                   help="Only import these tickers (e.g. NABIL UPPER NICA)")
    p.add_argument("--max-symbols", type=int,
                   help="Cap total symbols processed (useful for testing)")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse + report; do not write any files.")
    args = p.parse_args()

    wanted = {s.upper() for s in args.symbols} if args.symbols else None
    target_dir = Path(args.data_dir).expanduser().resolve() / "ohlcv"

    print(
        f"Bootstrap source: github.com/{args.source_repo}@{args.branch}",
        file=sys.stderr,
    )
    print(
        "  Data attribution: Aabishkar2/nepse-data (MIT). NEPSE OHLCV scraped from sharesansar.",
        file=sys.stderr,
    )

    print("Downloading tarball ...", file=sys.stderr)
    try:
        tarball = _download_tarball(args.source_repo, args.branch)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: tarball download failed: {exc}", file=sys.stderr)
        return 2

    print(f"  got {len(tarball):,} bytes; extracting + transforming ...", file=sys.stderr)
    total_symbols = 0
    total_rows = 0
    totals = {"added": 0, "updated": 0, "unchanged": 0}
    processed_examples: list[str] = []

    for symbol, csv_text in _iter_company_csvs(tarball, args.path_prefix):
        if wanted and symbol not in wanted:
            continue
        if args.max_symbols and total_symbols >= args.max_symbols:
            break

        rows = transform_csv(csv_text)
        if not rows:
            continue
        total_symbols += 1
        total_rows += len(rows)

        if args.dry_run:
            if len(processed_examples) < 3:
                processed_examples.append(
                    f"{symbol}: {len(rows)} rows ({rows[0]['date']} → {rows[-1]['date']})"
                )
            continue

        csv_path = target_dir / f"{symbol}.csv"
        added, updated, unchanged = merge_into_csv(csv_path, rows)
        totals["added"] += added
        totals["updated"] += updated
        totals["unchanged"] += unchanged

    if args.dry_run:
        print(
            f"Would process {total_symbols} symbols, {total_rows:,} total rows.",
            file=sys.stderr,
        )
        for line in processed_examples:
            print(f"  • {line}", file=sys.stderr)
        return 0

    print(
        f"Done. {total_symbols} symbols, {total_rows:,} total rows.\n"
        f"  Merged into {target_dir}/: "
        f"{totals['added']:,} added, {totals['updated']:,} updated, "
        f"{totals['unchanged']:,} unchanged.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
