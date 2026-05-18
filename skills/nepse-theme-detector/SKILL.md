---
name: nepse-theme-detector
description: Detect emerging NEPSE investment themes by combining sector-rotation signals (from nepse-sector-analyst), breadth participation, and optional user-supplied theme tickers (e.g., "monsoon hydropower play", "rate-cut financials"). Outputs a ranked list of active themes with constituent names. Use when the user asks "what themes are working on NEPSE?", wants to align positions with the dominant narrative, or needs a thematic basket suggestion.
---

# NEPSE Theme Detector

Detects which thematic clusters of names are driving NEPSE returns by combining sector outputs with optional user-supplied theme baskets.

## What is a "theme"

A grouping of NEPSE names that should move together because of a shared driver — for example:
- "Monsoon hydropower" (June-September generation peak)
- "Rate-cut financials" (banks + finance when NRB is easing)
- "Insurance defensive" (life + non-life when risk-off)
- "Microfinance euphoria" (late-cycle speculation)

NEPSE doesn't have ETF-tradeable themes, so each theme is a list of underlying tickers + a rationale.

## NEPSE Built-In Theme Library

The default theme library covers common NEPSE narratives:

| Theme | Constituents (examples) | Signal it's working |
|---|---|---|
| Monsoon hydropower | UPPER, NHPC, BPCL, AHPC | Hydropower sector index in top 3, May-Aug |
| Rate-cut financials | NABIL, NIB, SCB, NICA | NRB easing + banking sector index ≥ #3 |
| Defensive insurance | NLIC, LICN, NICL, RLI | Insurance sectors ≥ #3 + composite < SMA50 |
| Microfinance speculation | CBBL, GBLBS, NSEWA, SHL | Microfinance #1 in 1w window + new highs spike |
| BFI dividend cluster | NABIL, NICA, EBL, SBI | Banking sector positive + dividend season approaching |

Users can supply their own themes via `--themes-csv`.

## Workflow

### Step 1: Run upstream skills

```bash
python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py --output-dir reports/
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py --output-dir reports/
# Optional:
python3 skills/nepse-macro-regime-detector/scripts/detect_macro_regime.py \
  --macro-csv data/nepse_macro.csv --reports-dir reports/ --output-dir reports/
```

### Step 2: Run the theme detector

```bash
# Default — use built-in themes
python3 skills/nepse-theme-detector/scripts/detect_themes.py \
  --reports-dir reports/ --output-dir reports/

# Bring your own themes
python3 skills/nepse-theme-detector/scripts/detect_themes.py \
  --reports-dir reports/ \
  --themes-csv data/my_nepse_themes.csv \
  --output-dir reports/
```

User CSV format:
```csv
theme_id,display_name,symbols,rationale
my_hydro,Custom Hydropower Basket,"UPPER,NHPC,BPCL",Monsoon thesis
```

### Step 3: Read output

- JSON: `reports/nepse_themes_<YYYY-MM-DD>.json`
- Markdown: `reports/nepse_themes_<YYYY-MM-DD>.md` — themes ranked by activity score

## How "activity score" is computed

For each theme:
- Sector rotation alignment: 40 pts max (theme's primary sectors lead the rankings)
- Macro alignment: 25 pts max (macro regime favors the theme)
- Breadth alignment: 20 pts max (theme constituents participate in advances)
- Recency: 15 pts max (theme has been active in the last 5 sessions)

Themes scoring ≥70 are flagged ACTIVE; 50-69 = DEVELOPING; <50 = INACTIVE.

## Combining

- **Upstream:** `nepse-sector-analyst`, `nepse-market-breadth-analyzer`, `nepse-macro-regime-detector`
- **Downstream:** filter `nepse-vcp-screener` candidates by ACTIVE theme membership
- **Companion:** `nepse-stanley-druckenmiller-investment` for narrative-driven sizing

## Limitations

- Themes are heuristic; "the theme is working" is a *bet*, not a fact
- Built-in theme library reflects NEPSE conventions as of May 2026; sector rotations can invalidate themes
- Constituent lists need maintenance — new IPOs may belong to existing themes
- Macro alignment depends on `nepse-macro-regime-detector` being fresh
