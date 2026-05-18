"""Tests for the NEPSE Kanchi dividend scorer."""

from kanchi_scorer import score_candidate, score_candidates


def _cand(**overrides) -> dict:
    base = {
        "symbol": "NABIL",
        "sector": "BANKING",
        "yield_pct": 7.5,
        "cash_div_pct": 11.0,
        "bonus_div_pct": 0.0,
        "distance_to_sma200_pct": -5.0,
    }
    base.update(overrides)
    return base


def test_high_quality_bank_passes():
    s = score_candidate(_cand())
    # BANKING + cash-heavy + below SMA200 + decent yield → PASS
    assert s.verdict == "PASS"
    assert s.score >= 75


def test_skip_when_low_yield_and_low_quality_sector():
    s = score_candidate(_cand(sector="OTHERS", yield_pct=3.5, cash_div_pct=2.0, bonus_div_pct=2.0,
                              distance_to_sma200_pct=30.0))
    # Low yield + non-traditional sector + far above SMA200 → SKIP
    assert s.verdict == "SKIP"


def test_bonus_heavy_penalized():
    s_cash = score_candidate(_cand(cash_div_pct=10.0, bonus_div_pct=0.0))
    s_bonus = score_candidate(_cand(cash_div_pct=0.0, bonus_div_pct=10.0))
    assert s_cash.score > s_bonus.score


def test_microfinance_cautious_note():
    s = score_candidate(_cand(sector="MICROFINANCE"))
    assert any("caution" in n.lower() for n in s.notes)


def test_far_above_sma200_wait_for_pullback():
    s = score_candidate(_cand(distance_to_sma200_pct=20.0))
    assert any("wait for pullback" in n.lower() for n in s.notes)


def test_score_candidates_sorts_descending():
    cands = [
        _cand(symbol="HIGH", yield_pct=10, sector="BANKING"),
        _cand(symbol="LOW", yield_pct=3, sector="OTHERS"),
    ]
    rows = score_candidates(cands)
    assert rows[0].symbol == "HIGH"
    assert rows[0].score > rows[1].score


def test_no_dividend_data_neutral():
    s = score_candidate(_cand(cash_div_pct=0.0, bonus_div_pct=0.0))
    assert any("no dividend split" in n.lower() for n in s.notes)
