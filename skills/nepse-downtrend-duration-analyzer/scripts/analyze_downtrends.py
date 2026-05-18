#!/usr/bin/env python3
"""nepse-downtrend-duration-analyzer — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from downtrend_detector import DowntrendSummary, detect_drawdowns, summarize

from common.nepse import NepseClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE downtrend duration analyzer")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--index", type=str, default="NEPSE")
    parser.add_argument("--min-depth-pct", type=float, default=10.0)
    parser.add_argument("--lookback-days", type=int, default=1825,
                        help="Calendar days of history to fetch (default: 5 years)")
    parser.add_argument("--since", type=str, default=None,
                        help="Optionally clip history to YYYY-MM-DD onward")
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    end = date.today()
    start = end - timedelta(days=args.lookback_days)
    bars = client.get_index(args.index, start, end)
    if not bars:
        print(f"ERROR: no bars for index {args.index}", file=sys.stderr)
        return 1

    if args.since:
        try:
            since = date.fromisoformat(args.since)
            bars = [b for b in bars if b.day >= since]
        except ValueError:
            print(f"ERROR: bad --since: {args.since}", file=sys.stderr)
            return 1

    drawdowns = detect_drawdowns(bars, min_depth_pct=args.min_depth_pct)
    summary = summarize(drawdowns)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_downtrend_history_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_downtrend_history_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(summary), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(summary, today, args.min_depth_pct), encoding="utf-8")
    print(f"  Drawdowns: {len(summary.drawdowns)} (completed: {summary.historical_count})")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(s: DowntrendSummary) -> dict:
    return {
        "historical_count": s.historical_count,
        "decline_days": {
            "p25": s.decline_days_p25, "median": s.decline_days_median,
            "p75": s.decline_days_p75, "max": s.decline_days_max,
        },
        "recovery_days": {
            "p25": s.recovery_days_p25, "median": s.recovery_days_median,
            "p75": s.recovery_days_p75, "max": s.recovery_days_max,
        },
        "in_progress": _dd_to_dict(s.in_progress) if s.in_progress else None,
        "drawdowns": [_dd_to_dict(d) for d in s.drawdowns],
    }


def _dd_to_dict(d) -> dict:
    out = asdict(d)
    out["peak_date"] = d.peak_date.isoformat()
    out["trough_date"] = d.trough_date.isoformat()
    out["recovery_date"] = d.recovery_date.isoformat() if d.recovery_date else None
    return out


def _render_markdown(s: DowntrendSummary, today: date, min_depth: float) -> str:
    lines = [
        f"# NEPSE Downtrend Duration Analysis — {today.isoformat()}",
        "",
        f"**Minimum drawdown:** {min_depth}%    "
        f"**Historical drawdowns (completed):** {s.historical_count}",
        "",
        "## Duration Distribution (trading days)",
        "",
        "| Metric | Decline | Recovery |",
        "|---|---:|---:|",
        f"| P25 | {s.decline_days_p25 or '—'} | {s.recovery_days_p25 or '—'} |",
        f"| Median | {s.decline_days_median or '—'} | {s.recovery_days_median or '—'} |",
        f"| P75 | {s.decline_days_p75 or '—'} | {s.recovery_days_p75 or '—'} |",
        f"| Max | {s.decline_days_max or '—'} | {s.recovery_days_max or '—'} |",
        "",
    ]
    if s.in_progress:
        ip = s.in_progress
        lines += [
            "## Drawdown in progress",
            "",
            f"- Peak: {ip.peak_date} at {ip.peak_close:,.0f}",
            f"- Current trough: {ip.trough_date} at {ip.trough_close:,.0f}",
            f"- Depth: {ip.depth_pct:.1f}%   Decline days: {ip.decline_days}",
        ]
        if s.decline_days_median:
            lines.append(f"- Median historical decline: {s.decline_days_median} days "
                         f"({'past median' if ip.decline_days > s.decline_days_median else 'within median'})")
        lines.append("")
    lines += [
        "## All drawdowns",
        "",
        "| Peak | Trough | Recovery | Depth | Decline (d) | Recovery (d) | Total (d) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for d in s.drawdowns:
        lines.append(
            f"| {d.peak_date} | {d.trough_date} | "
            f"{d.recovery_date or '_in progress_'} | {d.depth_pct:.1f}% | "
            f"{d.decline_days} | {d.recovery_days or '—'} | {d.total_days or '—'} |"
        )
    if not s.drawdowns:
        lines.append("| _(no drawdowns meeting threshold)_ | | | | | | |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
