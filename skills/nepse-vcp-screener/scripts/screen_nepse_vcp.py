#!/usr/bin/env python3
"""nepse-vcp-screener — main entry point.

Iterates the NEPSE universe, fetches OHLCV via NepseClient, runs the
VCP detector, and writes both JSON and Markdown reports.

Usage:
    python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \\
        --output-dir reports/

Backend selection: $NEPSE_BACKEND (default 'nepalstock') or --backend.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401 — sys.path setup
from vcp_detector import VcpParameters, VcpResult, detect_vcp

from common.nepse import NepseClient, Registry, format_npr
from common.nepse.client import Security


def screen(
    client: NepseClient,
    registry: Registry,
    *,
    symbols: list[str] | None,
    history_days: int,
    params: VcpParameters,
    top_n: int,
) -> list[dict]:
    """Run the screener and return a sorted list of candidate dicts.

    Continues past individual symbol failures (NEPSE backends are
    occasionally flaky) — failures are logged to stderr but don't
    abort the run.
    """
    constituents: list[Security] = []
    if symbols:
        symbol_set = {s.upper() for s in symbols}
        try:
            all_constituents = client.list_constituents()
            constituents = [c for c in all_constituents if c.symbol in symbol_set]
        except Exception as exc:
            print(
                f"WARN: list_constituents() unavailable ({exc}); "
                "falling back to --symbols-only mode (sector will be 'OTHERS')",
                file=sys.stderr,
            )
        if not constituents:
            constituents = [
                Security(symbol=s, name=s, sector_id="OTHERS")
                for s in sorted(symbol_set)
            ]
    else:
        constituents = client.list_constituents()

    if not constituents:
        print("ERROR: no NEPSE constituents to screen", file=sys.stderr)
        return []

    end = date.today()
    start = end - timedelta(days=int(history_days * 1.6))  # calendar→trading buffer
    candidates: list[dict] = []
    failures = 0

    for sec in constituents:
        try:
            bars = client.get_ohlcv(sec.symbol, start, end)
        except Exception as exc:
            failures += 1
            print(f"WARN: get_ohlcv({sec.symbol}) failed: {exc}", file=sys.stderr)
            continue

        if not bars:
            continue
        # NepseClient may return rows in either order; sort defensively.
        bars = sorted(bars, key=lambda b: b.day)
        result = detect_vcp(bars, params)
        if result.composite_score == 0 and not result.valid_vcp:
            continue
        candidates.append(_row(sec, bars[-1].close, result, registry))

    candidates.sort(key=lambda r: (r["valid_vcp"], r["composite_score"]), reverse=True)
    if failures:
        print(f"INFO: {failures} symbols failed to fetch", file=sys.stderr)
    return candidates[:top_n]


def _row(sec: Security, last_close: float, r: VcpResult, registry: Registry) -> dict:
    return {
        "symbol": sec.symbol,
        "name": sec.name,
        "sector": sec.sector_id,
        "price": round(last_close, 2),
        "valid_vcp": r.valid_vcp,
        "base_days": r.base_days,
        "contractions": r.contractions,
        "final_contraction_pct": r.final_contraction_pct,
        "pivot_price": r.pivot_price,
        "distance_to_pivot_pct": r.distance_to_pivot_pct,
        "composite_score": r.composite_score,
        "reasons": r.reasons,
        "margin_eligible": registry.is_margin_eligible(sec.symbol),
    }


def write_reports(rows: list[dict], output_dir: Path, *, today: date | None = None) -> tuple[Path, Path]:
    today = today or date.today()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"nepse_vcp_{today.isoformat()}.json"
    md_path = output_dir / f"nepse_vcp_{today.isoformat()}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(), "candidates": rows}, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(rows, today), encoding="utf-8")
    return json_path, md_path


def _render_markdown(rows: list[dict], today: date) -> str:
    lines: list[str] = [
        f"# NEPSE VCP Screener — {today.isoformat()}",
        "",
        f"**Candidates:** {len(rows)}    **Valid VCP:** {sum(1 for r in rows if r['valid_vcp'])}",
        "",
        "| Symbol | Sector | Price | Score | Contractions | Final % | Dist to Pivot | Valid VCP | Margin |",
        "|---|---|---|---:|---:|---:|---:|:---:|:---:|",
    ]
    for r in rows:
        dist = f"{r['distance_to_pivot_pct']}%" if r["distance_to_pivot_pct"] is not None else "—"
        lines.append(
            f"| **{r['symbol']}** | {r['sector']} | {format_npr(r['price'], decimals=2)} | "
            f"{r['composite_score']} | {r['contractions']} | {r['final_contraction_pct']}% | "
            f"{dist} | {'✓' if r['valid_vcp'] else '·'} | {'✓' if r['margin_eligible'] else '·'} |"
        )
    if not rows:
        lines.append("| _(no candidates returned)_ | | | | | | | | |")
    lines += [
        "",
        "**Reading guide:** scores ≥70 are actionable; check `valid_vcp=✓` and `distance_to_pivot_pct` "
        "≤ pivot-distance-max before sizing. Use `nepse-breakout-trade-planner` to generate manual-entry plans.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE VCP screener (Minervini-style)")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--symbols", nargs="*", help="Limit to these tickers (default: full universe)")
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--history-days", type=int, default=300, help="Calendar days of OHLCV to fetch")
    parser.add_argument("--top", type=int, default=30)
    # Tunables (Phase 1 defaults; see references/nepse_vcp_methodology.md)
    parser.add_argument("--min-contractions", type=int, default=2)
    parser.add_argument("--max-final-contraction-pct", type=float, default=6.0)
    parser.add_argument("--min-base-days", type=int, default=15)
    parser.add_argument("--avg-volume-min", type=int, default=5_000)
    parser.add_argument("--stage2-sma200-rising-days", type=int, default=20)
    parser.add_argument("--pivot-distance-max-pct", type=float, default=5.0)
    args = parser.parse_args(argv)

    params = VcpParameters(
        min_contractions=args.min_contractions,
        max_final_contraction_pct=args.max_final_contraction_pct,
        min_base_days=args.min_base_days,
        avg_volume_min=args.avg_volume_min,
        stage2_sma200_rising_days=args.stage2_sma200_rising_days,
        pivot_distance_max_pct=args.pivot_distance_max_pct,
    )

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    registry = Registry.load()
    rows = screen(
        client,
        registry,
        symbols=args.symbols,
        history_days=args.history_days,
        params=params,
        top_n=args.top,
    )
    json_path, md_path = write_reports(rows, args.output_dir)
    print(f"  Wrote {len(rows)} candidates to:\n    {json_path}\n    {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
