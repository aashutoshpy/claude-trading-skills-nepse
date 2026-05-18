#!/usr/bin/env python3
"""nepse-edge-candidate-agent — CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
import yaml
from edge_detectors import (
    EdgeObservation,
    detect_bfi_dividend_pullback,
    detect_circuit_day_continuation,
    detect_microfinance_turnaround,
    detect_monsoon_hydro_cluster,
)

from common.nepse import NepseClient

DETECTORS = {
    "circuit_day_continuation": (
        detect_circuit_day_continuation,
        "Stocks that hit upper circuit on >2× avg volume in last 5 sessions; hypothesize continuation",
    ),
    "monsoon_hydro_cluster": (
        detect_monsoon_hydro_cluster,
        "Hydropower names making new 30-day highs together (May-Aug only)",
    ),
    "microfinance_turnaround": (
        detect_microfinance_turnaround,
        "Microfinance stocks that bounced ≥10% off 90-day low in last 5 sessions",
    ),
    "bfi_dividend_pullback": (
        detect_bfi_dividend_pullback,
        "BFI gap-downs of 8-15% in last 10 sessions (potential ex-dividend bargains)",
    ),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE edge candidate agent")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/edge_tickets"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument("--detector", choices=list(DETECTORS.keys()), default=None,
                        help="Run only a specific detector (default: all)")
    parser.add_argument("--history-days", type=int, default=150)
    parser.add_argument("--limit", type=int, default=None, help="Limit universe (testing)")
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

    securities_by_symbol = {sec.symbol.upper(): sec for sec in constituents}
    today = date.today()
    detectors_to_run = [args.detector] if args.detector else list(DETECTORS.keys())

    all_tickets: list[dict] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for det_name in detectors_to_run:
        det_func, det_desc = DETECTORS[det_name]
        # Some detectors need extra kwargs
        if det_name == "monsoon_hydro_cluster":
            observations = det_func(bars_by_symbol, securities_by_symbol, today=today)
        elif det_name == "bfi_dividend_pullback":
            observations = det_func(bars_by_symbol, securities_by_symbol, dividend_records=None)
        else:
            observations = det_func(bars_by_symbol, securities_by_symbol)
        if not observations:
            continue
        ticket = _build_ticket(det_name, det_desc, observations, today)
        ticket_path = args.output_dir / f"{ticket['ticket_id']}.yaml"
        ticket_path.write_text(yaml.safe_dump(ticket, sort_keys=False), encoding="utf-8")
        all_tickets.append(ticket)
        print(f"  Wrote {ticket_path.name} ({len(observations)} candidates)")

    summary_path = args.output_dir.parent / f"nepse_edge_tickets_{today.isoformat()}.json"
    summary_path.write_text(
        json.dumps({"as_of": today.isoformat(), "tickets": all_tickets}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"  Summary: {summary_path}")
    return 0


def _build_ticket(detector: str, description: str, observations: list[EdgeObservation], today: date) -> dict:
    return {
        "ticket_id": f"edge_{today.isoformat()}_{detector}_001",
        "detector": detector,
        "as_of": today.isoformat(),
        "description": description,
        "candidates": [asdict(o) for o in observations],
        "hypothesis": _hypothesis_for(detector),
        "falsification": _falsification_for(detector),
    }


def _hypothesis_for(detector: str) -> str:
    return {
        "circuit_day_continuation": (
            "Names that hit upper circuit on heavy volume often follow through with continued "
            "strength in the next 3-5 sessions. Test: enter at next open, exit at 7% gain or 4% stop."
        ),
        "monsoon_hydro_cluster": (
            "Hydropower names making new 30-day highs in unison during the monsoon window often "
            "extend through August. Test: equal-weight basket entry, hold until first 8% drawdown "
            "from peak or end of August."
        ),
        "microfinance_turnaround": (
            "Microfinance names bouncing 10%+ off a 90-day low often see 20-30% follow-through "
            "if breadth supports. Test: entry on close above 5-day EMA, stop below recent low."
        ),
        "bfi_dividend_pullback": (
            "BFI names that gap down by ~dividend amount on ex-date are often mean-reversion buys "
            "as dividend-arb pressure unwinds. Test: enter at gap-fill price, target prior close."
        ),
    }.get(detector, "Investigate and propose a falsifiable hypothesis.")


def _falsification_for(detector: str) -> str:
    return {
        "circuit_day_continuation": "If 3-session forward return < -5% for the basket, hypothesis fails.",
        "monsoon_hydro_cluster": "If basket gives back >50% of monsoon-window gains by Sep 1, fails.",
        "microfinance_turnaround": "If basket re-tests 90-day low within 10 sessions, fails.",
        "bfi_dividend_pullback": "If basket fails to recover 50% of gap within 20 sessions, fails.",
    }.get(detector, "Define basket forward returns and a clear failure threshold.")


if __name__ == "__main__":
    raise SystemExit(main())
