"""Pure-functional NEPSE margin math.

Loads rules from config/nepse_rules.yaml + config/registry.yaml. No I/O
within the math functions; the caller resolves the configs once and
passes them in.
"""

from __future__ import annotations

from dataclasses import dataclass

import _path_setup  # noqa: F401

from common.nepse._config import load_rules
from common.nepse.registry import Registry


@dataclass(frozen=True)
class MarginRules:
    enabled: bool
    initial_pct: float
    maintenance_pct: float

    @classmethod
    def load(cls) -> MarginRules:
        m = load_rules().get("margin") or {}
        return cls(
            enabled=bool(m.get("enabled", False)),
            initial_pct=float(m.get("initial_margin_pct", 30.0)),
            maintenance_pct=float(m.get("maintenance_margin_pct", 20.0)),
        )


@dataclass
class MarginCheck:
    symbol: str
    eligible: bool
    initial_pct: float
    maintenance_pct: float


@dataclass
class MarginCallReport:
    symbol: str
    eligible: bool
    position_cost: float
    initial_equity: float
    borrowed: float
    current_value: float | None = None
    current_equity: float | None = None
    margin_call_price: float | None = None
    pct_distance_to_call: float | None = None
    warning: str | None = None


def check_eligibility(symbol: str, *, registry: Registry, rules: MarginRules) -> MarginCheck:
    return MarginCheck(
        symbol=symbol.upper(),
        eligible=registry.is_margin_eligible(symbol) and rules.enabled,
        initial_pct=rules.initial_pct,
        maintenance_pct=rules.maintenance_pct,
    )


def margin_call_price(
    *, shares: float, borrowed: float, maintenance_pct: float
) -> float | None:
    """Solve for the price at which equity falls to the maintenance margin.

    Equity at price P = shares*P - borrowed.
    Maintenance equity = (shares*P) * (maintenance_pct/100).
    Margin call: equity ≤ maintenance_equity
        shares*P - borrowed ≤ shares*P*(m/100)
        shares*P*(1 - m/100) ≤ borrowed
        P ≤ borrowed / (shares * (1 - m/100))

    Returns the cross-over price (the lowest legal pre-call price). None
    if shares ≤ 0 or maintenance_pct ≥ 100.
    """
    if shares <= 0 or maintenance_pct >= 100.0:
        return None
    denom = shares * (1.0 - maintenance_pct / 100.0)
    if denom <= 0:
        return None
    return round(borrowed / denom, 2)


def compute_position(
    symbol: str,
    *,
    entry_price: float,
    shares: float,
    margin_pct: float | None = None,
    current_price: float | None = None,
    registry: Registry,
    rules: MarginRules,
) -> MarginCallReport:
    """Build a full margin-call report for a position.

    `margin_pct` is the user's actual initial margin (defaults to SEBON minimum).
    If `current_price` is given, the report adds live equity + distance-to-call.
    """
    eligible = registry.is_margin_eligible(symbol) and rules.enabled
    if margin_pct is None:
        margin_pct = rules.initial_pct
    position_cost = round(entry_price * shares, 2)
    initial_equity = round(position_cost * margin_pct / 100.0, 2)
    borrowed = round(position_cost - initial_equity, 2)
    report = MarginCallReport(
        symbol=symbol.upper(),
        eligible=eligible,
        position_cost=position_cost,
        initial_equity=initial_equity,
        borrowed=borrowed,
    )
    if not eligible:
        report.warning = "not on margin-eligible list — broker would reject the trade"

    call_price = margin_call_price(
        shares=shares, borrowed=borrowed, maintenance_pct=rules.maintenance_pct
    )
    report.margin_call_price = call_price

    if current_price is not None:
        report.current_value = round(current_price * shares, 2)
        report.current_equity = round(report.current_value - borrowed, 2)
        if call_price is not None and current_price > 0:
            report.pct_distance_to_call = round(
                (call_price - current_price) / current_price * 100.0, 2
            )
            if call_price >= current_price:
                report.warning = (
                    (report.warning + "; " if report.warning else "")
                    + f"MARGIN CALL TRIGGERED at NPR {current_price:,.2f}"
                )
    return report
