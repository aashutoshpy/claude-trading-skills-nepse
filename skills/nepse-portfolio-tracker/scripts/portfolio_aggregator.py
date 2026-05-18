"""Pure-functional NEPSE portfolio aggregation.

Inputs: list of parsed Position rows + a price-lookup map + Registry.
Outputs: a PortfolioSnapshot with totals, per-position rows, sector
breakdown, and margin warnings. No I/O.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from io import StringIO

import _path_setup  # noqa: F401

from common.nepse.registry import Registry

SECTOR_CONCENTRATION_THRESHOLD_PCT = 40.0


@dataclass
class Position:
    symbol: str
    shares: float
    avg_cost: float
    entry_date: date | None = None
    is_margin: bool = False


@dataclass
class PositionRow:
    symbol: str
    sector: str
    shares: float
    avg_cost: float
    current_price: float
    invested: float
    current_value: float
    unrealized_pnl_npr: float
    unrealized_pnl_pct: float
    is_margin: bool
    margin_eligible: bool
    margin_call_price: float | None = None
    margin_call_distance_pct: float | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class PortfolioSnapshot:
    as_of: date
    positions: list[PositionRow]
    invested_total: float
    current_value_total: float
    unrealized_pnl_npr: float
    unrealized_pnl_pct: float
    sector_breakdown: dict[str, dict]   # sector_id → {value_pct, value_npr, count}
    sector_warnings: list[str]
    margin_warnings: list[str]


def parse_portfolio_csv(text: str) -> list[Position]:
    out: list[Position] = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        sym = (row.get("symbol") or "").strip().upper()
        if not sym:
            continue
        try:
            shares = float(row.get("shares") or 0)
            avg_cost = float(row.get("avg_cost") or 0)
        except ValueError:
            continue
        if shares <= 0 or avg_cost <= 0:
            continue
        entry_str = (row.get("entry_date") or "").strip()
        entry_date: date | None
        try:
            entry_date = date.fromisoformat(entry_str) if entry_str else None
        except ValueError:
            entry_date = None
        is_margin = (row.get("is_margin") or "").strip().lower() in ("true", "1", "yes", "y")
        out.append(Position(symbol=sym, shares=shares, avg_cost=avg_cost,
                            entry_date=entry_date, is_margin=is_margin))
    return out


def _sector_for(symbol: str, registry: Registry, default: str = "OTHERS") -> str:
    # We don't have a per-symbol sector index in seed registry; surface
    # default for now. Production refresh script would populate
    # registry.constituents which would let us look this up.
    return default


def _margin_call_for_position(
    pos: Position, current_price: float, registry: Registry, *,
    initial_pct: float, maintenance_pct: float,
) -> tuple[float | None, float | None]:
    """Returns (margin_call_price, pct_distance_from_current). None pair if not margin."""
    if not pos.is_margin:
        return None, None
    borrowed = pos.shares * pos.avg_cost * (1.0 - initial_pct / 100.0)
    if pos.shares <= 0 or maintenance_pct >= 100:
        return None, None
    call_price = round(borrowed / (pos.shares * (1.0 - maintenance_pct / 100.0)), 2)
    pct_distance = round((call_price - current_price) / current_price * 100.0, 2) if current_price > 0 else None
    return call_price, pct_distance


def build_snapshot(
    positions: list[Position],
    *,
    price_lookup: dict[str, float],
    registry: Registry,
    today: date,
    initial_margin_pct: float = 30.0,
    maintenance_margin_pct: float = 20.0,
) -> PortfolioSnapshot:
    rows: list[PositionRow] = []
    margin_warnings: list[str] = []

    for pos in positions:
        current_price = price_lookup.get(pos.symbol.upper(), pos.avg_cost)
        invested = round(pos.shares * pos.avg_cost, 2)
        current_value = round(pos.shares * current_price, 2)
        pnl_npr = round(current_value - invested, 2)
        pnl_pct = round(pnl_npr / invested * 100.0, 2) if invested > 0 else 0.0
        margin_eligible = registry.is_margin_eligible(pos.symbol)

        call_price, call_distance = _margin_call_for_position(
            pos, current_price, registry,
            initial_pct=initial_margin_pct, maintenance_pct=maintenance_margin_pct,
        )

        warnings: list[str] = []
        if pos.is_margin and not margin_eligible:
            warnings.append("MARGIN flag set but ticker is NOT on margin-eligible list")
        if call_distance is not None and call_distance >= 0:
            warnings.append(f"MARGIN CALL TRIGGERED at NPR {current_price:,.2f}")
            margin_warnings.append(f"{pos.symbol}: margin call active")
        elif call_distance is not None and call_distance > -5.0:
            warnings.append(f"margin call within 5% (at NPR {call_price:,.2f})")
            margin_warnings.append(f"{pos.symbol}: margin call within {abs(call_distance)}% of current")

        rows.append(
            PositionRow(
                symbol=pos.symbol,
                sector=_sector_for(pos.symbol, registry),
                shares=pos.shares,
                avg_cost=round(pos.avg_cost, 2),
                current_price=round(current_price, 2),
                invested=invested,
                current_value=current_value,
                unrealized_pnl_npr=pnl_npr,
                unrealized_pnl_pct=pnl_pct,
                is_margin=pos.is_margin,
                margin_eligible=margin_eligible,
                margin_call_price=call_price,
                margin_call_distance_pct=call_distance,
                warnings=warnings,
            )
        )

    invested_total = round(sum(r.invested for r in rows), 2)
    current_value_total = round(sum(r.current_value for r in rows), 2)
    pnl_npr = round(current_value_total - invested_total, 2)
    pnl_pct = round(pnl_npr / invested_total * 100.0, 2) if invested_total > 0 else 0.0

    sector_breakdown: dict[str, dict] = {}
    if current_value_total > 0:
        for r in rows:
            entry = sector_breakdown.setdefault(
                r.sector, {"value_npr": 0.0, "value_pct": 0.0, "count": 0}
            )
            entry["value_npr"] += r.current_value
            entry["count"] += 1
        for sec_id, entry in sector_breakdown.items():
            entry["value_npr"] = round(entry["value_npr"], 2)
            entry["value_pct"] = round(entry["value_npr"] / current_value_total * 100.0, 2)

    sector_warnings: list[str] = []
    for sec_id, entry in sector_breakdown.items():
        if entry["value_pct"] > SECTOR_CONCENTRATION_THRESHOLD_PCT:
            sector_warnings.append(
                f"{sec_id} = {entry['value_pct']}% of portfolio (above {SECTOR_CONCENTRATION_THRESHOLD_PCT}% threshold)"
            )

    return PortfolioSnapshot(
        as_of=today,
        positions=rows,
        invested_total=invested_total,
        current_value_total=current_value_total,
        unrealized_pnl_npr=pnl_npr,
        unrealized_pnl_pct=pnl_pct,
        sector_breakdown=sector_breakdown,
        sector_warnings=sector_warnings,
        margin_warnings=margin_warnings,
    )
