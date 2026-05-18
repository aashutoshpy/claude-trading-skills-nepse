"""Tests for the NEPSE Druckenmiller synthesizer."""

from druck_synthesizer import synthesize


def _all_bullish_inputs() -> dict:
    return {
        "macro_json": {
            "regime": "RISK_ON",
            "inputs": {
                "rate_direction": "easing",
                "usd_npr_pct_change_30d": 0.5,
                "nifty50_ytd_pct": 15.0,
            },
        },
        "uptrend_json": {"regime": "STRONG_UPTREND"},
        "breadth_json": {"regime": "BULL_BROAD"},
        "sectors_json": {
            "sectors": [
                {"sector_id": "BANKING", "returns_pct": {"1w": 5.0}, "ranks": {"1w": 1}},
                {"sector_id": "HYDROPOWER", "returns_pct": {"1w": 3.0}, "ranks": {"1w": 2}},
                {"sector_id": "MICROFINANCE", "returns_pct": {"1w": -8.0}, "ranks": {"1w": 13}},
            ]
        },
        "top_json": {"level": "LOW"},
        "distrib_json": {"active_count": 0},
    }


def _all_bearish_inputs() -> dict:
    return {
        "macro_json": {
            "regime": "RISK_OFF",
            "inputs": {
                "rate_direction": "tightening",
                "usd_npr_pct_change_30d": -2.0,
                "nifty50_ytd_pct": -5.0,
            },
        },
        "uptrend_json": {"regime": "DOWNTREND"},
        "breadth_json": {"regime": "BEAR_BROAD"},
        "sectors_json": {
            "sectors": [
                {"sector_id": "BANKING", "returns_pct": {"1w": -5.0}, "ranks": {"1w": 1}},
            ]
        },
        "top_json": {"level": "EXTREME"},
        "distrib_json": {"active_count": 7},
    }


# ---- bias classification ------------------------------------------------


def test_all_bullish_yields_strong_bias_long():
    r = synthesize(**_all_bullish_inputs())
    assert r.bias in ("STRONG_BIAS_LONG", "BIAS_LONG")
    assert r.score >= 75


def test_all_bearish_yields_defensive():
    r = synthesize(**_all_bearish_inputs())
    assert r.bias in ("STRONG_DEFENSIVE", "BIAS_DEFENSIVE")
    assert r.score <= 35


def test_no_inputs_yields_neutral():
    r = synthesize(macro_json=None, uptrend_json=None, breadth_json=None,
                   sectors_json=None, top_json=None, distrib_json=None)
    assert r.bias == "NEUTRAL"


def test_tilt_matches_bias():
    r = synthesize(**_all_bullish_inputs())
    assert r.tilt["exposure_pct_range"] in ("70-85%", "90-100%")
    assert "sector_tilt" in r.tilt


# ---- specific component behavior --------------------------------------


def test_tightening_lowers_nrb_component():
    bullish_easing = synthesize(**_all_bullish_inputs())
    inputs = _all_bullish_inputs()
    inputs["macro_json"]["inputs"]["rate_direction"] = "tightening"
    tightening = synthesize(**inputs)
    assert bullish_easing.components["nrb"]["score"] > tightening.components["nrb"]["score"]


def test_distribution_days_punish_score():
    no_dist = synthesize(**_all_bullish_inputs())
    inputs = _all_bullish_inputs()
    inputs["distrib_json"]["active_count"] = 6
    with_dist = synthesize(**inputs)
    assert no_dist.score > with_dist.score


def test_sector_clarity_higher_for_wide_spread():
    inputs = _all_bullish_inputs()
    # Wide spread already in fixture (5 - (-8) = 13%)
    r_wide = synthesize(**inputs)
    inputs["sectors_json"]["sectors"] = [
        {"sector_id": "BANKING", "returns_pct": {"1w": 1.5}, "ranks": {"1w": 1}},
        {"sector_id": "HYDROPOWER", "returns_pct": {"1w": 1.0}, "ranks": {"1w": 2}},
        {"sector_id": "MICROFINANCE", "returns_pct": {"1w": 0.5}, "ranks": {"1w": 3}},
    ]
    r_narrow = synthesize(**inputs)
    assert r_wide.components["sector_clarity"]["score"] > r_narrow.components["sector_clarity"]["score"]


def test_extreme_top_risk_collapses_score():
    inputs = _all_bullish_inputs()
    inputs["top_json"] = {"level": "EXTREME"}
    r = synthesize(**inputs)
    # Even with everything else bullish, EXTREME top-risk drags score
    assert r.components["top_risk"]["score"] == 5
