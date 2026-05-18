#!/usr/bin/env python3
"""nepse-uptrend-analyzer — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from uptrend_calculator import UptrendResult, build_result

from common.nepse import NepseClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE uptrend ratio analyzer")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--history-days", type=int, default=252,
                        help="Trading-day window for ratio history (default 252)")
    parser.add_argument("--lookback-days", type=int, default=500,
                        help="Calendar days of OHLCV to fetch per name (200-SMA needs ≥200 trading days)")
    parser.add_argument("--limit", type=int, default=None, help="Limit universe (testing)")
    parser.add_argument("--no-divergence", action="store_true",
                        help="Skip the divergence check (no need to fetch NEPSE index)")
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    constituents = client.list_constituents()
    if args.limit:
        constituents = constituents[: args.limit]
    if not constituents:
        print("ERROR: no constituents fetched", file=sys.stderr)
        return 1

    end = date.today()
    start = end - timedelta(days=int(args.lookback_days * 1.6))
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

    index_series = None
    if not args.no_divergence:
        try:
            index_series = client.get_index("NEPSE", start, end) or None
        except Exception as exc:
            print(f"WARN: get_index(NEPSE) failed: {exc}", file=sys.stderr)

    today = date.today()
    result = build_result(
        bars_by_symbol,
        today=today,
        index_series=index_series,
        history_days=args.history_days,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"nepse_uptrend_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_uptrend_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(f"  Uptrend ratio: {result.current_ratio}%  Regime: {result.regime}")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: UptrendResult) -> dict:
    return {
        "as_of": r.as_of.isoformat(),
        "current_ratio": r.current_ratio,
        "eligible_today": r.eligible_today,
        "regime": r.regime,
        "divergence_detected": r.divergence_detected,
        "divergence_note": r.divergence_note,
        "history": [asdict(p) for p in r.history],
    }


def _render_markdown(r: UptrendResult) -> str:
    lines = [
        f"# NEPSE Uptrend Ratio — {r.as_of.isoformat()}",
        "",
        f"**Current ratio:** {r.current_ratio}% of {r.eligible_today} eligible names "
        f"above their 200-day SMA",
        f"**Regime:** `{r.regime}`",
        "",
    ]
    if r.divergence_detected:
        lines.append(f"⚠️ **Divergence:** {r.divergence_note}")
    else:
        lines.append(f"_No divergence: {r.divergence_note}_")
    lines += [
        "",
        "## Recent History (last 20 sessions)",
        "",
        "| Date | Ratio | Eligible | Above 200-SMA |",
        "|---|---:|---:|---:|",
    ]
    for p in r.history[-20:]:
        lines.append(f"| {p.day} | {p.ratio}% | {p.eligible} | {p.above_200sma} |")
    lines += [
        "",
        "**Reading guide:** ≥70% = strong; 50-70% = uptrend; 30-50% = neutral; <30% = downtrend.",
        "Ratio falling while NEPSE composite makes new highs = bearish breadth divergence.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
