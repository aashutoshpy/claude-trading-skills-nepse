#!/usr/bin/env python3
"""nepse-breakout-trade-planner — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from trade_planner import AccountSettings, TradePlan, plan_all

from common.nepse import format_npr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE breakout trade planner")
    parser.add_argument("--vcp-json", type=Path, required=True,
                        help="Output JSON from nepse-vcp-screener")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--account-size", type=float, required=True,
                        help="Total account size in NPR")
    parser.add_argument("--risk-pct", type=float, default=1.0,
                        help="Risk per trade as % of account (default 1.0)")
    parser.add_argument("--stop-method", choices=["percent", "swing_low"], default="percent")
    parser.add_argument("--stop-pct", type=float, default=7.0)
    parser.add_argument("--min-score", type=int, default=60)
    parser.add_argument("--valid-only", action="store_true")
    args = parser.parse_args(argv)

    if not args.vcp_json.exists():
        print(f"ERROR: VCP JSON not found: {args.vcp_json}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(args.vcp_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not parse VCP JSON: {exc}", file=sys.stderr)
        return 1

    candidates = payload.get("candidates") or []
    if not candidates:
        print("WARN: no candidates in VCP JSON", file=sys.stderr)

    account = AccountSettings(
        account_size=args.account_size,
        risk_pct=args.risk_pct,
        stop_method=args.stop_method,
        stop_pct=args.stop_pct,
    )
    plans = plan_all(
        candidates,
        account=account,
        min_score=args.min_score,
        valid_only=args.valid_only,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    json_path = args.output_dir / f"nepse_trade_plans_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_trade_plans_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({
            "as_of": today.isoformat(),
            "account_size": args.account_size,
            "risk_pct": args.risk_pct,
            "stop_pct": args.stop_pct,
            "min_score": args.min_score,
            "valid_only": args.valid_only,
            "plans": [asdict(p) for p in plans],
        }, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(plans, today, args), encoding="utf-8")
    print(f"  Wrote {len(plans)} trade plans:\n    {json_path}\n    {md_path}")
    return 0


def _render_markdown(plans: list[TradePlan], today: date, args) -> str:
    lines = [
        f"# NEPSE Trade Plans — {today.isoformat()}",
        "",
        f"**Account size:** {format_npr(args.account_size)}    "
        f"**Risk per trade:** {args.risk_pct}%    "
        f"**Stop method:** {args.stop_method} ({args.stop_pct}%)    "
        f"**Min score:** {args.min_score}",
        "",
        f"**Plans generated:** {len(plans)}",
        "",
    ]
    if not plans:
        lines.append("_(no plans — try lowering --min-score or removing --valid-only)_")
        return "\n".join(lines) + "\n"

    for p in plans:
        lines += [
            f"## {p.symbol}  —  {p.sector}  —  score {p.score}",
            "",
            f"- **Entry trigger:** {format_npr(p.entry_trigger)}  (buy stop)",
            f"- **Stop loss:** {format_npr(p.stop_loss)}  ({p.stop_pct}% below entry, "
            f"risk/share = {format_npr(p.risk_per_share)})",
            f"- **Shares:** {p.shares}    **Position cost:** {format_npr(p.position_cost)}  "
            f"({p.position_pct_of_account}% of account)",
            f"- **Targets:** 1R = {format_npr(p.target_1r)}  |  2R = {format_npr(p.target_2r)}  "
            f"|  3R = {format_npr(p.target_3r)}",
            f"- **Margin-eligible:** {'✓' if p.margin_eligible else '·'}",
            f"- **AMO:** {p.amo_instruction}",
        ]
        for w in p.warnings:
            lines.append(f"- ⚠ {w}")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
