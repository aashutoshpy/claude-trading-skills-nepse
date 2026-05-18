"""Tests for the NEPSE edge strategy designer."""

from datetime import date

from strategy_designer import design_all, design_for_signal


def _signal(status="ACT", detectors=None, **overrides):
    base = {
        "symbol": "NABIL",
        "sector": "BANKING",
        "composite_score": 80,
        "status": status,
        "confluence": 1,
        "detectors_flagged": detectors or ["circuit_day_continuation"],
    }
    base.update(overrides)
    return base


# ---- design_for_signal ----------------------------------------------


def test_design_basic_circuit_day_strategy():
    draft = design_for_signal(_signal(), today=date(2026, 5, 17))
    assert draft["metadata"]["primary_detector"] == "circuit_day_continuation"
    assert draft["constraints"]["long_only"] is True
    assert draft["constraints"]["daily_price_band_pct"] == 15.0
    assert draft["exit"]["take_profit_pct"] == 7.0
    assert draft["exit"]["stop_loss_pct"] == 4.0


def test_design_monsoon_hydro_uses_specific_template():
    draft = design_for_signal(
        _signal(detectors=["monsoon_hydro_cluster"], sector="HYDROPOWER"),
        today=date(2026, 5, 17),
    )
    assert draft["metadata"]["primary_detector"] == "monsoon_hydro_cluster"
    # Monsoon hydro has wider TP/stop and longer time stop
    assert draft["exit"]["take_profit_pct"] == 15.0
    assert draft["exit"]["time_stop_sessions"] == 60


def test_design_microfinance_turnaround_template():
    draft = design_for_signal(
        _signal(detectors=["microfinance_turnaround"], sector="MICROFINANCE"),
        today=date(2026, 5, 17),
    )
    assert draft["entry"]["trigger"] == "close_above_5d_ema"
    assert draft["exit"]["take_profit_pct"] == 20.0


def test_design_bfi_dividend_pullback_template():
    draft = design_for_signal(
        _signal(detectors=["bfi_dividend_pullback"], sector="BANKING"),
        today=date(2026, 5, 17),
    )
    assert draft["entry"]["trigger"] == "gap_fill_target"


def test_design_picks_most_confident_when_multiple_detectors():
    # circuit_day_continuation has the highest base confidence
    draft = design_for_signal(
        _signal(detectors=["bfi_dividend_pullback", "circuit_day_continuation"]),
        today=date(2026, 5, 17),
    )
    assert draft["metadata"]["primary_detector"] == "circuit_day_continuation"


def test_unknown_detector_falls_back_to_generic():
    draft = design_for_signal(
        _signal(detectors=["unknown_detector"]),
        today=date(2026, 5, 17),
    )
    # Generic template
    assert "Define a clear failure threshold" in draft["falsification"]["interpretation"]


def test_constraints_always_baked_in():
    draft = design_for_signal(_signal(), today=date(2026, 5, 17))
    c = draft["constraints"]
    assert c["long_only"] is True
    assert c["daily_price_band_pct"] == 15.0
    assert c["settlement_t_plus"] == 2
    assert c["amo_eligible"] is True


def test_strategy_id_includes_date_and_symbol():
    draft = design_for_signal(_signal(), today=date(2026, 5, 17))
    assert "NABIL" in draft["strategy_id"]
    assert "2026-05-17" in draft["strategy_id"]


# ---- design_all -----------------------------------------------------


def test_design_all_includes_only_act_by_default():
    signals = [
        _signal(symbol="A", status="ACT"),
        _signal(symbol="B", status="WATCH"),
        _signal(symbol="C", status="NOISE"),
    ]
    drafts = design_all(signals, today=date(2026, 5, 17))
    assert [d["universe"]["symbols"][0] for d in drafts] == ["A"]


def test_design_all_with_include_watch():
    signals = [
        _signal(symbol="A", status="ACT"),
        _signal(symbol="B", status="WATCH"),
        _signal(symbol="C", status="NOISE"),
    ]
    drafts = design_all(signals, today=date(2026, 5, 17), include_watch=True)
    symbols = sorted(d["universe"]["symbols"][0] for d in drafts)
    assert symbols == ["A", "B"]
