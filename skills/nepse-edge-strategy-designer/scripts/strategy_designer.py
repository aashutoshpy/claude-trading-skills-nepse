"""Pure-functional NEPSE edge-strategy draft builder.

Inputs: signal dicts (from `nepse-edge-signal-aggregator`).
Outputs: strategy-draft dicts ready for YAML serialization. No I/O.
"""

from __future__ import annotations

from datetime import date

import _path_setup  # noqa: F401

NEPSE_CONSTRAINTS = {
    "long_only": True,
    "daily_price_band_pct": 15.0,
    "settlement_t_plus": 2,
    "amo_eligible": True,
}


# Per-detector templates — overlay onto the shared base
DETECTOR_TEMPLATES = {
    "circuit_day_continuation": {
        "hypothesis": "Names that hit upper circuit on heavy volume often continue 3-5 sessions",
        "entry": {
            "trigger": "open_after_signal",
            "filters": [
                "circuit_day_continuation observation present in last 1 session",
                "sector in leading_sectors per nepse-sector-analyst (optional)",
            ],
        },
        "exit": {"take_profit_pct": 7.0, "stop_loss_pct": 4.0, "time_stop_sessions": 5},
        "falsification": {
            "metric": "forward_3_session_return",
            "threshold_pct": -5.0,
            "interpretation": "If basket avg forward 3-session return < -5%, hypothesis fails",
        },
    },
    "monsoon_hydro_cluster": {
        "hypothesis": "Hydropower names making new 30-day highs together extend through August",
        "entry": {
            "trigger": "open_after_signal",
            "filters": [
                "monsoon_hydro_cluster observation in May-August window",
                "name is among the cluster",
            ],
        },
        "exit": {"take_profit_pct": 15.0, "stop_loss_pct": 8.0, "time_stop_sessions": 60},
        "falsification": {
            "metric": "drawdown_from_peak_by_sep_1",
            "threshold_pct": -50.0,
            "interpretation": "If basket gives back >50% of monsoon-window gains by Sep 1, fails",
        },
    },
    "microfinance_turnaround": {
        "hypothesis": "Microfinance names bouncing 10%+ off 90-day low often see 20-30% follow-through",
        "entry": {
            "trigger": "close_above_5d_ema",
            "filters": [
                "microfinance_turnaround observation in last 5 sessions",
                "close above 5-day EMA",
            ],
        },
        "exit": {"take_profit_pct": 20.0, "stop_loss_pct": 8.0, "time_stop_sessions": 15},
        "falsification": {
            "metric": "retest_of_90d_low_within_10_sessions",
            "threshold_pct": 0.0,
            "interpretation": "If basket re-tests 90-day low within 10 sessions, fails",
        },
    },
    "bfi_dividend_pullback": {
        "hypothesis": "BFI gap-downs of ~dividend amount are mean-reversion buys as arb pressure unwinds",
        "entry": {
            "trigger": "gap_fill_target",
            "filters": [
                "bfi_dividend_pullback observation in last 5 sessions",
                "current price at or below gap-fill target",
            ],
        },
        "exit": {"take_profit_pct": 10.0, "stop_loss_pct": 5.0, "time_stop_sessions": 20},
        "falsification": {
            "metric": "gap_recovery_within_20_sessions",
            "threshold_pct": 50.0,
            "interpretation": "If basket fails to recover 50% of gap within 20 sessions, fails",
        },
    },
}


def design_for_signal(signal: dict, *, today: date) -> dict:
    """Build a strategy draft for a single aggregated signal."""
    symbol = signal.get("symbol") or "UNKNOWN"
    sector = signal.get("sector") or "OTHERS"
    detectors = signal.get("detectors_flagged") or []
    # Pick the detector with the highest base confidence for the primary template
    primary = _pick_primary(detectors)
    template = DETECTOR_TEMPLATES.get(primary, _generic_template())

    return {
        "strategy_id": f"nepse_{primary}_{symbol}_{today.isoformat()}",
        "based_on_signal": f"nepse_{symbol}_{today.isoformat()}",
        "hypothesis": template["hypothesis"],
        "universe": {
            "source": "nepse-edge-signal-aggregator",
            "symbols": [symbol],
            "sector": sector,
        },
        "entry": template["entry"],
        "exit": template["exit"],
        "sizing": {
            "method": "risk_pct_of_account",
            "risk_pct": 1.0,
            "whole_share_rounding": "floor",
        },
        "constraints": dict(NEPSE_CONSTRAINTS),
        "falsification": template["falsification"],
        "metadata": {
            "market": "NEPSE",
            "created_at": today.isoformat(),
            "draft_status": "untested",
            "primary_detector": primary,
            "all_detectors": detectors,
            "signal_score": signal.get("composite_score"),
            "signal_status": signal.get("status"),
        },
    }


def design_all(
    signals: list[dict],
    *,
    today: date,
    include_watch: bool = False,
) -> list[dict]:
    """Design drafts for every ACT signal (or ACT + WATCH if include_watch)."""
    drafts: list[dict] = []
    for s in signals:
        status = s.get("status")
        if status == "ACT" or (include_watch and status == "WATCH"):
            drafts.append(design_for_signal(s, today=today))
    return drafts


def _pick_primary(detectors: list[str]) -> str:
    """Pick the most-confident detector as the primary basis."""
    if not detectors:
        return "circuit_day_continuation"   # fallback
    order = list(DETECTOR_TEMPLATES.keys())
    return min(detectors, key=lambda d: order.index(d) if d in order else len(order))


def _generic_template() -> dict:
    return {
        "hypothesis": "User-defined edge; specify hypothesis manually",
        "entry": {"trigger": "open_after_signal", "filters": []},
        "exit": {"take_profit_pct": 7.0, "stop_loss_pct": 4.0, "time_stop_sessions": 5},
        "falsification": {
            "metric": "forward_5_session_return",
            "threshold_pct": -5.0,
            "interpretation": "Define a clear failure threshold for this edge",
        },
    }
