#!/usr/bin/env python3
"""nepse-earnings-trade-analyzer — CLI entry point."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from earnings_scorer import EarningsScore, score_earnings

from common.nepse import NepseClient


def _parse_batch_csv(path: Path) -> list[tuple[str, date]]:
    out: list[tuple[str, date]] = []
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            sym = (row.get("symbol") or "").strip().upper()
            rd_str = (row.get("report_date") or "").strip()
            if not sym or not rd_str:
                continue
            try:
                rd = date.fromisoformat(rd_str)
            except ValueError:
                continue
            out.append((sym, rd))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE post-result earnings analyzer")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--symbol", type=str, help="Single ticker (paired with --report-date)")
    parser.add_argument("--report-date", type=str, help="Report date YYYY-MM-DD")
    parser.add_argument("--batch-csv", type=Path, help="CSV with columns symbol,report_date")
    parser.add_argument("--history-days", type=int, default=500)
    args = parser.parse_args(argv)

    if args.batch_csv:
        targets = _parse_batch_csv(args.batch_csv)
    elif args.symbol and args.report_date:
        try:
            rd = date.fromisoformat(args.report_date)
        except ValueError:
            print(f"ERROR: bad --report-date: {args.report_date}", file=sys.stderr)
            return 1
        targets = [(args.symbol.upper(), rd)]
    else:
        print("ERROR: pass --symbol + --report-date, or --batch-csv", file=sys.stderr)
        return 1

    if not targets:
        print("ERROR: no symbols to analyze", file=sys.stderr)
        return 1

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    scores: list[EarningsScore] = []
    for sym, rd in targets:
        end = date.today()
        start = end - timedelta(days=int(args.history_days * 1.6))
        try:
            bars = client.get_ohlcv(sym, start, end)
        except Exception as exc:
            print(f"WARN: get_ohlcv({sym}) failed: {exc}", file=sys.stderr)
            continue
        if not bars:
            print(f"WARN: no bars for {sym}", file=sys.stderr)
            continue
        scores.append(score_earnings(bars, symbol=sym, report_date=rd))

    scores.sort(key=lambda s: s.score, reverse=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_earnings_analysis_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_earnings_analysis_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(),
                    "scores": [_to_dict(s) for s in scores]},
                   indent=2, default=str),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(scores, today), encoding="utf-8")
    print(f"  Scored {len(scores)} reports:\n    {json_path}\n    {md_path}")
    return 0


def _to_dict(s: EarningsScore) -> dict:
    out = asdict(s)
    out["report_date"] = s.report_date.isoformat()
    out["reaction_date"] = s.reaction_date.isoformat() if s.reaction_date else None
    return out


def _render_markdown(scores: list[EarningsScore], today: date) -> str:
    lines = [
        f"# NEPSE Post-Result Analysis — {today.isoformat()}",
        "",
        f"**Reports scored:** {len(scores)}",
        "",
        "| Symbol | Report | Reaction | Rating | Score | Gap | Stage | Vol× | dMA200 | dMA50 |",
        "|---|---|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for s in scores:
        gap = f"{s.gap_pct:+.1f}%" if s.gap_pct is not None else "—"
        d200 = f"{s.distance_to_ma200_pct:+.1f}%" if s.distance_to_ma200_pct is not None else "—"
        d50 = f"{s.distance_to_ma50_pct:+.1f}%" if s.distance_to_ma50_pct is not None else "—"
        vol = f"{s.volume_surge:.1f}" if s.volume_surge is not None else "—"
        lines.append(
            f"| **{s.symbol}** | {s.report_date} | {s.reaction_date or '—'} | "
            f"`{s.rating}` | {s.score} | {gap} | {s.trend_stage} | {vol} | {d200} | {d50} |"
        )
    if not scores:
        lines.append("| _(no reports scored)_ | | | | | | | | | |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
