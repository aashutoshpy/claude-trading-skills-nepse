"""Pure-functional NEPSE capital gains tax calculator.

Reads rates from `config/nepse_rules.yaml` via `common.nepse._config`.
"""

from __future__ import annotations

from dataclasses import dataclass

import _path_setup  # noqa: F401

from common.nepse._config import load_rules


@dataclass(frozen=True)
class TaxRates:
    long_term_pct: float
    short_term_pct: float
    long_term_threshold_days: int
    proposed_uniform_pct: float | None
    proposed_uniform_status: str

    @classmethod
    def load(cls) -> TaxRates:
        t = load_rules().get("capital_gains_tax") or {}
        return cls(
            long_term_pct=float(t.get("long_term_pct", 5.0)),
            short_term_pct=float(t.get("short_term_pct", 7.5)),
            long_term_threshold_days=int(t.get("long_term_threshold_days", 365)),
            proposed_uniform_pct=(
                float(t["proposed_uniform_pct"]) if t.get("proposed_uniform_pct") is not None else None
            ),
            proposed_uniform_status=str(t.get("proposed_uniform_status", "not_enacted")),
        )


@dataclass
class TaxEstimate:
    symbol: str
    shares: float
    entry_price: float
    exit_price: float
    holding_days: int
    cost: float
    proceeds: float
    gross_gain: float
    is_long_term: bool
    rate_pct: float
    tax_npr: float
    net_gain: float
    net_return_pct: float
    days_to_long_term: int | None    # None if already LT
    long_term_tax_npr: float | None  # what tax would be if held to LT
    notes: list[str]


def estimate_tax(
    *,
    symbol: str,
    entry_price: float,
    exit_price: float,
    shares: float,
    holding_days: int,
    rates: TaxRates,
) -> TaxEstimate:
    cost = round(entry_price * shares, 2)
    proceeds = round(exit_price * shares, 2)
    gross_gain = round(proceeds - cost, 2)

    is_long_term = holding_days > rates.long_term_threshold_days
    rate = rates.long_term_pct if is_long_term else rates.short_term_pct
    # Tax only on positive gains (losses are not taxed, no rebate either)
    tax_npr = round(max(0.0, gross_gain) * rate / 100.0, 2)
    net_gain = round(gross_gain - tax_npr, 2)
    net_return_pct = round(net_gain / cost * 100.0, 2) if cost > 0 else 0.0

    days_to_lt = None
    lt_tax = None
    if not is_long_term and gross_gain > 0:
        days_to_lt = rates.long_term_threshold_days + 1 - holding_days
        lt_tax = round(gross_gain * rates.long_term_pct / 100.0, 2)

    notes: list[str] = []
    if rates.proposed_uniform_status != "not_enacted":
        notes.append(
            f"proposed uniform {rates.proposed_uniform_pct}% rate status: "
            f"{rates.proposed_uniform_status} — verify before filing"
        )
    if gross_gain < 0:
        notes.append("capital loss: no tax due; offsettable only in the same fiscal year")
    elif not is_long_term and days_to_lt is not None and lt_tax is not None:
        savings = round(tax_npr - lt_tax, 2)
        notes.append(
            f"hold {days_to_lt} more days to qualify for {rates.long_term_pct}% "
            f"long-term rate; tax savings if price holds: NPR {savings:,.2f}"
        )

    return TaxEstimate(
        symbol=symbol.upper(),
        shares=shares,
        entry_price=entry_price,
        exit_price=exit_price,
        holding_days=holding_days,
        cost=cost,
        proceeds=proceeds,
        gross_gain=gross_gain,
        is_long_term=is_long_term,
        rate_pct=rate,
        tax_npr=tax_npr,
        net_gain=net_gain,
        net_return_pct=net_return_pct,
        days_to_long_term=days_to_lt,
        long_term_tax_npr=lt_tax,
        notes=notes,
    )
