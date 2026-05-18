#!/usr/bin/env python3
"""nepse-value-dividend-screener — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from dividend_scorer import parse_dividends_csv, score_universe

from common.nepse import NepseClient, format_npr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE value + dividend screener")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument(
        "--dividends",
        type=Path,
        default=None,
        help="CSV with columns: symbol, cash_div_pct, bonus_div_pct, [reported_at]. "
             "Without this, the screener returns an empty result (NEPSE backends do not "
             "expose structured dividend feeds — see SKILL.md for the rationale).",
    )
    parser.add_argument("--min-yield", type=float, default=5.0, help="Minimum yield %% to include")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--history-days", type=int, default=300)
    parser.add_argument("--limit", type=int, default=None, help="Limit universe (testing)")
    args = parser.parse_args(argv)

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    dividends = {}
    if args.dividends:
        if not args.dividends.exists():
            print(f"ERROR: dividend CSV not found: {args.dividends}", file=sys.stderr)
            return 1
        dividends = parse_dividends_csv(args.dividends.read_text(encoding="utf-8"))
        print(f"  Loaded dividend records for {len(dividends)} symbols", file=sys.stderr)
    else:
        print(
            "WARN: --dividends not supplied; screener will return zero rows. "
            "See SKILL.md for the recommended CSV format.",
            file=sys.stderr,
        )

    constituents = client.list_constituents()
    if args.limit:
        constituents = constituents[: args.limit]
    if not constituents:
        print("ERROR: no NEPSE constituents fetched", file=sys.stderr)
        return 1

    # Fetch OHLCV only for names that have a dividend record (saves a lot of calls)
    target_symbols = {s.symbol.upper() for s in constituents} & set(dividends.keys())
    target_constituents = [s for s in constituents if s.symbol.upper() in target_symbols]

    end = date.today()
    start = end - timedelta(days=int(args.history_days * 1.6))
    bars_by_symbol: dict[str, list] = {}
    failures = 0
    for sec in target_constituents:
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

    candidates = score_universe(
        target_constituents,
        bars_by_symbol=bars_by_symbol,
        dividends=dividends,
        min_yield_pct=args.min_yield,
    )[: args.top]

    today = date.today()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"nepse_dividends_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_dividends_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(), "candidates": candidates}, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(candidates, today), encoding="utf-8")
    print(f"  Wrote {len(candidates)} candidates:\n    {json_path}\n    {md_path}")
    return 0


def _render_markdown(rows: list[dict], today: date) -> str:
    lines = [
        f"# NEPSE Dividend Screener — {today.isoformat()}",
        "",
        f"**Candidates:** {len(rows)}",
        "",
        "| Symbol | Sector | Price | Yield | Cash % | Bonus % | Total % | vs SMA200 | Margin |",
        "|---|---|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in rows:
        dist = f"{r['distance_to_sma200_pct']:+.1f}%" if r["distance_to_sma200_pct"] is not None else "—"
        lines.append(
            f"| **{r['symbol']}** | {r['sector']} | {format_npr(r['price'], decimals=2)} | "
            f"{r['yield_pct']}% | {r['cash_div_pct']} | {r['bonus_div_pct']} | "
            f"{r['total_div_pct']} | {dist} | {'✓' if r['margin_eligible'] else '·'} |"
        )
    if not rows:
        lines.append("| _(no candidates — supply `--dividends <csv>`)_ | | | | | | | | |")
    lines += [
        "",
        "**Notes:** Yield = (cash + bonus div %) × NPR 100 face value / current price.",
        "Negative `vs SMA200` = trading below 200-SMA = value-y entry zone.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
