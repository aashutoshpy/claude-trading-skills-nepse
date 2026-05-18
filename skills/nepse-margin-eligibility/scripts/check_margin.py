#!/usr/bin/env python3
"""nepse-margin-eligibility — CLI entry point."""

from __future__ import annotations

import argparse
import sys

import _path_setup  # noqa: F401
from margin_calculator import MarginRules, check_eligibility, compute_position

from common.nepse import Registry, format_npr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE margin eligibility + margin-call calculator")
    parser.add_argument("symbols", nargs="+", help="NEPSE ticker(s) to check")
    parser.add_argument("--entry-price", type=float, default=None,
                        help="Position entry price (NPR)")
    parser.add_argument("--shares", type=float, default=None,
                        help="Position size in shares")
    parser.add_argument("--margin-pct", type=float, default=None,
                        help="Initial margin % (default: SEBON minimum 30%%)")
    parser.add_argument("--current-price", type=float, default=None,
                        help="Current market price for distance-to-call")
    args = parser.parse_args(argv)

    try:
        registry = Registry.load()
        rules = MarginRules.load()
    except Exception as exc:
        print(f"ERROR: could not load config: {exc}", file=sys.stderr)
        return 1

    # Position mode requires entry_price + shares; otherwise plain eligibility
    if args.entry_price is not None or args.shares is not None:
        if not (args.entry_price and args.shares):
            print("ERROR: --entry-price AND --shares required for position mode", file=sys.stderr)
            return 1
        for sym in args.symbols:
            rep = compute_position(
                sym,
                entry_price=args.entry_price,
                shares=args.shares,
                margin_pct=args.margin_pct,
                current_price=args.current_price,
                registry=registry,
                rules=rules,
            )
            print(_format_position(rep))
        return 0

    for sym in args.symbols:
        chk = check_eligibility(sym, registry=registry, rules=rules)
        label = "ELIGIBLE" if chk.eligible else "NOT_ELIGIBLE"
        print(
            f"{chk.symbol}: {label}"
            + (f"   initial={chk.initial_pct:.0f}%   maintenance={chk.maintenance_pct:.0f}%"
               if chk.eligible else "")
        )
    return 0


def _format_position(rep) -> str:
    lines = [
        f"{rep.symbol}: {'ELIGIBLE' if rep.eligible else 'NOT_ELIGIBLE'}   "
        f"position cost={format_npr(rep.position_cost)}   "
        f"borrowed={format_npr(rep.borrowed)}   "
        f"equity={format_npr(rep.initial_equity)}"
    ]
    if rep.current_value is not None:
        lines.append(
            f"  Current equity (at {format_npr(rep.current_value / max(rep.position_cost / max(1, 1), 1))}): "
            f"{format_npr(rep.current_equity)}"
        )
        if rep.margin_call_price is not None and rep.pct_distance_to_call is not None:
            lines.append(
                f"  Margin call triggered below: {format_npr(rep.margin_call_price)}   "
                f"({rep.pct_distance_to_call:+.1f}% from current)"
            )
    elif rep.margin_call_price is not None:
        lines.append(f"  Margin call triggered below: {format_npr(rep.margin_call_price)}")
    if rep.warning:
        lines.append(f"  ⚠ {rep.warning}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
