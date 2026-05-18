#!/usr/bin/env python3
"""nepse-canslim-screener — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from canslim_scorer import CanslimRow, parse_fundamentals_csv, score_universe

from common.nepse import NepseClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE CANSLIM screener")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--fundamentals-csv", type=Path, default=None,
                        help="CSV: symbol, eps_latest, eps_prior_year, eps_3y_cagr, sales_3y_cagr")
    parser.add_argument("--uptrend-json", type=Path, default=None,
                        help="JSON output from nepse-uptrend-analyzer for the M factor")
    parser.add_argument("--require-strong-uptrend", action="store_true")
    parser.add_argument("--max-per-sector", type=int, default=5)
    parser.add_argument("--history-days", type=int, default=400)
    parser.add_argument("--limit", type=int, default=None, help="Limit universe (testing)")
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    fundamentals = {}
    if args.fundamentals_csv:
        if not args.fundamentals_csv.exists():
            print(f"ERROR: fundamentals CSV not found: {args.fundamentals_csv}", file=sys.stderr)
            return 1
        fundamentals = parse_fundamentals_csv(args.fundamentals_csv.read_text(encoding="utf-8"))
    else:
        print("WARN: --fundamentals-csv not supplied; C and A factors get neutral 50/100", file=sys.stderr)

    uptrend_regime = None
    if args.uptrend_json and args.uptrend_json.exists():
        try:
            payload = json.loads(args.uptrend_json.read_text(encoding="utf-8"))
            uptrend_regime = payload.get("regime")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARN: could not parse uptrend JSON: {exc}", file=sys.stderr)

    constituents = client.list_constituents()
    if args.limit:
        constituents = constituents[: args.limit]
    if not constituents:
        print("ERROR: no constituents fetched", file=sys.stderr)
        return 1

    end = date.today()
    start = end - timedelta(days=int(args.history_days * 1.6))
    bars_by_symbol: dict[str, list] = {}
    failures = 0
    for sec in constituents:
        try:
            bars = client.get_ohlcv(sec.symbol, start, end)
        except Exception as exc:
            failures += 1
            print(f"WARN: {sec.symbol}: {exc}", file=sys.stderr)
            continue
        if bars:
            bars_by_symbol[sec.symbol.upper()] = bars
    if failures:
        print(f"INFO: {failures} symbols failed to fetch", file=sys.stderr)

    index_bars = None
    try:
        index_bars = client.get_index("NEPSE", start, end) or None
    except Exception as exc:
        print(f"WARN: get_index(NEPSE) failed: {exc}", file=sys.stderr)

    rows = score_universe(
        constituents,
        bars_by_symbol=bars_by_symbol,
        index_bars=index_bars,
        fundamentals=fundamentals,
        uptrend_regime=uptrend_regime,
        require_strong_uptrend=args.require_strong_uptrend,
        max_per_sector=args.max_per_sector,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_canslim_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_canslim_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(),
                    "uptrend_regime": uptrend_regime,
                    "candidates": [asdict(r) for r in rows]},
                   indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(rows, today, uptrend_regime), encoding="utf-8")
    print(f"  Wrote {len(rows)} candidates:\n    {json_path}\n    {md_path}")
    return 0


def _render_markdown(rows: list[CanslimRow], today: date, uptrend_regime: str | None) -> str:
    lines = [
        f"# NEPSE CANSLIM Screener — {today.isoformat()}",
        "",
        f"**Market regime (M):** `{uptrend_regime or 'unknown'}`",
        f"**Candidates:** {len(rows)}",
        "",
        "| Symbol | Sector | Rating | Score | C | A | N | S | L | I | M |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        if r.skipped:
            lines.append(f"| _{r.symbol}_ | — | NO_MATCH | — | — | — | — | — | — | — | — |")
            lines.append(f"  - _{r.skip_reason}_")
            continue
        c = r.components
        lines.append(
            f"| **{r.symbol}** | {r.sector} | `{r.rating}` | {r.score} | "
            f"{c['C']['score']} | {c['A']['score']} | {c['N']['score']} | "
            f"{c['S']['score']} | {c['L']['score']} | {c['I']['score']} | {c['M']['score']} |"
        )
    if not rows:
        lines.append("| _(no candidates)_ | | | | | | | | | | |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
