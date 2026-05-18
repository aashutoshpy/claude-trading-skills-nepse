#!/usr/bin/env python3
"""nepse-market-breadth-analyzer — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from breadth_calculator import BreadthInputs, BreadthResult, compute_breadth

from common.nepse import NepseClient


def collect_inputs(
    client: NepseClient, *, history_days: int, limit: int | None
) -> list[BreadthInputs]:
    constituents = client.list_constituents()
    if limit:
        constituents = constituents[:limit]
    end = date.today()
    start = end - timedelta(days=int(history_days * 1.6))
    out: list[BreadthInputs] = []
    failures = 0
    for sec in constituents:
        try:
            bars = client.get_ohlcv(sec.symbol, start, end)
        except Exception as exc:
            failures += 1
            print(f"WARN: {sec.symbol}: {exc}", file=sys.stderr)
            continue
        if not bars:
            continue
        out.append(BreadthInputs(security=sec, bars=sorted(bars, key=lambda b: b.day)))
    if failures:
        print(f"INFO: {failures} symbols failed to fetch", file=sys.stderr)
    return out


def write_reports(result: BreadthResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"nepse_breadth_{result.as_of}"
    json_path = output_dir / f"{base}.json"
    md_path = output_dir / f"{base}.md"
    json_path.write_text(
        json.dumps(_to_dict(result), indent=2), encoding="utf-8"
    )
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    return json_path, md_path


def _to_dict(r: BreadthResult) -> dict:
    return {
        "as_of": r.as_of,
        "regime": r.regime,
        "totals": {
            "universe": r.total_universe,
            "eligible": r.eligible,
            "advances": r.advances,
            "declines": r.declines,
            "unchanged": r.unchanged,
        },
        "new_52w_highs": r.new_52w_highs,
        "new_52w_lows": r.new_52w_lows,
        "pct_above_50sma": r.pct_above_50sma,
        "pct_above_200sma": r.pct_above_200sma,
        "ad_ratio": r.ad_ratio,
        "sector_breakdown": r.sector_breakdown,
    }


def _render_markdown(r: BreadthResult) -> str:
    lines = [
        f"# NEPSE Market Breadth — {r.as_of}",
        "",
        f"**Regime:** `{r.regime}`",
        "",
        "| Indicator | Value |",
        "|---|---:|",
        f"| Universe / eligible | {r.total_universe} / {r.eligible} |",
        f"| Advances / Declines / Unchanged | {r.advances} / {r.declines} / {r.unchanged} |",
        f"| A/D ratio | {r.ad_ratio} |",
        f"| New 52-wk highs / lows | {r.new_52w_highs} / {r.new_52w_lows} |",
        f"| % above 50-SMA | {r.pct_above_50sma}% |",
        f"| % above 200-SMA | {r.pct_above_200sma}% |",
        "",
        "## Sector Participation",
        "",
        "| Sector | Eligible | Advances | Declines | A/D |",
        "|---|---:|---:|---:|---:|",
    ]
    for sec_id, s in sorted(r.sector_breakdown.items()):
        adv, dec = s.get("advances", 0), s.get("declines", 0)
        ad = round(adv / dec, 2) if dec else "∞" if adv else "0"
        lines.append(f"| {sec_id} | {s.get('eligible', 0)} | {adv} | {dec} | {ad} |")
    lines += [
        "",
        "**Reading guide:**",
        "- `BULL_BROAD`  : size up — both 50-SMA and 200-SMA breadth in bull zone",
        "- `BULL_NARROW` : market is rising but leadership is thin; favor leaders only",
        "- `NEUTRAL`     : keep current exposure; watch for regime change",
        "- `BEAR_NARROW` : tighten stops, no new positions",
        "- `BEAR_BROAD`  : raise cash, exit weakest holdings",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE market breadth analyzer")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--as-of", type=str, default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument("--history-days", type=int, default=300)
    parser.add_argument("--limit", type=int, default=None, help="Limit universe size (testing)")
    parser.add_argument("--new-high-lookback", type=int, default=252)
    parser.add_argument("--min-trading-days", type=int, default=150)
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    inputs = collect_inputs(client, history_days=args.history_days, limit=args.limit)
    if not inputs:
        print("ERROR: no constituents fetched", file=sys.stderr)
        return 1
    as_of = args.as_of or date.today().isoformat()
    result = compute_breadth(
        inputs,
        as_of=as_of,
        new_high_lookback=args.new_high_lookback,
        min_trading_days=args.min_trading_days,
    )
    json_path, md_path = write_reports(result, args.output_dir)
    print(f"  Wrote breadth report:\n    {json_path}\n    {md_path}\n  Regime: {result.regime}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
