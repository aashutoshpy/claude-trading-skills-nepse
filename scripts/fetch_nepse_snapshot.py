#!/usr/bin/env python3
"""Append today's NEPSE OHLCV snapshot to `data/ohlcv/<SYMBOL>.csv`.

Scrapes sharesansar.com/today-share-price (a public HTML table — no anti-bot
defense — covering all ~160 actively-traded NEPSE symbols on the day).
For each symbol, appends a single bar (today's OHLCV) to its per-symbol CSV.
De-duplicates by date, so running the script twice in one day is a no-op.

Default schedule: run once per trading day, after market close (15:00 NPT).
Build up a multi-month base by running it daily; for an instant 6-month
bootstrap, paste historical OHLCV into the CSVs manually from any source
you trust (broker statement, sharesansar's per-company "Price History" tab
that you screenshot, etc.).

Usage:
    python3 scripts/fetch_nepse_snapshot.py
    python3 scripts/fetch_nepse_snapshot.py --as-of 2026-05-17  # backfill label
    python3 scripts/fetch_nepse_snapshot.py --data-dir custom/dir
    python3 scripts/fetch_nepse_snapshot.py --symbols NABIL UPPER NICA  # subset

The script is offline-safe to dry-run (`--dry-run` prints what it would do).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError

_URL = "https://www.sharesansar.com/today-share-price"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Column indices in sharesansar's today-share-price table (0-indexed within a row).
# Row schema:
#   0:S.No  1:Symbol  2:Conf.  3:Open  4:High  5:Low  6:Close  7:LTP
#   8:Close-LTP  9:Close-LTP%  10:VWAP  11:Vol  12:Prev.Close  ...
_COL_SYMBOL, _COL_OPEN, _COL_HIGH, _COL_LOW, _COL_CLOSE, _COL_VOL, _COL_PREV = (
    1, 3, 4, 5, 6, 11, 12,
)
_CSV_HEADER = ["date", "open", "high", "low", "close", "volume", "prev_close"]


def fetch_html(url: str = _URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_snapshot(html: str) -> list[dict]:
    """Extract rows from the today-share-price table. Returns a list of dicts
    keyed by symbol, with float OHLCV and int volume."""
    # Grab the main bordered table that holds the price grid
    m = re.search(
        r'<table[^>]*class=["\'][^"\']*table-bordered[^"\']*["\'][^>]*>([\s\S]*?)</table>',
        html,
    )
    if not m:
        return []
    body = m.group(1)
    rows_html = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', body)
    out: list[dict] = []
    for row in rows_html:
        cells_raw = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row)
        if len(cells_raw) < _COL_PREV + 1:
            continue
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells_raw]
        symbol = cells[_COL_SYMBOL].upper()
        if not re.match(r'^[A-Z][A-Z0-9]{1,9}$', symbol):
            continue
        try:
            bar = {
                "symbol": symbol,
                "open": _num(cells[_COL_OPEN]),
                "high": _num(cells[_COL_HIGH]),
                "low": _num(cells[_COL_LOW]),
                "close": _num(cells[_COL_CLOSE]),
                "volume": _intnum(cells[_COL_VOL]),
                "prev_close": _num(cells[_COL_PREV]),
            }
        except (ValueError, IndexError):
            continue
        # Filter out non-traded rows (price=0 across the board)
        if bar["open"] == 0 and bar["close"] == 0:
            continue
        out.append(bar)
    return out


def _num(s: str) -> float:
    s = s.replace(",", "").strip()
    if s in ("", "-", "N/A"):
        return 0.0
    return float(s)


def _intnum(s: str) -> int:
    s = s.replace(",", "").strip()
    if s in ("", "-", "N/A"):
        return 0
    return int(float(s))


def upsert_bar(csv_path: Path, as_of: date, bar: dict) -> str:
    """Append or update today's row in <SYMBOL>.csv. Returns 'added', 'updated',
    or 'unchanged'."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))

    new_row = {
        "date": as_of.isoformat(),
        "open": f"{bar['open']:.2f}",
        "high": f"{bar['high']:.2f}",
        "low": f"{bar['low']:.2f}",
        "close": f"{bar['close']:.2f}",
        "volume": str(bar["volume"]),
        "prev_close": f"{bar['prev_close']:.2f}",
    }

    status = "added"
    existing_idx = next(
        (i for i, r in enumerate(rows) if r.get("date") == as_of.isoformat()), None,
    )
    if existing_idx is not None:
        if rows[existing_idx] == new_row:
            return "unchanged"
        rows[existing_idx] = new_row
        status = "updated"
    else:
        rows.append(new_row)

    rows.sort(key=lambda r: r.get("date", ""))
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_CSV_HEADER)
        w.writeheader()
        w.writerows(rows)
    return status


def write_constituents_csv(data_dir: Path, bars: list[dict]) -> None:
    """Write data/constituents.csv from the snapshot (symbol → seen-today)."""
    path = data_dir / "constituents.csv"
    # Preserve any existing rows (so the universe grows over time).
    existing: dict[str, dict] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                sym = (row.get("symbol") or "").upper().strip()
                if sym:
                    existing[sym] = row
    for bar in bars:
        sym = bar["symbol"]
        if sym not in existing:
            existing[sym] = {
                "symbol": sym,
                "name": sym,
                "sector_id": "OTHERS",  # user can edit later if they want
            }
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["symbol", "name", "sector_id", "margin_eligible"],
            extrasaction="ignore",
        )
        w.writeheader()
        for row in sorted(existing.values(), key=lambda r: r["symbol"]):
            w.writerow(row)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--data-dir", default="data", help="Root of the CSV cache (default: data/)")
    p.add_argument("--as-of", help="Override today's date (YYYY-MM-DD)")
    p.add_argument("--symbols", nargs="*", help="Limit to these tickers")
    p.add_argument("--dry-run", action="store_true", help="Print what would change; don't write")
    p.add_argument("--url", default=_URL, help="Source URL (default: sharesansar today-share-price)")
    args = p.parse_args()

    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    data_dir = Path(args.data_dir).expanduser().resolve()

    print(f"Fetching {args.url} ...", file=sys.stderr)
    try:
        html = fetch_html(args.url)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: fetch failed: {exc}", file=sys.stderr)
        return 2

    bars = parse_snapshot(html)
    if not bars:
        print("ERROR: parsed 0 rows; source HTML structure may have changed.", file=sys.stderr)
        return 3

    if args.symbols:
        wanted = {s.upper() for s in args.symbols}
        bars = [b for b in bars if b["symbol"] in wanted]
        if not bars:
            print(f"ERROR: none of {sorted(wanted)} found in today's snapshot.", file=sys.stderr)
            return 4

    print(f"Parsed {len(bars)} symbols. Writing to {data_dir}/ohlcv/ ...", file=sys.stderr)
    counts = {"added": 0, "updated": 0, "unchanged": 0}
    if args.dry_run:
        for bar in bars[:5]:
            print(f"  would write {bar['symbol']}: {bar}", file=sys.stderr)
        print(f"  ... and {max(0, len(bars) - 5)} more. (dry-run; no files written.)", file=sys.stderr)
        return 0

    ohlcv_dir = data_dir / "ohlcv"
    for bar in bars:
        path = ohlcv_dir / f"{bar['symbol']}.csv"
        status = upsert_bar(path, as_of, bar)
        counts[status] += 1

    write_constituents_csv(data_dir, bars)

    print(
        f"Done. {counts['added']} added, {counts['updated']} updated, "
        f"{counts['unchanged']} unchanged. Constituents: {data_dir / 'constituents.csv'}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
