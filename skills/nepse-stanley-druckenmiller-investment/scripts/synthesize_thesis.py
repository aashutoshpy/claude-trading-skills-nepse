#!/usr/bin/env python3
"""nepse-stanley-druckenmiller-investment — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from druck_synthesizer import WEIGHTS, DruckResult, synthesize


def _load_json(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN: could not load {path}: {exc}", file=sys.stderr)
        return None


def _resolve_latest(reports_dir: Path, prefix: str) -> Path | None:
    if not reports_dir.is_dir():
        return None
    matches = sorted(reports_dir.glob(f"{prefix}_*.json"))
    return matches[-1] if matches else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE Druckenmiller-style synthesis")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--macro-json", type=Path, default=None)
    parser.add_argument("--uptrend-json", type=Path, default=None)
    parser.add_argument("--breadth-json", type=Path, default=None)
    parser.add_argument("--sectors-json", type=Path, default=None)
    parser.add_argument("--top-json", type=Path, default=None)
    parser.add_argument("--distrib-json", type=Path, default=None)
    args = parser.parse_args(argv)

    result = synthesize(
        macro_json=_load_json(args.macro_json or _resolve_latest(args.reports_dir, "nepse_macro_regime")),
        uptrend_json=_load_json(args.uptrend_json or _resolve_latest(args.reports_dir, "nepse_uptrend")),
        breadth_json=_load_json(args.breadth_json or _resolve_latest(args.reports_dir, "nepse_breadth")),
        sectors_json=_load_json(args.sectors_json or _resolve_latest(args.reports_dir, "nepse_sectors")),
        top_json=_load_json(args.top_json or _resolve_latest(args.reports_dir, "nepse_top_risk")),
        distrib_json=_load_json(args.distrib_json or _resolve_latest(args.reports_dir, "nepse_distribution_days")),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_druckenmiller_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_druckenmiller_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result, today), indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(result, today), encoding="utf-8")
    print(f"  Bias: {result.bias} (score {result.score}/100)")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: DruckResult, today: date) -> dict:
    return {
        "as_of": today.isoformat(),
        "score": r.score,
        "bias": r.bias,
        "tilt": r.tilt,
        "weights": WEIGHTS,
        "components": r.components,
    }


def _render_markdown(r: DruckResult, today: date) -> str:
    lines = [
        f"# NEPSE Druckenmiller Synthesis — {today.isoformat()}",
        "",
        f"**Composite score:** {r.score}/100",
        f"**Bias:** `{r.bias}`",
        "",
        "## Recommended Portfolio Tilt",
        "",
        f"- Exposure: **{r.tilt['exposure_pct_range']}**",
        f"- Names: **{r.tilt['name_count_range']}**",
        f"- Sector tilt: {r.tilt['sector_tilt']}",
        "",
        "## Components",
        "",
        "| Component | Weight | Score | Reason |",
        "|---|---:|---:|---|",
    ]
    for k, w in WEIGHTS.items():
        c = r.components[k]
        lines.append(f"| {k} | {w:.0%} | {c['score']} | {c['reason']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
