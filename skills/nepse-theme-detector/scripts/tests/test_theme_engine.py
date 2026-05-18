"""Tests for the NEPSE theme engine."""

from theme_engine import BUILT_IN_THEMES, Theme, parse_themes_csv, score_themes

# ---- CSV parsing ------------------------------------------------------


def test_parse_csv_basic():
    csv = (
        "theme_id,display_name,symbols,rationale,primary_sectors,favorable_macro\n"
        "my_hydro,Custom Hydro,\"UPPER,NHPC\",Monsoon thesis,HYDROPOWER,RISK_ON\n"
    )
    themes = parse_themes_csv(csv)
    assert len(themes) == 1
    t = themes[0]
    assert t.theme_id == "my_hydro"
    assert t.symbols == ["UPPER", "NHPC"]
    assert t.primary_sectors == ["HYDROPOWER"]
    assert t.favorable_macro == ["RISK_ON"]


def test_parse_csv_skips_empty_theme_id():
    csv = "theme_id,display_name,symbols\n,No ID,UPPER\nok,OK,NABIL\n"
    themes = parse_themes_csv(csv)
    assert [t.theme_id for t in themes] == ["ok"]


# ---- built-in themes -------------------------------------------------


def test_builtin_themes_exist():
    ids = {t.theme_id for t in BUILT_IN_THEMES}
    assert "monsoon_hydropower" in ids
    assert "rate_cut_financials" in ids
    assert "microfinance_speculation" in ids


# ---- score_themes ----------------------------------------------------


def _theme(**overrides) -> Theme:
    base = {
        "theme_id": "t",
        "display_name": "T",
        "symbols": ["X"],
        "primary_sectors": ["HYDROPOWER"],
        "favorable_macro": ["RISK_ON"],
        "rationale": "",
    }
    base.update(overrides)
    return Theme(**base)


def test_score_themes_returns_sorted_descending():
    themes = [_theme(theme_id="A"), _theme(theme_id="B")]
    rows = score_themes(themes, sectors_json=None, breadth_json=None,
                        macro_json=None, uptrend_json=None)
    assert len(rows) == 2
    assert rows[0].score >= rows[1].score


def test_score_high_when_all_signals_aligned():
    themes = [_theme()]
    sectors_json = {
        "sectors": [
            {"sector_id": "HYDROPOWER", "ranks": {"1w": 1}},
        ]
    }
    breadth_json = {
        "sector_breakdown": {
            "HYDROPOWER": {"advances": 50, "declines": 0},
            "BANKING": {"advances": 10, "declines": 0},
        }
    }
    macro_json = {"regime": "RISK_ON"}
    uptrend_json = {"regime": "STRONG_UPTREND"}
    rows = score_themes(themes, sectors_json=sectors_json, breadth_json=breadth_json,
                        macro_json=macro_json, uptrend_json=uptrend_json)
    assert rows[0].status == "ACTIVE"
    assert rows[0].score >= 80


def test_score_inactive_when_no_data():
    themes = [_theme()]
    rows = score_themes(themes, sectors_json=None, breadth_json=None,
                        macro_json=None, uptrend_json=None)
    assert rows[0].status == "INACTIVE"


def test_macro_misaligned_lowers_score():
    themes = [_theme(favorable_macro=["RISK_ON"])]
    macro_off = {"regime": "RISK_OFF"}
    macro_on = {"regime": "RISK_ON"}
    r_off = score_themes(themes, sectors_json=None, breadth_json=None,
                         macro_json=macro_off, uptrend_json=None)[0]
    r_on = score_themes(themes, sectors_json=None, breadth_json=None,
                        macro_json=macro_on, uptrend_json=None)[0]
    assert r_on.score > r_off.score


def test_downtrend_kills_recency_component():
    themes = [_theme()]
    uptrend = {"regime": "DOWNTREND"}
    rows = score_themes(themes, sectors_json=None, breadth_json=None,
                        macro_json=None, uptrend_json=uptrend)
    assert rows[0].components["recency"]["score"] == 0
