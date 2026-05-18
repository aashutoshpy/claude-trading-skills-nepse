#!/usr/bin/env python3
"""nepse-ibd-distribution-day-monitor — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from distribution_days import DistributionResult, detect_distribution_days

from common.nepse import NepseClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE IBD distribution-day monitor")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--index", type=str, default="NEPSE", help="Index ID (default: NEPSE)")
    parser.add_argument("--window", type=int, default=25)
    parser.add_argument("--min-down-pct", type=float, default=0.2)
    parser.add_argument("--rally-cancel-pct", type=float, default=5.0)
    parser.add_argument("--history-days", type=int, default=120)
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    end = date.today()
    start = end - timedelta(days=int(args.history_days * 1.6))
    bars = client.get_index(args.index, start, end)
    if not bars:
        print(f"ERROR: no bars for index {args.index}", file=sys.stderr)
        return 1

    result = detect_distribution_days(
        bars,
        window=args.window,
        min_down_pct=args.min_down_pct,
        rally_cancel_pct=args.rally_cancel_pct,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_distribution_days_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_distribution_days_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(f"  Active distribution days: {result.active_count}/{result.window}    Severity: {result.severity}")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: DistributionResult) -> dict:
    return {
        "as_of": r.as_of.isoformat(),
        "window": r.window,
        "min_down_pct": r.min_down_pct,
        "rally_cancel_pct": r.rally_cancel_pct,
        "active_count": r.active_count,
        "severity": r.severity,
        "distribution_days": [_dd_to_dict(d) for d in r.distribution_days],
    }


def _dd_to_dict(d) -> dict:
    out = asdict(d)
    out["day"] = d.day.isoformat()
    return out


def _render_markdown(r: DistributionResult) -> str:
    lines = [
        f"# NEPSE Distribution-Day Monitor — {r.as_of.isoformat()}",
        "",
        f"**Active distribution days:** {r.active_count} (window={r.window} sessions)",
        f"**Severity:** `{r.severity}`",
        "",
        "| Date | Prev → Close | %Δ | Volume Ratio | Cancelled? |",
        "|---|---|---:|---:|:---:|",
    ]
    for d in r.distribution_days:
        cancelled = "✓ cancelled" if d.cancelled else "—"
        lines.append(
            f"| {d.day} | {d.prev_close} → {d.close} | {d.pct_change:+.2f}% | "
            f"{d.volume_ratio}× | {cancelled} |"
        )
    if not r.distribution_days:
        lines.append("| _(no distribution days in window)_ | | | | |")
    lines += [
        "",
        "**Reading guide:** ≤2 = healthy; 3 = caution; 4 = risk; ≥5 = institutional distribution.",
        "Cancelled days = the index later rallied ≥ rally-cancel-pct above the d-day close.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
