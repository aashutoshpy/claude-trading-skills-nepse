#!/usr/bin/env python3
"""nepse-macro-regime-detector — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import _path_setup  # noqa: F401
from macro_regime import MacroInputs, MacroRegimeResult, detect_macro_regime, parse_macro_csv


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
    parser = argparse.ArgumentParser(description="NEPSE macro regime detector")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--macro-csv", type=Path, default=None,
                        help="CSV with macro inputs (key,value,as_of)")
    parser.add_argument("--breadth-json", type=Path, default=None)
    parser.add_argument("--sectors-json", type=Path, default=None)
    args = parser.parse_args(argv)

    today = date.today()
    macro = MacroInputs()
    if args.macro_csv:
        if not args.macro_csv.exists():
            print(f"ERROR: macro CSV not found: {args.macro_csv}", file=sys.stderr)
            return 1
        macro = parse_macro_csv(args.macro_csv.read_text(encoding="utf-8"), today=today)
    else:
        print("WARN: no --macro-csv; regime call will be low-confidence", file=sys.stderr)
        macro.stale = True

    breadth = args.breadth_json or _resolve_latest(args.reports_dir, "nepse_breadth")
    sectors = args.sectors_json or _resolve_latest(args.reports_dir, "nepse_sectors")

    result = detect_macro_regime(
        macro=macro,
        breadth_json=_load_json(breadth),
        sectors_json=_load_json(sectors),
        today=today,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"nepse_macro_regime_{today.isoformat()}.json"
    md_path = args.output_dir / f"nepse_macro_regime_{today.isoformat()}.md"
    json_path.write_text(json.dumps(_to_dict(result), indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(f"  Macro regime: {result.regime}")
    print(f"    {json_path}\n    {md_path}")
    return 0


def _to_dict(r: MacroRegimeResult) -> dict:
    return {
        "as_of": r.as_of.isoformat(),
        "regime": r.regime,
        "inputs": asdict(r.inputs),
        "breadth_regime": r.breadth_regime,
        "sector_leader": r.sector_leader,
        "rationale": r.rationale,
    }


def _render_markdown(r: MacroRegimeResult) -> str:
    inp = r.inputs
    lines = [
        f"# NEPSE Macro Regime — {r.as_of.isoformat()}",
        "",
        f"**Regime:** `{r.regime}`",
        f"**NEPSE breadth:** {r.breadth_regime or 'unknown'}    **Sector leader:** {r.sector_leader or 'unknown'}",
        "",
        "## Macro Inputs",
        "",
        "| Input | Value | As-of |",
        "|---|---|---|",
        f"| NRB repo (%) | {inp.nrb_repo_pct} | {inp.as_of or '—'} |",
        f"| Rate direction | {inp.rate_direction or '—'} | {inp.as_of or '—'} |",
        f"| USD/NPR 30d %Δ | {inp.usd_npr_pct_change_30d} | {inp.as_of or '—'} |",
        f"| Nifty50 YTD % | {inp.nifty50_ytd_pct} | {inp.as_of or '—'} |",
        f"| Brent YTD % | {inp.brent_ytd_pct} | {inp.as_of or '—'} |",
        f"| Gold YTD % | {inp.gold_ytd_pct} | {inp.as_of or '—'} |",
        f"| Inputs stale? | {inp.stale} | {inp.as_of or '—'} |",
        "",
        "## Rationale",
        "",
    ]
    for note in r.rationale:
        lines.append(f"- {note}")
    lines += [
        "",
        "**Action guide:**",
        "- `RISK_ON`: long-bias on top-quality setups; standard sizing",
        "- `NEUTRAL`: maintain exposure; await regime shift",
        "- `RISK_OFF`: tighten stops; no new larger positions; consider raising cash",
        "- `STAGFLATION`: defensive sectors only (insurance, utilities); minimum exposure",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
