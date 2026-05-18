#!/usr/bin/env python3
"""nepse-sector-analyst — main entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import _path_setup  # noqa: F401
from sector_ranker import SectorScore, rank_sectors

from common.nepse import NepseClient, Registry


def fetch_sector_bars(client: NepseClient, registry: Registry, history_days: int) -> dict[str, list]:
    """Fetch sector-index OHLCV for every sector in the registry."""
    end = date.today()
    start = end - timedelta(days=int(history_days * 1.6))
    out: dict[str, list] = {}
    for sector in registry.sectors:
        try:
            bars = client.get_index(sector.id, start, end)
        except Exception as exc:
            print(f"WARN: get_index({sector.id}) failed: {exc}", file=sys.stderr)
            continue
        if bars:
            out[sector.id] = bars
    return out


def write_reports(scores: list[SectorScore], output_dir: Path, today: date) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"nepse_sectors_{today.isoformat()}"
    json_path = output_dir / f"{base}.json"
    md_path = output_dir / f"{base}.md"
    json_path.write_text(
        json.dumps({"as_of": today.isoformat(), "sectors": [asdict(s) for s in scores]}, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(scores, today), encoding="utf-8")
    return json_path, md_path


def _render_markdown(scores: list[SectorScore], today: date) -> str:
    if not scores:
        return f"# NEPSE Sector Ranking — {today.isoformat()}\n\n_(no sector data returned)_\n"

    labels = list(next(iter(scores)).returns_pct.keys())
    headers = ["Sector", "Last", "Stage", *[f"{label} %" for label in labels], *[f"#{label}" for label in labels]]
    lines = [
        f"# NEPSE Sector Ranking — {today.isoformat()}",
        "",
        f"**Sectors covered:** {len(scores)}    **Sort:** by first window ranking",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] + ["---:" for _ in headers[1:]]) + "|",
    ]
    # Sort by rank in first window (descending strength → ascending rank)
    primary_label = labels[0] if labels else None
    ordered = sorted(
        scores,
        key=lambda s: s.ranks.get(primary_label, 999) if primary_label else 0,
    )
    for s in ordered:
        ret_cells = [f"{s.returns_pct.get(label, 0.0):+.1f}" for label in labels]
        rank_cells = [str(s.ranks.get(label, "—")) for label in labels]
        lines.append(
            f"| **{s.sector_id}** | {s.last_close} | {s.stage} | " +
            " | ".join(ret_cells) + " | " + " | ".join(rank_cells) + " |"
        )

    leaders = [s.sector_id for s in ordered[:3]]
    laggards = [s.sector_id for s in ordered[-3:]]
    lines += [
        "",
        f"**Top 3 leaders:** {', '.join(leaders)}",
        f"**Bottom 3 laggards:** {', '.join(laggards)}",
        "",
        "**Reading guide:** rotate screening focus to leaders; trim positions in laggards "
        "if `nepse-market-breadth-analyzer` confirms broad weakness.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEPSE sector index ranker")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--backend", choices=["nepalstock", "community"], default=None)
    parser.add_argument(
        "--windows",
        type=str,
        default="5,22,66",
        help="Comma-separated trading-day windows (default 5,22,66 = 1w/1mo/3mo)",
    )
    parser.add_argument("--history-days", type=int, default=300)
    parser.add_argument("--no-ytd", action="store_true")
    args = parser.parse_args(argv)

    windows = {}
    labels = ["1w", "1mo", "3mo", "6mo", "1y"]
    for i, raw in enumerate(args.windows.split(",")):
        try:
            n = int(raw.strip())
        except ValueError:
            print(f"ERROR: bad --windows value {raw!r}", file=sys.stderr)
            return 1
        windows[labels[i] if i < len(labels) else f"w{n}"] = n

    try:
        client = NepseClient.create(backend=args.backend)
    except Exception as exc:
        print(f"ERROR: could not create NepseClient: {exc}", file=sys.stderr)
        return 1

    registry = Registry.load()
    sector_bars = fetch_sector_bars(client, registry, args.history_days)
    if not sector_bars:
        print("ERROR: no sector indices fetched", file=sys.stderr)
        return 1

    today = date.today()
    scores = rank_sectors(sector_bars, windows=windows, today=today, include_ytd=not args.no_ytd)
    json_path, md_path = write_reports(scores, args.output_dir, today)
    print(f"  Ranked {len(scores)} sectors:\n    {json_path}\n    {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
