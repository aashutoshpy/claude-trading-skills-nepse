#!/usr/bin/env python3
"""Bulk-import historical OHLCV from a pasted/copied table into data/ohlcv/<SYMBOL>.csv.

Use case:
  Sharesansar's per-company `/company/<SYMBOL>` page has a "Price History" tab
  that renders 100+ days of OHLCV in the browser. We can't fetch it via API
  (silent 202 anti-bot), but you CAN select-all the rendered table in your
  browser and paste it into a text file. This script parses that paste and
  merges it into your data/ohlcv/ cache.

Workflow:
  1. Open https://www.sharesansar.com/company/NABIL in your browser.
  2. Click the "Price History" tab.
  3. Select all rows, copy.
  4. Paste into nabil_history.tsv (or pipe through stdin).
  5. python3 scripts/import_ohlcv_from_table.py --symbol NABIL --input nabil_history.tsv

The parser is forgiving: tab-, comma-, or whitespace-separated; header row
optional; tolerates extra columns (turnover, transactions, etc.); accepts
dates in YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY, or any format Python's date
parser handles. De-dupes by date when merging with the existing CSV.

Examples:
  # From a saved TSV file
  python3 scripts/import_ohlcv_from_table.py --symbol NABIL --input nabil.tsv

  # From clipboard via stdin (macOS: pbpaste; Linux: xclip -o)
  pbpaste | python3 scripts/import_ohlcv_from_table.py --symbol NABIL

  # Dry-run to preview before writing
  pbpaste | python3 scripts/import_ohlcv_from_table.py --symbol NABIL --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path

_HEADER_ALIASES = {
    "date": ["date", "trade date", "trading date", "as of", "day"],
    "open": ["open", "open price", "opening", "opening price", "o"],
    "high": ["high", "high price", "max", "h"],
    "low": ["low", "low price", "min", "l"],
    "close": ["close", "close price", "closing", "closing price", "c", "ltp", "last", "last price"],
    "volume": ["volume", "vol", "qty", "quantity", "traded quantity", "v"],
    "prev_close": ["prev close", "previous close", "prev. close", "previous", "prev"],
}

_OUT_CSV_HEADER = ["date", "open", "high", "low", "close", "volume", "prev_close"]


def _normalize_header(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower().replace(".", ""))


def _detect_separator(line: str) -> str:
    """Pick the most likely delimiter from the first non-empty line."""
    counts = {
        "\t": line.count("\t"),
        ",": line.count(","),
        "|": line.count("|"),
    }
    sep, n = max(counts.items(), key=lambda kv: kv[1])
    if n >= 3:
        return sep
    # Fall back to whitespace (multiple spaces)
    return None  # None = whitespace-split


def _split(line: str, sep: str | None) -> list[str]:
    if sep is None:
        return re.split(r"\s{2,}|\t+", line.strip())
    return [c.strip() for c in line.split(sep)]


def _parse_date(s: str) -> date | None:
    s = s.strip()
    if not s:
        return None
    for fmt in (
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y",
        "%d %b %Y", "%d %B %Y",
    ):
        try:
            return datetime.strptime(s[:20], fmt).date()
        except ValueError:
            continue
    # Last resort: ISO-prefix match
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return None


def _parse_num(s: str) -> float | None:
    s = s.replace(",", "").strip()
    if s in ("", "-", "N/A", "NA"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_table(text: str) -> list[dict]:
    """Parse pasted table text into list of {date, open, high, low, close, volume, prev_close}."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    # Determine separator from the first dense line.
    sep = _detect_separator(lines[0])

    # Try to detect a header row by looking at the first line's cells.
    header_cells = _split(lines[0], sep)
    header_lookup: dict[str, int] = {}
    for i, raw in enumerate(header_cells):
        norm = _normalize_header(raw)
        for key, aliases in _HEADER_ALIASES.items():
            if norm in aliases:
                header_lookup[key] = i

    has_header = len(header_lookup) >= 3  # at least 3 OHLCV columns matched

    if has_header:
        data_lines = lines[1:]
    else:
        # No header. Assume the standard sharesansar/merolagani column order:
        #   Date Open High Low Close (optional Volume) (optional Prev.Close)
        # Try to find the date column by scanning the first row's cells.
        first_cells = _split(lines[0], sep)
        date_col = next(
            (i for i, c in enumerate(first_cells) if _parse_date(c)),
            None,
        )
        if date_col is None:
            # Maybe the first column is a row-number; second column is date.
            return []
        # Assume OHLC are the next 4 cells.
        header_lookup = {
            "date": date_col,
            "open": date_col + 1,
            "high": date_col + 2,
            "low": date_col + 3,
            "close": date_col + 4,
        }
        if date_col + 5 < len(first_cells):
            header_lookup["volume"] = date_col + 5
        data_lines = lines

    rows: list[dict] = []
    for ln in data_lines:
        cells = _split(ln, sep)
        if len(cells) <= max(header_lookup.values()):
            continue
        d = _parse_date(cells[header_lookup["date"]])
        if d is None:
            continue
        try:
            o = _parse_num(cells[header_lookup["open"]])
            h = _parse_num(cells[header_lookup["high"]])
            lo = _parse_num(cells[header_lookup["low"]])
            c = _parse_num(cells[header_lookup["close"]])
        except (KeyError, IndexError):
            continue
        if None in (o, h, lo, c):
            continue
        # Volume + prev_close optional.
        v = 0
        if "volume" in header_lookup:
            v_parsed = _parse_num(cells[header_lookup["volume"]])
            v = int(v_parsed) if v_parsed is not None else 0
        pc = None
        if "prev_close" in header_lookup:
            pc = _parse_num(cells[header_lookup["prev_close"]])
        rows.append({
            "date": d.isoformat(),
            "open": f"{o:.2f}",
            "high": f"{h:.2f}",
            "low": f"{lo:.2f}",
            "close": f"{c:.2f}",
            "volume": str(v),
            "prev_close": f"{pc:.2f}" if pc is not None else "",
        })
    return rows


def merge_into_csv(csv_path: Path, new_rows: list[dict]) -> tuple[int, int, int]:
    """Merge new_rows into the existing CSV. Returns (added, updated, unchanged)."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict] = {}
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                d = (row.get("date") or "").strip()
                if d:
                    existing[d] = row

    added = updated = unchanged = 0
    for r in new_rows:
        d = r["date"]
        if d in existing:
            # Update only if values changed
            same = all(existing[d].get(k, "") == r.get(k, "") for k in _OUT_CSV_HEADER)
            if same:
                unchanged += 1
            else:
                existing[d] = r
                updated += 1
        else:
            existing[d] = r
            added += 1

    rows_out = [existing[d] for d in sorted(existing.keys())]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_OUT_CSV_HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_out)
    return added, updated, unchanged


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--symbol", required=True, help="Ticker (uppercased automatically)")
    p.add_argument("--input", help="Path to pasted table file. Defaults to stdin.")
    p.add_argument("--data-dir", default="data", help="Root of the CSV cache (default: data/)")
    p.add_argument("--dry-run", action="store_true", help="Preview parsed rows; don't write.")
    args = p.parse_args()

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    rows = parse_table(text)
    if not rows:
        print("ERROR: parsed 0 rows. Check the input format.", file=sys.stderr)
        return 2

    symbol = args.symbol.upper()
    csv_path = Path(args.data_dir).expanduser().resolve() / "ohlcv" / f"{symbol}.csv"

    if args.dry_run:
        print(f"Would write {len(rows)} parsed rows to {csv_path}", file=sys.stderr)
        print("Sample (first 3):", file=sys.stderr)
        for r in rows[:3]:
            print(f"  {r}", file=sys.stderr)
        return 0

    added, updated, unchanged = merge_into_csv(csv_path, rows)
    print(
        f"{symbol}: {added} added, {updated} updated, {unchanged} unchanged → {csv_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
