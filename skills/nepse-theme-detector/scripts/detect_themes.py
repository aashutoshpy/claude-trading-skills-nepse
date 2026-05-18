#!/usr/bin/env python3
"""nepse-theme-detector — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from theme_engine import (
    BUILT_IN_THEMES,
    ThemeScore,
    parse_themes_csv,
    score_themes,
)


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
    parser = argparse.ArgumentParser(description="NEPSE theme detector")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--themes-csv", type=Path, default=None,
                        help="Optional user CSV adding themes to the built-in library")
    parser.add_argument("--builtin-only", action="store_true",
                        help="Ignore the CSV even if supplied")
    parser.add_argument("--sectors-json", type=Path, default=None)
    parser.add_argument("--breadth-json", type=Path, default=None)
    parser.add_argument("--macro-json", type=Path, default=None)
    parser.add_argument("--uptrend-json", type=Path, default=None)
    args = parser.parse_args(argv)

    themes = list(BUILT_IN_THEMES)
    if args.themes_csv and not args.builtin_only:
        if not args.themes_csv.exists():
            print(f"ERROR: themes CSV not found: {args.themes_csv}", file=sys.stderr)
            return 1
        themes.extend(parse_themes_csv(args.themes_csv.read_text(encoding="utf-8")))

    sectors = args.sectors_json or _resolve_latest(args.reports_dir, "nepse_sectors")
    breadth = args.breadth_json or _resolve_latest(args.reports_dir, "nepse_breadth")
    macro = args.macro_json or _resolve_latest(args.reports_dir, "nepse_macro_regime")
    uptrend = args.uptrend_json or _resolve_latest(args.reports_dir, "nepse_uptrend")

    scores = score_themes(
        themes,
        sectors_json=_load_json(sectors),
        breadth_json=_load_json(breadth),
        macro_json=_load_json(macro),
        uptrend_json=_load_json(uptrend),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_themes_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_themes_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(),
                    "themes": [_to_dict(s) for s in scores]},
                   indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(scores, today), encoding="utf-8")
    print(f"  Scored {len(scores)} themes:\n    {json_path}\n    {md_path}")
    return 0


def _to_dict(ts: ThemeScore) -> dict:
    return {
        "theme_id": ts.theme.theme_id,
        "display_name": ts.theme.display_name,
        "symbols": ts.theme.symbols,
        "primary_sectors": ts.theme.primary_sectors,
        "rationale": ts.theme.rationale,
        "score": ts.score,
        "status": ts.status,
        "components": ts.components,
    }


def _render_markdown(scores: list[ThemeScore], today: date) -> str:
    lines = [
        f"# NEPSE Theme Detector — {today.isoformat()}",
        "",
        f"**Themes scored:** {len(scores)}    "
        f"**Active:** {sum(1 for s in scores if s.status == 'ACTIVE')}    "
        f"**Developing:** {sum(1 for s in scores if s.status == 'DEVELOPING')}",
        "",
        "| Theme | Status | Score | Sector | Macro | Breadth | Recency | Symbols |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for ts in scores:
        c = ts.components
        lines.append(
            f"| **{ts.theme.display_name}** | `{ts.status}` | {ts.score} | "
            f"{c['sector']['score']} | {c['macro']['score']} | {c['breadth']['score']} | "
            f"{c['recency']['score']} | {', '.join(ts.theme.symbols[:5])} |"
        )
    if not scores:
        lines.append("| _(no themes)_ | | | | | | | |")
    lines += [
        "",
        "## Theme Notes",
        "",
    ]
    for ts in scores:
        if ts.status == "INACTIVE":
            continue
        lines.append(f"### {ts.theme.display_name}  (`{ts.status}`, score {ts.score})")
        lines.append(f"_{ts.theme.rationale}_")
        for k, comp in ts.components.items():
            lines.append(f"- **{k}** ({comp['score']}): {comp['reason']}")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
