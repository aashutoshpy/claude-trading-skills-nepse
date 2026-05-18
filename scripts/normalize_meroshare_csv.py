#!/usr/bin/env python3
"""Normalize a raw MeroShare portfolio export into the tracker schema.

MeroShare's exported CSV uses verbose column names and has no cost-basis
column at all. Our nepse-portfolio-tracker expects:

    symbol, shares, avg_cost, entry_date, is_margin

This script:
1. Reads `data/meroshare_export.csv` (raw export, MeroShare schema).
2. Reads `data/cost_basis.csv` (user-maintained side file with cost basis).
3. Joins on `symbol` and writes `data/nepse_portfolio.csv` in tracker schema.
4. Reports symbols missing cost basis to stderr so the user can fill them in.

MeroShare CSV columns (case-insensitive, quoted):
    "S.N", "Scrip", "Current Balance",
    "Last Closing Price", "Value as of Last Closing Price",
    "Last Transaction Price (LTP)", "Value as of LTP"

Side-file (`data/cost_basis.csv`) schema:
    symbol,avg_cost,entry_date,is_margin

A template lives at `data/cost_basis.csv.example`.

Exit codes:
    0 — output written; every symbol has cost basis
    1 — MeroShare CSV missing or unparseable; nothing written
    3 — output written but some symbols missing cost basis (partial)

Re-run idempotently — output is sorted by symbol for diff-stability.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

_MEROSHARE_DEFAULT = "data/meroshare_export.csv"
_COST_BASIS_DEFAULT = "data/cost_basis.csv"
_OUTPUT_DEFAULT = "data/nepse_portfolio.csv"

_TRACKER_SCHEMA = ["symbol", "shares", "avg_cost", "entry_date", "is_margin"]


def _norm_header(s: str) -> str:
    """Normalize a header for case/whitespace-insensitive lookup."""
    return s.strip().lower().replace(".", "")


# MeroShare → tracker column mapping (after normalization).
_MEROSHARE_HEADER_MAP = {
    "scrip": "symbol",
    "current balance": "shares",
}


def parse_meroshare_csv(path: Path) -> list[dict]:
    """Return a list of {symbol, shares} dicts from the MeroShare export.

    Tolerates MeroShare's quoted format and verbose column names.
    Returns [] if the file is empty.
    """
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return rows
        # Build a lookup: normalized header → original header
        keymap = {_norm_header(k): k for k in reader.fieldnames if k}
        # Confirm we recognize the MeroShare schema
        missing = [k for k in _MEROSHARE_HEADER_MAP if k not in keymap]
        if missing:
            raise ValueError(
                f"MeroShare CSV at {path} missing required columns: "
                f"{missing}. Saw: {list(reader.fieldnames)}"
            )
        for row in reader:
            symbol = (row.get(keymap["scrip"]) or "").strip().upper()
            if not symbol:
                continue
            shares_raw = (row.get(keymap["current balance"]) or "").strip()
            try:
                shares = float(shares_raw)
            except ValueError:
                continue
            if shares <= 0:
                # Zero-balance rows are common after sales; skip.
                continue
            rows.append({"symbol": symbol, "shares": shares})
    return rows


def parse_cost_basis_csv(path: Path) -> dict[str, dict]:
    """Return {symbol: {avg_cost, entry_date, is_margin}} from the side file.

    Missing file → empty dict (caller decides whether that's fatal).
    Lines beginning with `#` are treated as comments and skipped.
    """
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    # Strip `#`-prefixed comment lines + blank lines BEFORE csv parsing
    # so DictReader's header detection lands on the real header row.
    text = path.read_text(encoding="utf-8")
    clean_lines = [
        ln for ln in text.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    if not clean_lines:
        return out
    import io
    reader = csv.DictReader(io.StringIO("\n".join(clean_lines)))
    for row in reader:
        symbol = (row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        out[symbol] = {
            "avg_cost": (row.get("avg_cost") or "").strip(),
            "entry_date": (row.get("entry_date") or "").strip(),
            "is_margin": (row.get("is_margin") or "false").strip().lower(),
        }
    return out


def merge(
    meroshare_rows: list[dict],
    cost_basis: dict[str, dict],
) -> tuple[list[dict], list[str]]:
    """Return (normalized rows, list of symbols missing cost basis)."""
    out: list[dict] = []
    missing: list[str] = []
    for r in meroshare_rows:
        symbol = r["symbol"]
        shares_str = (
            str(int(r["shares"]))
            if r["shares"].is_integer()
            else f"{r['shares']:.4f}".rstrip("0").rstrip(".")
        )
        basis = cost_basis.get(symbol)
        if basis and basis["avg_cost"]:
            out.append({
                "symbol": symbol,
                "shares": shares_str,
                "avg_cost": basis["avg_cost"],
                "entry_date": basis["entry_date"],
                "is_margin": basis["is_margin"],
            })
        else:
            out.append({
                "symbol": symbol,
                "shares": shares_str,
                "avg_cost": "",
                "entry_date": "",
                "is_margin": "false",
            })
            missing.append(symbol)
    out.sort(key=lambda r: r["symbol"])
    return out, missing


def write_tracker_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_TRACKER_SCHEMA)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--meroshare-csv", default=_MEROSHARE_DEFAULT,
                   help=f"Path to raw MeroShare export (default: {_MEROSHARE_DEFAULT})")
    p.add_argument("--cost-basis-csv", default=_COST_BASIS_DEFAULT,
                   help=f"Path to user-maintained cost basis file (default: {_COST_BASIS_DEFAULT})")
    p.add_argument("--output", default=_OUTPUT_DEFAULT,
                   help=f"Output path (default: {_OUTPUT_DEFAULT})")
    args = p.parse_args()

    meroshare_path = Path(args.meroshare_csv).expanduser().resolve()
    cost_basis_path = Path(args.cost_basis_csv).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not meroshare_path.exists():
        print(
            f"ERROR: MeroShare CSV not found at {meroshare_path}\n"
            f"  Export from meroshare.cdsc.com.np → My Portfolio → Export\n"
            f"  Save as {meroshare_path} (or pass --meroshare-csv <path>).",
            file=sys.stderr,
        )
        return 1

    try:
        meroshare_rows = parse_meroshare_csv(meroshare_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not meroshare_rows:
        print(f"ERROR: 0 positions parsed from {meroshare_path}", file=sys.stderr)
        return 1

    cost_basis = parse_cost_basis_csv(cost_basis_path)
    rows, missing = merge(meroshare_rows, cost_basis)

    write_tracker_csv(output_path, rows)

    total = len(rows)
    with_basis = total - len(missing)
    print(
        f"{total} positions normalized, {with_basis} with cost basis, "
        f"{len(missing)} missing.",
        file=sys.stderr,
    )
    print(f"  Output: {output_path}", file=sys.stderr)

    if missing:
        print(
            f"\nMissing cost basis for: {', '.join(missing)}\n"
            f"Add a row per symbol to {cost_basis_path}:\n"
            f"  symbol,avg_cost,entry_date,is_margin\n"
            f"  NABIL,1180.00,2025-12-15,false\n"
            f"\nThen re-run this script. The tracker's P&L / stop / margin checks\n"
            f"are skipped for any symbol without cost basis.",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
