"""Tests for the NEPSE market top scorer."""

from top_scorer import (
    compute_top_risk,
    score_ath_proximity,
    score_concentration,
    score_distribution,
    score_divergence,
    score_microfinance_leadership,
)

# ---- distribution scoring -------------------------------------------------


def test_distribution_zero_when_no_data():
    s, r = score_distribution(None)
    assert s == 0


def test_distribution_scales_with_active_count():
    assert score_distribution({"active_count": 0})[0] == 0
    assert score_distribution({"active_count": 3})[0] == 40
    assert score_distribution({"active_count": 5})[0] == 85
    assert score_distribution({"active_count": 7})[0] == 100


# ---- divergence ----------------------------------------------------------


def test_divergence_zero_when_no_data():
    assert score_divergence(None)[0] == 0


def test_divergence_high_when_detected():
    s, r = score_divergence({"divergence_detected": True, "divergence_note": "x"})
    assert s == 80


def test_divergence_zero_when_not_detected():
    s, r = score_divergence({"divergence_detected": False, "divergence_note": "ok"})
    assert s == 0


# ---- microfinance --------------------------------------------------------


def test_microfinance_high_when_rank_one():
    payload = {"sectors": [{"sector_id": "MICROFINANCE", "ranks": {"1w": 1}}]}
    s, r = score_microfinance_leadership(payload)
    assert s == 70


def test_microfinance_zero_when_low_rank():
    payload = {"sectors": [{"sector_id": "MICROFINANCE", "ranks": {"1w": 8}}]}
    s, r = score_microfinance_leadership(payload)
    assert s == 10


def test_microfinance_zero_when_missing():
    payload = {"sectors": [{"sector_id": "BANKING", "ranks": {"1w": 1}}]}
    s, r = score_microfinance_leadership(payload)
    assert s == 0


# ---- concentration ------------------------------------------------------


def test_concentration_high_when_single_sector_dominates_advances():
    payload = {
        "sector_breakdown": {
            "BANKING": {"advances": 60, "declines": 0},
            "HYDROPOWER": {"advances": 0, "declines": 50},
            "MICROFINANCE": {"advances": 40, "declines": 0},
        }
    }
    s, r = score_concentration(payload)
    # BANKING = 60/100 = 60% — high concentration
    assert s == 80


def test_concentration_low_when_advances_spread():
    payload = {
        "sector_breakdown": {
            "BANKING": {"advances": 20, "declines": 0},
            "HYDROPOWER": {"advances": 25, "declines": 0},
            "MICROFINANCE": {"advances": 25, "declines": 0},
            "FINANCE": {"advances": 30, "declines": 0},
        }
    }
    s, r = score_concentration(payload)
    # Max share = 30/100 = 30% (broad)
    assert s == 0


# ---- ath proximity ------------------------------------------------------


def test_ath_proximity_high_when_at_peak_with_high_ratio():
    payload = {
        "current_ratio": 80.0,
        "history": [{"ratio": 75.0}, {"ratio": 80.0}, {"ratio": 78.0}],
    }
    s, r = score_ath_proximity(payload)
    # 80 / 80 * 100 = 100% — within 5% — and current ≥70 — should be high
    assert s == 70


def test_ath_proximity_low_when_far_from_peak():
    payload = {
        "current_ratio": 30.0,
        "history": [{"ratio": 80.0}, {"ratio": 75.0}, {"ratio": 30.0}],
    }
    s, r = score_ath_proximity(payload)
    assert s == 10


# ---- composite ----------------------------------------------------------


def test_composite_zero_when_no_inputs():
    r = compute_top_risk(distribution_json=None, uptrend_json=None,
                         sectors_json=None, breadth_json=None)
    assert r.score == 0
    assert r.level == "LOW"


def test_composite_high_when_all_signals_red():
    r = compute_top_risk(
        distribution_json={"active_count": 6},
        uptrend_json={
            "divergence_detected": True, "divergence_note": "x",
            "current_ratio": 80.0,
            "history": [{"ratio": 80.0}],
        },
        sectors_json={"sectors": [{"sector_id": "MICROFINANCE", "ranks": {"1w": 1}}]},
        breadth_json={"sector_breakdown": {"MICROFINANCE": {"advances": 80, "declines": 0}}},
    )
    assert r.score >= 75
    assert r.level in ("HIGH", "EXTREME")


def test_composite_level_classification():
    # Score = 0 → LOW
    r = compute_top_risk(distribution_json=None, uptrend_json=None,
                         sectors_json=None, breadth_json=None)
    assert r.level == "LOW"
