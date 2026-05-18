#!/usr/bin/env python3
"""nepse-portfolio-tracker — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from portfolio_aggregator import (
    PortfolioSnapshot,
    build_snapshot,
    parse_portfolio_csv,
)

from common.nepse import NepseClient, Registry, format_npr
from common.nepse._config import load_rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE portfolio tracker")
    parser.add_argument("--portfolio-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--no-fetch-prices", action="store_true",
                        help="Skip price lookup (use avg_cost as 'current')")
    args = parser.parse_args(argv)

    if not args.portfolio_csv.exists():
        print(f"ERROR: portfolio CSV not found: {args.portfolio_csv}", file=sys.stderr)
        return 1

    positions = parse_portfolio_csv(args.portfolio_csv.read_text(encoding="utf-8"))
    if not positions:
        print("ERROR: no positions parsed from CSV", file=sys.stderr)
        return 1

    price_lookup: dict[str, float] = {}
    if not args.no_fetch_prices:
        try:
            client = NepseClient.create(backend=args.backend)
            end = date.today()
            start = end - timedelta(days=14)
            for pos in positions:
                try:
                    bars = client.get_ohlcv(pos.symbol, start, end)
                except Exception as exc:
                    print(f"WARN: get_ohlcv({pos.symbol}) failed: {exc}", file=sys.stderr)
                    continue
                if bars:
                    price_lookup[pos.symbol] = sorted(bars, key=lambda b: b.day)[-1].close
        except Exception as exc:
            print(f"WARN: could not create NepseClient: {exc}", file=sys.stderr)
            print("  Falling back to avg_cost as 'current'", file=sys.stderr)

    registry = Registry.load()
    rules = load_rules().get("margin") or {}
    snapshot = build_snapshot(
        positions,
        price_lookup=price_lookup,
        registry=registry,
        today=date.today(),
        initial_margin_pct=float(rules.get("initial_margin_pct", 30.0)),
        maintenance_margin_pct=float(rules.get("maintenance_margin_pct", 20.0)),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_portfolio_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_portfolio_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(snapshot), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(snapshot), encoding="utf-8")
    print(f"  Positions: {len(snapshot.positions)}    "
          f"Invested: {format_npr(snapshot.invested_total)}    "
          f"Current: {format_npr(snapshot.current_value_total)}    "
          f"P&L: {snapshot.unrealized_pnl_pct:+.2f}%")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(s: PortfolioSnapshot) -> dict:
    return {
        "as_of": s.as_of.isoformat(),
        "totals": {
            "invested": s.invested_total,
            "current_value": s.current_value_total,
            "unrealized_pnl_npr": s.unrealized_pnl_npr,
            "unrealized_pnl_pct": s.unrealized_pnl_pct,
            "position_count": len(s.positions),
        },
        "positions": [{**asdict(p)} for p in s.positions],
        "sector_breakdown": s.sector_breakdown,
        "sector_warnings": s.sector_warnings,
        "margin_warnings": s.margin_warnings,
    }


def _render_markdown(s: PortfolioSnapshot) -> str:
    lines = [
        f"# NEPSE Portfolio — {s.as_of.isoformat()}",
        "",
        f"**Positions:** {len(s.positions)}    "
        f"**Invested:** {format_npr(s.invested_total)}    "
        f"**Current:** {format_npr(s.current_value_total)}    "
        f"**P&L:** {format_npr(s.unrealized_pnl_npr)} ({s.unrealized_pnl_pct:+.2f}%)",
        "",
        "## Positions",
        "",
        "| Symbol | Sector | Shares | Avg Cost | Current | P&L | P&L % | Margin |",
        "|---|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for p in s.positions:
        margin_flag = "💰" if p.is_margin else ("✓" if p.margin_eligible else "·")
        lines.append(
            f"| **{p.symbol}** | {p.sector} | {p.shares:g} | {format_npr(p.avg_cost, decimals=2)} | "
            f"{format_npr(p.current_price, decimals=2)} | {format_npr(p.unrealized_pnl_npr)} | "
            f"{p.unrealized_pnl_pct:+.2f}% | {margin_flag} |"
        )
        for w in p.warnings:
            lines.append(f"  - ⚠ {w}")
    lines += [
        "",
        "## Sector Breakdown",
        "",
        "| Sector | Value | % of Portfolio | Positions |",
        "|---|---:|---:|---:|",
    ]
    for sec_id, entry in sorted(s.sector_breakdown.items(),
                                key=lambda kv: kv[1]["value_pct"], reverse=True):
        lines.append(
            f"| {sec_id} | {format_npr(entry['value_npr'])} | {entry['value_pct']}% | {entry['count']} |"
        )
    if s.sector_warnings:
        lines += ["", "## ⚠ Sector Concentration Warnings", ""]
        for w in s.sector_warnings:
            lines.append(f"- {w}")
    if s.margin_warnings:
        lines += ["", "## ⚠ Margin Warnings", ""]
        for w in s.margin_warnings:
            lines.append(f"- {w}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
