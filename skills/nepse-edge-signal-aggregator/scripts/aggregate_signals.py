#!/usr/bin/env python3
"""nepse-edge-signal-aggregator — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
import yaml
from signal_aggregator import Signal, aggregate


def _load_tickets(tickets_dir: Path) -> list[dict]:
    out: list[dict] = []
    for path in sorted(tickets_dir.glob("edge_*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            print(f"WARN: skip {path}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            out.append(data)
    return out


def _leading_sectors_from(reports_dir: Path) -> list[str]:
    sectors_files = sorted(reports_dir.glob("nepse_sectors_*.json"))
    if not sectors_files:
        return []
    try:
        payload = json.loads(sectors_files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    sectors = payload.get("sectors") or []
    # Sort by first-window rank
    first_window = next(iter(sectors[0].get("ranks", {})), None) if sectors else None
    if not first_window:
        return []
    ranked = sorted(
        (s for s in sectors if first_window in s.get("ranks", {})),
        key=lambda s: s["ranks"][first_window],
    )
    return [s["sector_id"] for s in ranked[:3]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE edge signal aggregator")
    parser.add_argument("--tickets-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"),
                        help="For loading nepse-sector-analyst output for sector boost")
    parser.add_argument("--max-age-days", type=int, default=7)
    args = parser.parse_args(argv)

    if not args.tickets_dir.is_dir():
        print(f"ERROR: tickets dir not found: {args.tickets_dir}", file=sys.stderr)
        return 1

    tickets = _load_tickets(args.tickets_dir)
    if not tickets:
        print(f"WARN: no tickets in {args.tickets_dir}", file=sys.stderr)

    leading_sectors = _leading_sectors_from(args.reports_dir)
    today = date.today()
    signals = aggregate(tickets, today=today, max_age_days=args.max_age_days,
                        leading_sectors=leading_sectors)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"nepse_edge_signals_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_edge_signals_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({
            "as_of": today.isoformat(),
            "leading_sectors": leading_sectors,
            "signals": [asdict(s) for s in signals],
        }, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(signals, today, leading_sectors), encoding="utf-8")
    print(f"  Aggregated {len(signals)} signals from {len(tickets)} tickets")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _render_markdown(signals: list[Signal], today: date, leading: list[str]) -> str:
    lines = [
        f"# NEPSE Edge Signals — {today.isoformat()}",
        "",
        f"**Signals:** {len(signals)}    "
        f"**ACT:** {sum(1 for s in signals if s.status == 'ACT')}    "
        f"**WATCH:** {sum(1 for s in signals if s.status == 'WATCH')}",
        f"**Leading sectors:** {', '.join(leading) if leading else '—'}",
        "",
        "| Symbol | Sector | Status | Score | Confluence | Detectors |",
        "|---|---|---|---:|---:|---|",
    ]
    for s in signals:
        lines.append(
            f"| **{s.symbol}** | {s.sector} | `{s.status}` | {s.composite_score} | "
            f"{s.confluence} | {', '.join(s.detectors_flagged)} |"
        )
    if not signals:
        lines.append("| _(no signals)_ | | | | | |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
