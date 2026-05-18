#!/usr/bin/env python3
"""nepse-kanchi-dividend-sop — quality check CLI."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from kanchi_scorer import KanchiScore, score_candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE Kanchi-style quality check on dividend candidates")
    parser.add_argument("--candidates-json", type=Path, required=True,
                        help="JSON output from nepse-value-dividend-screener")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    if not args.candidates_json.exists():
        print(f"ERROR: candidates JSON not found: {args.candidates_json}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(args.candidates_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not parse candidates JSON: {exc}", file=sys.stderr)
        return 1

    candidates = payload.get("candidates") or []
    scores = score_candidates(candidates)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_kanchi_quality_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_kanchi_quality_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(), "scores": [asdict(s) for s in scores]},
                   indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(scores, today), encoding="utf-8")
    print(f"  Scored {len(scores)} candidates:\n    {json_path}\n    {md_path}")
    return 0


def _render_markdown(scores: list[KanchiScore], today: date) -> str:
    lines = [
        f"# NEPSE Kanchi Dividend Quality — {today.isoformat()}",
        "",
        f"**Candidates scored:** {len(scores)}    "
        f"**PASS:** {sum(1 for s in scores if s.verdict == 'PASS')}    "
        f"**WATCH:** {sum(1 for s in scores if s.verdict == 'WATCH')}",
        "",
        "| Symbol | Sector | Verdict | Score | Yield | Cash% of Div | vs SMA200 |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for s in scores:
        ratio = f"{s.cash_bonus_ratio:.0%}" if s.cash_bonus_ratio is not None else "—"
        dist = f"{s.distance_to_sma200_pct:+.1f}%" if s.distance_to_sma200_pct is not None else "—"
        lines.append(
            f"| **{s.symbol}** | {s.sector} | `{s.verdict}` | {s.score} | "
            f"{s.yield_pct}% | {ratio} | {dist} |"
        )
    if not scores:
        lines.append("| _(no candidates)_ | | | | | | |")
    lines += [
        "",
        "## Notes per Candidate",
        "",
    ]
    for s in scores:
        if not s.notes:
            continue
        lines.append(f"### {s.symbol}")
        for n in s.notes:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
