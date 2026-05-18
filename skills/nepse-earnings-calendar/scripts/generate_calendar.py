#!/usr/bin/env python3
"""nepse-earnings-calendar — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from calendar_builder import CalendarResult, build_calendar, parse_earnings_csv

from common.nepse import Registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE quarterly-results calendar")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--earnings-csv", type=Path, default=None,
                        help="CSV with columns: symbol, quarter, fiscal_year, announced_at, expected_at")
    parser.add_argument("--weeks-forward", type=int, default=4)
    parser.add_argument("--filing-window-days", type=int, default=30)
    args = parser.parse_args(argv)

    registry = Registry.load()
    rows = None
    if args.earnings_csv:
        if not args.earnings_csv.exists():
            print(f"ERROR: earnings CSV not found: {args.earnings_csv}", file=sys.stderr)
            return 1
        rows = parse_earnings_csv(args.earnings_csv.read_text(encoding="utf-8"))

    today = date.today()
    result = build_calendar(
        registry,
        today=today,
        weeks_forward=args.weeks_forward,
        company_rows=rows,
        filing_window_days=args.filing_window_days,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"nepse_earnings_calendar_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_earnings_calendar_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(f"  Wrote calendar:\n    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: CalendarResult) -> dict:
    return {
        "as_of": r.as_of.isoformat(),
        "weeks_forward": r.weeks_forward,
        "quarter_windows": [
            {**asdict(w), "ends_on": w.ends_on.isoformat(),
             "filing_deadline": w.filing_deadline.isoformat()}
            for w in r.quarter_windows
        ],
        "company_rows": [
            {**asdict(r2),
             "announced_at": r2.announced_at.isoformat() if r2.announced_at else None,
             "expected_at": r2.expected_at.isoformat() if r2.expected_at else None}
            for r2 in r.company_rows
        ],
    }


def _render_markdown(r: CalendarResult) -> str:
    lines = [
        f"# NEPSE Earnings Calendar — {r.as_of.isoformat()}",
        "",
        f"**Forward window:** {r.weeks_forward} weeks",
        "",
        "## Quarter Windows",
        "",
        "| FY | Quarter | Ends | Filing Deadline | Type |",
        "|---|---|---|---|---|",
    ]
    if not r.quarter_windows:
        lines.append("| _(no quarter windows in horizon)_ | | | | |")
    for w in r.quarter_windows:
        kind = "audited (annual)" if w.is_audited else "unaudited (statutory T+30)"
        lines.append(f"| {w.fy} | Q{w.quarter} | {w.ends_on} | {w.filing_deadline} | {kind} |")
    lines += [
        "",
        "## Company Announcements",
        "",
    ]
    if not r.company_rows:
        lines.append("_(no per-company rows — supply --earnings-csv to populate)_")
    else:
        lines += [
            "| Symbol | FY / Q | Expected | Announced |",
            "|---|---|---|---|",
        ]
        for row in r.company_rows:
            lines.append(
                f"| {row.symbol} | {row.fiscal_year} {row.quarter} | "
                f"{row.expected_at or '—'} | {row.announced_at or '—'} |"
            )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
