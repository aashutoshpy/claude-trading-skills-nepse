# NEPSE Trading Skills

A Claude Skills toolkit for trading the **Nepal Stock Exchange (NEPSE)**. 27 skills + 5 workflows that turn Claude into a structured assistant for screening, charting, trade planning, portfolio tracking, and quarterly results review on Nepali stocks.

> **Status:** Beta — verified against NEPSE rules as of **May 2026**
> (Mon–Fri 11:00–15:00 NPT, 15% daily price band, AMO 18:00–06:00,
> margin trading live since April 2026 for 123 names, T+2 settlement,
> 5% LT / 7.5% ST capital gains).

This is a fork of [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) adapted for the Nepal Stock Exchange. The original US-market skills are retained in the repo but are not exposed in this README — see [`docs/en/skill-catalog.md`](docs/en/skill-catalog.md) if you need them.

> **New to this repo?** Start with [GETTING_STARTED.md](GETTING_STARTED.md) — a step-by-step walkthrough for amateur traders with a MeroShare + broker account, covering setup, the daily 30-minute routine, weekly portfolio review, and a jargon glossary.

---

## Quick Start

### 1. Clone + install

```bash
git clone https://github.com/aashutoshpy/claude-trading-skills-nepse.git
cd claude-trading-skills-nepse
pip install -e .            # installs pyyaml, requests, scipy, yfinance
pip install -e ".[dev]"     # adds pytest, ruff for testing/linting
```

Optional: install a community NEPSE library if you want the `community` backend instead of the default scraper:

```bash
pip install nepse-api
```

### 2. Verify the foundation

```bash
python3 -m pytest common/nepse/tests/ -v
```

You should see **57 tests pass** in well under a second.

### 3. Run a skill

```bash
# Default: nepalstock.com.np scraper backend, full universe
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --output-dir reports/

# Switch backend
NEPSE_BACKEND=community python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --output-dir reports/

# Limit to a few symbols for a quick smoke test
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py --symbols NABIL UPPER NICA --output-dir reports/
```

Reports land in `reports/` as paired `.json` (machine-readable) and `.md` (human-readable) files.

### 4. Use with Claude Code

Copy the relevant `skills/nepse-*/` folder into your Claude Code Skills directory (Settings → Skills → Open Skills Folder), or run from this repo directly using the SKILL.md files in place. See [Claude Code Skills documentation](https://docs.claude.com/en/docs/claude-code/skills) for the latest steps.

---

## What's Inside

| Group | Skills |
|---|---|
| **Foundation** | `common/nepse/` package — NepseClient interface, two backends (`nepalstock` scraper, `community` lib wrapper), disk cache, registry, trading calendar, NPR formatting |
| **Config** | `config/nepse_rules.yaml`, `config/registry.yaml` — single source of truth for market rules, sector taxonomy, margin-eligible universe |
| **Skills** | 27 NEPSE-specific skills across screening, market context, trade planning, portfolio, research |
| **Workflows** | 5 canonical workflow manifests (`workflows/nepse-*.yaml`) |
| **Tests** | 274 tests; pass in <1s with one `pytest` invocation |

### Recommended Workflows

| Goal | Workflow | Cadence |
|---|---|---|
| Daily regime check before sizing | [`nepse-market-regime-daily`](workflows/nepse-market-regime-daily.yaml) | Daily |
| Find swing-trade candidates | [`nepse-swing-opportunity-daily`](workflows/nepse-swing-opportunity-daily.yaml) | Daily |
| Weekly portfolio review | [`nepse-core-portfolio-weekly`](workflows/nepse-core-portfolio-weekly.yaml) | Weekly |
| Record every trade as a thesis | [`nepse-trade-memory-loop`](workflows/nepse-trade-memory-loop.yaml) | Per trade |
| Quarterly results review | [`nepse-quarterly-results-review`](workflows/nepse-quarterly-results-review.yaml) | Quarterly (Nepali FY) |

See [`workflows/README.md`](workflows/README.md) for the manifest schema and how to run them.

---

## Skill Catalog

<!-- skills-index:start name="catalog-en" -->
<!-- This section is auto-generated from skills-index.yaml by scripts/generate_catalog_from_index.py. Do not edit by hand — edit the index and re-run the generator. -->

### Market Regime

| Skill | Summary | Integrations | Status |
|---|---|---|---|
| **NEPSE Downtrend Duration Analyzer** (`nepse-downtrend-duration-analyzer`) | Identify historical NEPSE composite drawdowns, measure peak-to-trough and trough-to-recovery durations, and produce a distribution to contextualize current pullbacks. | `nepse_client` **required** | beta |
| **NEPSE IBD Distribution Day Monitor** (`nepse-ibd-distribution-day-monitor`) | Apply IBD-style distribution day rules to the NEPSE composite — count active down-on-higher-volume sessions in a 25-session rolling window. | `nepse_client` **required** | beta |
| **NEPSE Macro Regime Detector** (`nepse-macro-regime-detector`) | Combine NRB monetary policy, USD/NPR, Nifty 50, Brent, gold, and NEPSE breadth/sector signals into a coarse RISK_ON / NEUTRAL / RISK_OFF / STAGFLATION regime label. | `user_macro_csv` _recommended_, `upstream_skill_outputs` **required** | beta |
| **NEPSE Market Breadth Analyzer** (`nepse-market-breadth-analyzer`) | Compute NEPSE breadth indicators (A/D, new 52w highs/lows, % above 50/200-SMA, sector participation) across the ~284-name universe. | `nepse_client` **required** | beta |
| **NEPSE Market Top Detector** (`nepse-market-top-detector`) | Aggregate distribution-day count, breadth divergence, microfinance over-leadership, sector concentration, and ATH proximity into a composite top-risk score and warning level. | `upstream_skill_outputs` **required** | beta |
| **NEPSE Sector Analyst** (`nepse-sector-analyst`) | Rank NEPSE's 13 sector indices by trailing returns and classify each sector's stage. Identifies leaders, laggards, and rotation patterns. | `nepse_client` **required** | beta |
| **NEPSE Uptrend Analyzer** (`nepse-uptrend-analyzer`) | Compute the NEPSE Uptrend Ratio (% of names above their 200-day SMA), track its 1-year history, classify regime, and flag breadth divergence vs the NEPSE composite. | `nepse_client` **required** | beta |

### Core Portfolio

| Skill | Summary | Integrations | Status |
|---|---|---|---|
| **NEPSE Kanchi Dividend SOP** (`nepse-kanchi-dividend-sop`) | Apply Kanchi's 5-step dividend investing method to NEPSE — sector-aware quality scoring (BFI / insurance preferred), cash-vs-bonus split awareness, pullback entry planning around the Bhadra-Mangsir AGM cycle. | `upstream_skill_outputs` **required** | beta |
| **NEPSE Portfolio Tracker** (`nepse-portfolio-tracker`) | Track a NEPSE portfolio from MeroShare CSV/manual entries — per-position P&L, sector concentration, margin usage warnings cross-referenced with the eligible-name list. | `user_portfolio_csv` **required**, `nepse_client` optional | beta |
| **NEPSE Value + Dividend Screener** (`nepse-value-dividend-screener`) | Screen NEPSE for high cash+bonus dividend yield using a user-supplied dividend CSV (NEPSE backends do not expose structured dividends). | `nepse_client` **required**, `user_dividends_csv` _recommended_ | beta |

### Swing Opportunity

| Skill | Summary | Integrations | Status |
|---|---|---|---|
| **NEPSE CANSLIM Screener** (`nepse-canslim-screener`) | CANSLIM 7-factor screening for NEPSE. C+A from user fundamentals CSV; N+S+L+I from OHLCV/floorsheet; M gated by nepse-uptrend-analyzer. Sector-cap default 5 prevents hydropower domination. | `nepse_client` **required**, `user_fundamentals_csv` _recommended_, `upstream_skill_outputs` **required** | beta |
| **NEPSE Technical Analyst** (`nepse-technical-analyst`) | Chart-image-driven technical analysis tuned for NEPSE microstructure (15% band, circuit-hit bars, bonus-share gaps, illiquid no-trade days). | `user_image` **required** | beta |
| **NEPSE VCP Screener** (`nepse-vcp-screener`) | Screen the NEPSE universe for Minervini-style Volatility Contraction Patterns, calibrated for the 15% daily price band introduced April 2026. | `nepse_client` **required** | beta |

### Trade Planning

| Skill | Summary | Integrations | Status |
|---|---|---|---|
| **NEPSE Breakout Trade Planner** (`nepse-breakout-trade-planner`) | Convert nepse-vcp-screener candidates into manual-entry breakout trade plans — entry trigger, stop-loss, 1R/2R/3R targets, risk-based share count, and AMO queue instructions. | `upstream_skill_outputs` **required** | beta |
| **NEPSE Capital Gains Tax Notes** (`nepse-capital-gains-tax-notes`) | Estimate Nepal capital gains tax on NEPSE share trades (5% long-term >365 days, 7.5% short-term) with optional batch CSV processing and exit-timing guidance for the LT threshold. | `nepse_config` **required** | beta |
| **NEPSE Earnings Calendar** (`nepse-earnings-calendar`) | Generate NEPSE quarterly-results calendar from Nepali FY (statutory T+30 windows after Ashwin/Poush/Chaitra/Ashadh quarter-ends), optionally enriched with per-company announcement CSV. | `nepse_config` **required**, `user_earnings_csv` optional | beta |
| **NEPSE Earnings Trade Analyzer** (`nepse-earnings-trade-analyzer`) | Score NEPSE post-quarterly-result reactions with the 5-factor framework (gap %, trend stage, volume surge, MA200/MA50 distance), recalibrated for NEPSE's 15% daily price band. | `nepse_client` **required** | beta |
| **NEPSE Margin Eligibility** (`nepse-margin-eligibility`) | Check if a NEPSE ticker is on the 123-name margin-eligible list (live April 2026) and compute margin-call distance for a given position. | `nepse_config` **required** | beta |

### Strategy Research

| Skill | Summary | Integrations | Status |
|---|---|---|---|
| **NEPSE Edge Candidate Agent** (`nepse-edge-candidate-agent`) | Detect NEPSE-specific anomalies (circuit-day continuation, monsoon hydropower clusters, microfinance turnarounds, BFI dividend pullbacks) and emit edge tickets for downstream strategy design. | `nepse_client` **required** | beta |
| **NEPSE Edge Signal Aggregator** (`nepse-edge-signal-aggregator`) | Aggregate edge tickets from nepse-edge-candidate-agent, deduplicate same-symbol observations, and rank by confluence + recency + detector confidence + sector boost. | `upstream_skill_outputs` **required** | beta |
| **NEPSE Edge Strategy Designer** (`nepse-edge-strategy-designer`) | Convert NEPSE edge signals into backtest-ready strategy YAML drafts with NEPSE-specific defaults (15% band, long-only, T+2 settlement, AMO eligible, whole-share floor rounding). | `upstream_skill_outputs` **required** | beta |
| **NEPSE Stanley Druckenmiller Investment** (`nepse-stanley-druckenmiller-investment`) | Synthesize NEPSE macro (NRB, USD/NPR, Nifty), regime (uptrend, breadth), and top-risk signals into a Druckenmiller-style bias score and recommended portfolio tilt. | `upstream_skill_outputs` **required** | beta |
| **NEPSE Theme Detector** (`nepse-theme-detector`) | Detect active NEPSE themes (monsoon hydropower, rate-cut financials, defensive insurance, microfinance speculation, BFI dividend cluster) by combining sector rotation, breadth, and macro signals. | `upstream_skill_outputs` **required**, `user_themes_csv` optional | beta |
<!-- skills-index:end name="catalog-en" -->

---

## Configuration

### NEPSE market rules — `config/nepse_rules.yaml`

The single source of truth for changeable NEPSE rules. Every skill reads from here. When SEBON/NEPSE updates a rule (which has happened 3 times in 12 months), edit this YAML — never edit Python constants.

```yaml
trading_days_isoweekday: [1, 2, 3, 4, 5]   # Mon-Fri
session:
  open:  "11:00"
  close: "15:00"
daily_price_band_pct: 15.0                  # raised from 10% on 2026-04-17
amo:
  open:  "18:00"                            # next-session AMO window
  close: "06:00"
margin:
  enabled: true
  initial_margin_pct: 30.0                  # SEBON minimum
  maintenance_margin_pct: 20.0
settlement_t_plus: 2
short_selling_enabled: false                # NEPSE forbids shorting
capital_gains_tax:
  long_term_pct: 5.0                        # holding > 365 days
  short_term_pct: 7.5
  long_term_threshold_days: 365
```

When you edit this file, also append a one-line entry to [`common/nepse/references/nepse_market_rules_changelog.md`](common/nepse/references/nepse_market_rules_changelog.md) for auditability.

### Sector + universe — `config/registry.yaml`

13 NEPSE sector indices, the ~284-name universe (seed list), the 123 margin-eligible names (seed list), and the Nepali fiscal year quarter-ends. Refresh as listings change. (A `scripts/refresh_nepse_registry.py` refresh helper is planned.)

### Backend selection

| Backend | When to use | Setup |
|---|---|---|
| `nepalstock` (default) | Most uses; no third-party dependency | None — works out of the box |
| `community` | Fall-back when the scraper breaks after a site redesign | `pip install nepse-api` (or similar) |

Set via `NEPSE_BACKEND=nepalstock\|community` env var, or pass `--backend` to any CLI.

### Per-skill inputs

Several skills consume user-maintained CSVs (NEPSE has no FMP-equivalent feeds). Templates are documented in each skill's `SKILL.md`:

| CSV | Used by | Source |
|---|---|---|
| `data/nepse_dividends.csv` | `nepse-value-dividend-screener` | sharesansar.com, merolagani.com |
| `data/nepse_macro.csv` | `nepse-macro-regime-detector` | nrb.org.np, tradingeconomics.com |
| `data/nepse_earnings.csv` | `nepse-earnings-calendar` | sharesansar.com announcements |
| `data/nepse_fundamentals.csv` | `nepse-canslim-screener` | sharesansar.com financials |
| `data/nepse_portfolio.csv` | `nepse-portfolio-tracker` | MeroShare export |

---

## NEPSE Market Reference (May 2026)

Quick-reference card for the rules baked into the skills:

| Aspect | Current state |
|---|---|
| Listed companies | ~284 (132 BFIs/insurance, **97 hydropower**, 26 mfg, others) |
| Sector indices | 13 (Banking, Dev Bank, Finance, Microfinance, Hydropower, Life Ins, Non-Life Ins, Hotels & Tourism, Mfg, Trading, Mutual Funds, Investment, Others) |
| Trading days | **Mon–Fri** (changed from Sun–Thu in late 2025) |
| Session | **11:00–15:00 NPT** (UTC+5:45) |
| Pre-opening band | 3% (raised from 2% in April 2026) |
| **Daily price band** | **15%** (raised from 10% on April 17, 2026) |
| Circuit breakers | 5% halt 11:00–13:00 (15 min) · 8% close-for-day 13:00–15:00 |
| AMO window | **18:00–06:00** (next-session queueing, since April 2026) |
| Margin trading | **Live since mid-April 2026** for 123 names; 30% initial / 20% maintenance |
| Short selling | Not available |
| Settlement | T+2 |
| Capital gains tax | 5% long-term (>365 days) / 7.5% short-term (proposed uniform 10% not enacted) |
| Central bank rate | NRB repo **5.0%** (Jan–Mar 2026); SLF ceiling 6.5%; avg lending rate ~7.0% |

Full audit log in [`common/nepse/references/nepse_market_rules_changelog.md`](common/nepse/references/nepse_market_rules_changelog.md).

---

## Running Tests

```bash
# All NEPSE tests (foundation + 26 skills)
python3 -m pytest common/nepse/tests/ skills/nepse-*/scripts/tests/ -q

# Strict workflow validation
python3 scripts/validate_skills_index.py --strict-workflows

# Doc drift check
python3 scripts/generate_skill_docs.py --check
```

Expected: **274 tests pass** in well under a second; validator and drift gate both clean.

---

## Limitations

Known constraints and known-unknowns — read before relying on outputs for sizing decisions:

1. **`nepalstock.com.np` endpoint shapes are unverified against the live site.** The first real run may need tuning. See `common/nepse/backends/nepalstock_scraper.py`.
2. **`Registry.constituents` and `margin_eligible_symbols` are empty seeds.** Populate via the (planned) `scripts/refresh_nepse_registry.py` or by hand. Until populated, universe-driven skills return empty results.
3. **`_INDEX_IDS` map uses placeholder numeric IDs.** Verify against the live site for `nepse-sector-analyst` and `nepse-ibd-distribution-day-monitor`.
4. **No machine-readable fundamentals or dividend feed for NEPSE.** Skills that need them accept user-maintained CSVs (see *Per-skill inputs* above).
5. **No brokerage automation.** NEPSE TMS systems are web-only with no public API. All skills emit *plans*; you place orders manually at your broker or via MeroShare.
6. **Rule volatility.** NEPSE rules have changed 3 times in the last 12 months. Treat `config/nepse_rules.yaml` as a config file you should review whenever SEBON or NEPSE announces a change.
7. **Margin trading is brand new (April 2026).** The 123-name eligibility list will change; margin-call cascades have no historical NEPSE precedent.
8. **Heuristic composite scores** (top-risk, Druckenmiller bias, theme detector, etc.) are NEPSE conventions, not back-tested across a full post-reform NEPSE cycle.

---

## Disclaimer

This repository is for **educational and research purposes only**. It is not financial advice, investment advisory service, tax advice, legal advice, a signal service, or a broker execution platform. Trading and investing involve risk, including loss of principal. Past performance, backtests, screens, reports, and AI-generated analysis do not guarantee future results. All trading decisions, position sizing, tax/regulatory compliance, and broker usage are the user's responsibility.

Provided under the MIT License, **AS IS, WITHOUT WARRANTY**.

---

## License

MIT — see [`LICENSE`](LICENSE).

## Acknowledgements

Forked from [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills), the US-market predecessor. The foundation patterns, validator, workflow manifest schema, and documentation pipeline all originate upstream; this fork adapts them for NEPSE.
