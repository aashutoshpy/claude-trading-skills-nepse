#!/usr/bin/env python3
"""nepse-capital-gains-tax-notes — CLI entry point."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from tax_calculator import TaxRates, estimate_tax

from common.nepse import format_npr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE capital gains tax estimator")
    parser.add_argument("--symbol", type=str, default="POSITION")
    parser.add_argument("--entry-price", type=float)
    parser.add_argument("--exit-price", type=float)
    parser.add_argument("--shares", type=float)
    parser.add_argument("--holding-days", type=int)
    parser.add_argument("--entry-date", type=str, help="YYYY-MM-DD; alternative to --holding-days")
    parser.add_argument("--batch-csv", type=Path, default=None)
    args = parser.parse_args(argv)

    rates = TaxRates.load()

    if args.batch_csv:
        if not args.batch_csv.exists():
            print(f"ERROR: batch CSV not found: {args.batch_csv}", file=sys.stderr)
            return 1
        with args.batch_csv.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            today = date.today()
            for row in reader:
                try:
                    sym = (row.get("symbol") or "POSITION").strip().upper()
                    ep = float(row.get("entry_price") or 0)
                    xp = float(row.get("exit_price") or 0)
                    sh = float(row.get("shares") or 0)
                    entry_str = (row.get("entry_date") or "").strip()
                    if entry_str:
                        hd = (today - date.fromisoformat(entry_str)).days
                    else:
                        hd = int(row.get("holding_days") or 0)
                except (ValueError, KeyError):
                    continue
                est = estimate_tax(
                    symbol=sym, entry_price=ep, exit_price=xp, shares=sh,
                    holding_days=hd, rates=rates,
                )
                _print(est)
        return 0

    if not (args.entry_price and args.exit_price and args.shares):
        print("ERROR: --entry-price, --exit-price, --shares required (or use --batch-csv)",
              file=sys.stderr)
        return 1

    if args.entry_date:
        try:
            holding_days = (date.today() - date.fromisoformat(args.entry_date)).days
        except ValueError:
            print(f"ERROR: bad --entry-date: {args.entry_date}", file=sys.stderr)
            return 1
    elif args.holding_days is not None:
        holding_days = args.holding_days
    else:
        print("ERROR: --holding-days or --entry-date required", file=sys.stderr)
        return 1

    est = estimate_tax(
        symbol=args.symbol, entry_price=args.entry_price, exit_price=args.exit_price,
        shares=args.shares, holding_days=holding_days, rates=rates,
    )
    _print(est)
    return 0


def _print(est) -> None:
    print(
        f"{est.symbol}: {est.shares:g} shares  |  cost {format_npr(est.cost)}  |  "
        f"proceeds {format_npr(est.proceeds)}"
    )
    print(
        f"  Gross gain: {format_npr(est.gross_gain)}  |  "
        f"Holding: {est.holding_days} days → {'LONG' if est.is_long_term else 'SHORT'}-TERM "
        f"({est.rate_pct}% rate)"
    )
    print(
        f"  Tax: {format_npr(est.tax_npr)}  |  Net gain: {format_npr(est.net_gain)}  |  "
        f"Net return: {est.net_return_pct}%"
    )
    for n in est.notes:
        print(f"  - {n}")


if __name__ == "__main__":
    raise SystemExit(main())
