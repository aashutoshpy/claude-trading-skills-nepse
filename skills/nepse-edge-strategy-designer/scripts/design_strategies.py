#!/usr/bin/env python3
"""nepse-edge-strategy-designer — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
import yaml
from strategy_designer import design_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE edge strategy designer")
    parser.add_argument("--signals-json", type=Path, required=True,
                        help="JSON from nepse-edge-signal-aggregator")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/strategy_drafts"))
    parser.add_argument("--summary-dir", type=Path, default=Path("reports"))
    parser.add_argument("--include-watch", action="store_true",
                        help="Also design drafts for WATCH-status signals")
    args = parser.parse_args(argv)

    if not args.signals_json.exists():
        print(f"ERROR: signals JSON not found: {args.signals_json}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(args.signals_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not parse signals JSON: {exc}", file=sys.stderr)
        return 1

    signals = payload.get("signals") or []
    today = date.today()
    drafts = design_all(signals, today=today, include_watch=args.include_watch)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.summary_dir.mkdir(parents=True, exist_ok=True)

    for draft in drafts:
        path = args.output_dir / f"{draft['strategy_id']}.yaml"
        path.write_text(yaml.safe_dump(draft, sort_keys=False), encoding="utf-8")
        print(f"  Wrote {path.name}")

    summary_path = args.summary_dir / f"nepse_strategy_drafts_{today.isoformat()}.json"
    summary_path.write_text(
        json.dumps({"as_of": today.isoformat(), "drafts": drafts}, indent=2),
        encoding="utf-8",
    )
    print(f"  Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
