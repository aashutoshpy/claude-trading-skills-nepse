"""Pure-functional NEPSE breakout trade plan generation.

Inputs: parsed VCP-screener candidate dicts + account settings.
Outputs: a list of trade-plan dicts. No I/O.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import _path_setup  # noqa: F401

DEFAULT_STOP_PCT = 7.0
DEFAULT_MIN_SCORE = 0
DEFAULT_TARGETS_R = (1.0, 2.0, 3.0)


@dataclass
class AccountSettings:
    account_size: float
    risk_pct: float                  # 0.5-2.0 typical
    stop_method: str = "percent"     # "percent" | "swing_low"
    stop_pct: float = DEFAULT_STOP_PCT


@dataclass
class TradePlan:
    symbol: str
    sector: str
    score: int
    entry_trigger: float
    stop_loss: float
    stop_pct: float
    risk_per_share: float
    shares: int
    position_cost: float
    position_pct_of_account: float
    target_1r: float
    target_2r: float
    target_3r: float
    amo_instruction: str
    margin_eligible: bool
    warnings: list[str]


def plan_one(
    candidate: dict,
    *,
    account: AccountSettings,
    targets_r: tuple[float, ...] = DEFAULT_TARGETS_R,
) -> TradePlan | None:
    """Build a plan for one VCP-screener candidate. Returns None if not actionable."""
    symbol = str(candidate.get("symbol") or "").upper()
    if not symbol:
        return None

    pivot = float(candidate.get("pivot_price") or 0.0)
    price = float(candidate.get("price") or 0.0)
    if pivot <= 0 or price <= 0:
        return None

    # Entry trigger = pivot break (a hair above the pivot)
    entry_trigger = round(pivot * 1.001, 2)

    # Stop-loss
    if account.stop_method == "swing_low" and "swing_low_price" in candidate:
        stop_loss = float(candidate["swing_low_price"])
        # Guard against absurd stops
        max_stop = entry_trigger * (1.0 - account.stop_pct / 100.0)
        if stop_loss < max_stop:
            stop_loss = max_stop
    else:
        stop_loss = round(entry_trigger * (1.0 - account.stop_pct / 100.0), 2)

    risk_per_share = round(entry_trigger - stop_loss, 4)
    if risk_per_share <= 0:
        return None

    # Risk-based sizing
    risk_budget = account.account_size * account.risk_pct / 100.0
    raw_shares = risk_budget / risk_per_share
    shares = int(math.floor(raw_shares))
    if shares <= 0:
        return None

    position_cost = round(entry_trigger * shares, 2)
    position_pct = round(position_cost / max(account.account_size, 1) * 100.0, 2)

    targets = {
        f"target_{int(r)}r": round(entry_trigger + r * risk_per_share, 2)
        for r in targets_r
    }

    warnings: list[str] = []
    dist = candidate.get("distance_to_pivot_pct")
    if dist is not None and float(dist) <= 1.0:
        warnings.append(
            f"Distance to pivot {dist}% — entry imminent; double-check stop placement"
        )
    if not candidate.get("valid_vcp", False):
        warnings.append("VCP validity flag is False — only the score qualifies this setup")
    if position_pct > 25.0:
        warnings.append(
            f"Position would be {position_pct:.1f}% of account — consider splitting or reducing"
        )

    amo_instruction = (
        f"Queue buy stop at NPR {entry_trigger:.2f} between 18:00 and 06:00 for next session"
    )

    return TradePlan(
        symbol=symbol,
        sector=str(candidate.get("sector") or ""),
        score=int(candidate.get("composite_score") or 0),
        entry_trigger=entry_trigger,
        stop_loss=stop_loss,
        stop_pct=round(account.stop_pct, 2),
        risk_per_share=risk_per_share,
        shares=shares,
        position_cost=position_cost,
        position_pct_of_account=position_pct,
        target_1r=targets.get("target_1r", 0.0),
        target_2r=targets.get("target_2r", 0.0),
        target_3r=targets.get("target_3r", 0.0),
        amo_instruction=amo_instruction,
        margin_eligible=bool(candidate.get("margin_eligible", False)),
        warnings=warnings,
    )


def plan_all(
    candidates: list[dict],
    *,
    account: AccountSettings,
    min_score: int = DEFAULT_MIN_SCORE,
    valid_only: bool = False,
) -> list[TradePlan]:
    """Filter then plan."""
    plans: list[TradePlan] = []
    for c in candidates:
        if int(c.get("composite_score") or 0) < min_score:
            continue
        if valid_only and not c.get("valid_vcp", False):
            continue
        p = plan_one(c, account=account)
        if p is not None:
            plans.append(p)
    plans.sort(key=lambda p: p.score, reverse=True)
    return plans
