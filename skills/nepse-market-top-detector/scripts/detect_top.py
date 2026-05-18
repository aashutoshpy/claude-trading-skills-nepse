#!/usr/bin/env python3
"""nepse-market-top-detector — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from top_scorer import WEIGHTS, TopRiskResult, compute_top_risk


def _load_json(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN: could not load {path}: {exc}", file=sys.stderr)
        return None


def _resolve_latest(reports_dir: Path, prefix: str) -> Path | None:
    """Find the most recent reports/<prefix>_*.json."""
    if not reports_dir.is_dir():
        return None
    matches = sorted(reports_dir.glob(f"{prefix}_*.json"))
    return matches[-1] if matches else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE market top detector (aggregator)")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"),
                        help="Directory to scan for upstream-skill outputs (when explicit "
                             "paths not provided)")
    parser.add_argument("--distribution-json", type=Path, default=None)
    parser.add_argument("--uptrend-json", type=Path, default=None)
    parser.add_argument("--sectors-json", type=Path, default=None)
    parser.add_argument("--breadth-json", type=Path, default=None)
    args = parser.parse_args(argv)

    distrib = args.distribution_json or _resolve_latest(args.reports_dir, "nepse_distribution_days")
    uptrend = args.uptrend_json or _resolve_latest(args.reports_dir, "nepse_uptrend")
    sectors = args.sectors_json or _resolve_latest(args.reports_dir, "nepse_sectors")
    breadth = args.breadth_json or _resolve_latest(args.reports_dir, "nepse_breadth")

    result = compute_top_risk(
        distribution_json=_load_json(distrib),
        uptrend_json=_load_json(uptrend),
        sectors_json=_load_json(sectors),
        breadth_json=_load_json(breadth),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_top_risk_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_top_risk_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result, today), indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(result, today), encoding="utf-8")
    print(f"  Top-risk score: {result.score}/100    Level: {result.level}")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: TopRiskResult, today: date) -> dict:
    return {
        "as_of": today.isoformat(),
        "score": r.score,
        "level": r.level,
        "weights": WEIGHTS,
        "components": r.components,
    }


def _render_markdown(r: TopRiskResult, today: date) -> str:
    lines = [
        f"# NEPSE Top-Risk Detector — {today.isoformat()}",
        "",
        f"**Composite score:** {r.score}/100",
        f"**Level:** `{r.level}`",
        "",
        "## Components",
        "",
        "| Component | Weight | Score | Reason |",
        "|---|---:|---:|---|",
    ]
    for key, weight in WEIGHTS.items():
        c = r.components[key]
        lines.append(f"| {key} | {weight:.0%} | {c['score']} | {c['reason']} |")
    lines += [
        "",
        "**Action guide:**",
        "- LOW (≤30): continue normal sizing",
        "- ELEVATED (31-55): tighten stops, pause new larger positions",
        "- HIGH (56-75): reduce exposure, only top-quality setups",
        "- EXTREME (76-100): raise cash, exit weakest holdings",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
