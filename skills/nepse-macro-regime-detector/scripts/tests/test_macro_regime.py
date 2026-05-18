"""Tests for the NEPSE macro regime detector."""

from datetime import date

from macro_regime import MacroInputs, detect_macro_regime, parse_macro_csv

# ---- CSV parsing -------------------------------------------------------


def test_parse_csv_full():
    csv = (
        "key,value,as_of\n"
        "nrb_repo_pct,5.0,2026-03-30\n"
        "rate_direction,tightening,2026-03-30\n"
        "usd_npr_pct_change_30d,-0.8,2026-05-10\n"
        "nifty50_ytd_pct,12.5,2026-05-10\n"
        "brent_ytd_pct,8.3,2026-05-10\n"
        "gold_ytd_pct,18.2,2026-05-10\n"
    )
    inp = parse_macro_csv(csv, today=date(2026, 5, 17))
    assert inp.nrb_repo_pct == 5.0
    assert inp.rate_direction == "tightening"
    assert inp.usd_npr_pct_change_30d == -0.8
    assert inp.gold_ytd_pct == 18.2
    assert inp.as_of == date(2026, 5, 10)
    assert inp.stale is False


def test_parse_csv_marks_stale_when_as_of_old():
    csv = "key,value,as_of\nnrb_repo_pct,5.0,2026-01-01\n"
    inp = parse_macro_csv(csv, today=date(2026, 5, 17))
    assert inp.stale is True


def test_parse_csv_marks_stale_when_no_as_of():
    csv = "key,value,as_of\nnrb_repo_pct,5.0,\n"
    inp = parse_macro_csv(csv, today=date(2026, 5, 17))
    assert inp.stale is True


def test_parse_csv_skips_bad_numerics():
    csv = "key,value,as_of\nnrb_repo_pct,oops,2026-05-10\ngold_ytd_pct,18.0,2026-05-10\n"
    inp = parse_macro_csv(csv, today=date(2026, 5, 17))
    assert inp.nrb_repo_pct is None
    assert inp.gold_ytd_pct == 18.0


# ---- regime classification --------------------------------------------


def test_risk_off_when_tightening_and_bearish_breadth():
    inp = MacroInputs(rate_direction="tightening", nrb_repo_pct=5.0, as_of=date(2026, 5, 10))
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "BEAR_NARROW"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert r.regime == "RISK_OFF"


def test_risk_off_when_only_tightening():
    inp = MacroInputs(rate_direction="tightening", nrb_repo_pct=5.0, as_of=date(2026, 5, 10))
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "NEUTRAL"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    # NRB tightening trumps breadth
    assert r.regime == "RISK_OFF"


def test_risk_on_when_easing():
    inp = MacroInputs(rate_direction="easing", nrb_repo_pct=3.5, as_of=date(2026, 5, 10))
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "NEUTRAL"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert r.regime == "RISK_ON"


def test_risk_on_when_neutral_rate_and_bull_breadth():
    inp = MacroInputs(rate_direction="neutral", as_of=date(2026, 5, 10))
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "BULL_BROAD"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert r.regime == "RISK_ON"


def test_neutral_when_neutral_rate_and_mixed_breadth():
    inp = MacroInputs(rate_direction="neutral", as_of=date(2026, 5, 10))
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "NEUTRAL"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert r.regime == "NEUTRAL"


def test_stagflation_when_tightening_with_oil_and_currency_pressure():
    inp = MacroInputs(
        rate_direction="tightening",
        nrb_repo_pct=5.0,
        brent_ytd_pct=20.0,
        usd_npr_pct_change_30d=-1.5,
        as_of=date(2026, 5, 10),
    )
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "BEAR_BROAD"},
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert r.regime == "STAGFLATION"


def test_sector_leader_extracted_from_sectors_json():
    inp = MacroInputs(rate_direction="neutral", as_of=date(2026, 5, 10))
    sectors_json = {
        "sectors": [
            {"sector_id": "HYDROPOWER", "ranks": {"1w": 1}},
            {"sector_id": "BANKING", "ranks": {"1w": 2}},
        ]
    }
    r = detect_macro_regime(
        macro=inp,
        breadth_json={"regime": "NEUTRAL"},
        sectors_json=sectors_json,
        today=date(2026, 5, 17),
    )
    assert r.sector_leader == "HYDROPOWER"


def test_stale_inputs_flagged_in_rationale():
    inp = MacroInputs(rate_direction="tightening", as_of=date(2026, 1, 1))
    inp.stale = True
    r = detect_macro_regime(
        macro=inp,
        breadth_json=None,
        sectors_json=None,
        today=date(2026, 5, 17),
    )
    assert any("stale" in note for note in r.rationale)
