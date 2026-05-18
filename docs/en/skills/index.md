---
layout: default
title: Skill Guides
parent: English
nav_order: 3
has_children: true
lang_peer: /ja/skills/
permalink: /en/skills/
---

# Skill Guides
{: .no_toc }

Practical guides for individual skills with real-world examples, workflow explanations, and tips for power users.

Hand-written guides (marked with ★) follow a detailed 10-section structure. Auto-generated guides provide an overview, prerequisites, workflow, and resource listing extracted from each skill's SKILL.md.

---

## Available Guides

| Skill | Description | API |
|-------|-------------|-----|
| [Backtest Expert]({{ '/en/skills/backtest-expert/' | relative_url }}) ★ | Expert guidance for systematic backtesting of trading strategies | <span class="badge badge-free">No API</span> |
| [Breadth Chart Analyst]({{ '/en/skills/breadth-chart-analyst/' | relative_url }}) | This skill should be used when analyzing market breadth charts, specifically the S&P 500 Breadth Index (200-Day MA ba... | <span class="badge badge-free">No API</span> |
| [Breakout Trade Planner]({{ '/en/skills/breakout-trade-planner/' | relative_url }}) | Generate Minervini-style breakout trade plans from VCP screener output with worst-case risk calculation, portfolio he... | <span class="badge badge-free">No API</span> |
| [CANSLIM Screener]({{ '/en/skills/canslim-screener/' | relative_url }}) ★ | Screen US stocks using William O'Neil's CANSLIM growth stock methodology | <span class="badge badge-api">FMP Required</span> |
| [Data Quality Checker]({{ '/en/skills/data-quality-checker/' | relative_url }}) | Validate data quality in market analysis documents and blog articles before publication | <span class="badge badge-free">No API</span> |
| [Dividend Growth Pullback Screener]({{ '/en/skills/dividend-growth-pullback-screener/' | relative_url }}) | Use this skill to find high-quality dividend growth stocks (12%+ annual dividend growth, 1 | <span class="badge badge-api">FMP Required</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [Downtrend Duration Analyzer]({{ '/en/skills/downtrend-duration-analyzer/' | relative_url }}) | Analyze historical downtrend durations and generate interactive HTML histograms showing typical correction lengths by... | <span class="badge badge-free">No API</span> |
| [Dual Axis Skill Reviewer]({{ '/en/skills/dual-axis-skill-reviewer/' | relative_url }}) | Review skills in any project using a dual-axis method: (1) deterministic code-based checks (structure, scripts, tests... | <span class="badge badge-free">No API</span> |
| [Earnings Calendar]({{ '/en/skills/earnings-calendar/' | relative_url }}) | This skill retrieves upcoming earnings announcements for US stocks using the Financial Modeling Prep (FMP) API | <span class="badge badge-api">FMP Required</span> |
| [Earnings Trade Analyzer]({{ '/en/skills/earnings-trade-analyzer/' | relative_url }}) | Analyze recent post-earnings stocks using a 5-factor scoring system (Gap Size, Pre-Earnings Trend, Volume Trend, MA20... | <span class="badge badge-api">FMP Required</span> |
| [Economic Calendar Fetcher]({{ '/en/skills/economic-calendar-fetcher/' | relative_url }}) | Fetch upcoming economic events and data releases using FMP API | <span class="badge badge-api">FMP Required</span> |
| [Edge Candidate Agent]({{ '/en/skills/edge-candidate-agent/' | relative_url }}) | Generate and prioritize US equity long-side edge research tickets from EOD observations, then export pipeline-ready c... | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Edge Concept Synthesizer]({{ '/en/skills/edge-concept-synthesizer/' | relative_url }}) | Abstract detector tickets and hints into reusable edge concepts with thesis, invalidation signals, and strategy playb... | <span class="badge badge-free">No API</span> |
| [Edge Hint Extractor]({{ '/en/skills/edge-hint-extractor/' | relative_url }}) | Extract edge hints from daily market observations and news reactions, with optional LLM ideation, and output canonica... | <span class="badge badge-free">No API</span> |
| [Edge Pipeline Orchestrator]({{ '/en/skills/edge-pipeline-orchestrator/' | relative_url }}) | Orchestrate the full edge research pipeline from candidate detection through strategy design, review, revision, and e... | <span class="badge badge-free">No API</span> |
| [Edge Signal Aggregator]({{ '/en/skills/edge-signal-aggregator/' | relative_url }}) | Aggregate and rank signals from multiple edge-finding skills (edge-candidate-agent, theme-detector, sector-analyst, i... | <span class="badge badge-free">No API</span> |
| [Edge Strategy Designer]({{ '/en/skills/edge-strategy-designer/' | relative_url }}) | Convert abstract edge concepts into strategy draft variants and optional exportable ticket YAMLs for edge-candidate-a... | <span class="badge badge-free">No API</span> |
| [Edge Strategy Reviewer]({{ '/en/skills/edge-strategy-reviewer/' | relative_url }}) | Critically review strategy drafts from edge-strategy-designer for edge plausibility, overfitting risk, sample size ad... | <span class="badge badge-free">No API</span> |
| [Exposure Coach]({{ '/en/skills/exposure-coach/' | relative_url }}) | Generate a one-page Market Posture summary with net exposure ceiling, growth-vs-value bias, participation breadth, an... | <span class="badge badge-free">No API</span> |
| [Finviz Screener]({{ '/en/skills/finviz-screener/' | relative_url }}) ★ | Build and open FinViz screener URLs from natural language requests | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [FTD Detector]({{ '/en/skills/ftd-detector/' | relative_url }}) | Detects Follow-Through Day (FTD) signals for market bottom confirmation using William O'Neil's methodology | <span class="badge badge-api">FMP Required</span> |
| [Ibd Distribution Day Monitor]({{ '/en/skills/ibd-distribution-day-monitor/' | relative_url }}) | Detect IBD-style Distribution Days for QQQ/SPY (close down at least 0 | <span class="badge badge-api">FMP Required</span> |
| [Institutional Flow Tracker]({{ '/en/skills/institutional-flow-tracker/' | relative_url }}) | Use this skill to track institutional investor ownership changes and portfolio flows using 13F filings data | <span class="badge badge-api">FMP Required</span> |
| [Kanchi Dividend Review Monitor]({{ '/en/skills/kanchi-dividend-review-monitor/' | relative_url }}) | Monitor dividend portfolios with Kanchi-style forced-review triggers (T1-T5) and convert anomalies into OK/WARN/REVIE... | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Kanchi Dividend SOP]({{ '/en/skills/kanchi-dividend-sop/' | relative_url }}) | Convert Kanchi-style dividend investing into a repeatable US-stock operating procedure | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Kanchi Dividend US Tax Accounting]({{ '/en/skills/kanchi-dividend-us-tax-accounting/' | relative_url }}) | Provide US dividend tax and account-location workflow for Kanchi-style income portfolios | <span class="badge badge-free">No API</span> |
| [Macro Regime Detector]({{ '/en/skills/macro-regime-detector/' | relative_url }}) | Detect structural macro regime transitions (1-2 year horizon) using cross-asset ratio analysis | <span class="badge badge-free">No API</span> |
| [Market Breadth Analyzer]({{ '/en/skills/market-breadth-analyzer/' | relative_url }}) ★ | Quantifies market breadth health using TraderMonty's public CSV data | <span class="badge badge-free">No API</span> |
| [Market Environment Analysis]({{ '/en/skills/market-environment-analysis/' | relative_url }}) | Comprehensive market environment analysis and reporting tool | <span class="badge badge-free">No API</span> |
| [Market News Analyst]({{ '/en/skills/market-news-analyst/' | relative_url }}) ★ | This skill should be used when analyzing recent market-moving news events and their impact on equity markets and comm... | <span class="badge badge-free">No API</span> |
| [Market Top Detector]({{ '/en/skills/market-top-detector/' | relative_url }}) | Detects market top probability using O'Neil Distribution Days, Minervini Leading Stock Deterioration, and Monty Defen... | <span class="badge badge-free">No API</span> |
| [Nepse Breakout Trade Planner]({{ '/en/skills/nepse-breakout-trade-planner/' | relative_url }}) | Convert nepse-vcp-screener candidates into manual-entry breakout trade plans | <span class="badge badge-free">No API</span> |
| [Nepse CANSLIM Screener]({{ '/en/skills/nepse-canslim-screener/' | relative_url }}) | CANSLIM-style screening adapted for NEPSE | <span class="badge badge-free">No API</span> |
| [Nepse Capital Gains Tax Notes]({{ '/en/skills/nepse-capital-gains-tax-notes/' | relative_url }}) | Compute Nepal capital gains tax on NEPSE share trades (5% long-term for >365-day holdings, 7 | <span class="badge badge-free">No API</span> |
| [Nepse Downtrend Duration Analyzer]({{ '/en/skills/nepse-downtrend-duration-analyzer/' | relative_url }}) | Analyze NEPSE composite index history to identify past downtrends, measure their duration (peak-to-trough and trough-... | <span class="badge badge-free">No API</span> |
| [Nepse Earnings Calendar]({{ '/en/skills/nepse-earnings-calendar/' | relative_url }}) | Generate a NEPSE quarterly-results calendar from the Nepali fiscal year (FY 2082/83) — listed companies must publish ... | <span class="badge badge-free">No API</span> |
| [Nepse Earnings Trade Analyzer]({{ '/en/skills/nepse-earnings-trade-analyzer/' | relative_url }}) | Score NEPSE post-quarterly-result reactions using the 5-factor framework (gap %, trend stage, volume surge, distance ... | <span class="badge badge-free">No API</span> |
| [Nepse Edge Candidate Agent]({{ '/en/skills/nepse-edge-candidate-agent/' | relative_url }}) | Detect NEPSE-specific anomalies in OHLCV data that may indicate exploitable edges — circuit-day breakouts, monsoon-se... | <span class="badge badge-free">No API</span> |
| [Nepse Edge Signal Aggregator]({{ '/en/skills/nepse-edge-signal-aggregator/' | relative_url }}) | Aggregate, deduplicate, and prioritize NEPSE edge tickets from nepse-edge-candidate-agent into a ranked signal list | <span class="badge badge-free">No API</span> |
| [Nepse Edge Strategy Designer]({{ '/en/skills/nepse-edge-strategy-designer/' | relative_url }}) | Convert NEPSE edge signals into backtestable strategy YAML drafts — entry rules, exit rules, position sizing, and fal... | <span class="badge badge-free">No API</span> |
| [Nepse Ibd Distribution Day Monitor]({{ '/en/skills/nepse-ibd-distribution-day-monitor/' | relative_url }}) | Monitor the NEPSE composite index for IBD-style distribution days — sessions where the index closes down ≥0 | <span class="badge badge-free">No API</span> |
| [Nepse Kanchi Dividend SOP]({{ '/en/skills/nepse-kanchi-dividend-sop/' | relative_url }}) | NEPSE-specific Kanchi 5-step dividend investing workflow | <span class="badge badge-free">No API</span> |
| [Nepse Macro Regime Detector]({{ '/en/skills/nepse-macro-regime-detector/' | relative_url }}) | Detect the macro regime affecting NEPSE — NRB monetary policy stance (currently tightening), USD/NPR direction, India... | <span class="badge badge-free">No API</span> |
| [Nepse Margin Eligibility]({{ '/en/skills/nepse-margin-eligibility/' | relative_url }}) | Check whether a NEPSE ticker is on the 123-name margin-eligible list (live since April 2026), report initial/maintena... | <span class="badge badge-free">No API</span> |
| [Nepse Market Breadth Analyzer]({{ '/en/skills/nepse-market-breadth-analyzer/' | relative_url }}) | Compute NEPSE market breadth indicators — advances vs | <span class="badge badge-free">No API</span> |
| [Nepse Market Top Detector]({{ '/en/skills/nepse-market-top-detector/' | relative_url }}) | Aggregate multiple NEPSE-specific top signals (BFI overconcentration, microfinance euphoria, distribution-day count, ... | <span class="badge badge-free">No API</span> |
| [Nepse Portfolio Tracker]({{ '/en/skills/nepse-portfolio-tracker/' | relative_url }}) | Track a NEPSE portfolio from MeroShare CSV/manual entries | <span class="badge badge-free">No API</span> |
| [Nepse Sector Analyst]({{ '/en/skills/nepse-sector-analyst/' | relative_url }}) | Rank NEPSE's 13 sector indices by recent performance, identify sector rotation, and flag leading/lagging sectors | <span class="badge badge-free">No API</span> |
| [Nepse Stanley Druckenmiller Investment]({{ '/en/skills/nepse-stanley-druckenmiller-investment/' | relative_url }}) | Synthesize NEPSE macro, micro, and sentiment signals into a Druckenmiller-style top-down read for NEPSE positioning | <span class="badge badge-free">No API</span> |
| [Nepse Technical Analyst]({{ '/en/skills/nepse-technical-analyst/' | relative_url }}) | Analyze NEPSE (Nepal Stock Exchange) stock charts from screenshots | <span class="badge badge-free">No API</span> |
| [Nepse Theme Detector]({{ '/en/skills/nepse-theme-detector/' | relative_url }}) | Detect emerging NEPSE investment themes by combining sector-rotation signals (from nepse-sector-analyst), breadth par... | <span class="badge badge-free">No API</span> |
| [Nepse Uptrend Analyzer]({{ '/en/skills/nepse-uptrend-analyzer/' | relative_url }}) | Compute the NEPSE Uptrend Ratio — the percentage of listed names trading above their 200-day SMA — as a single trend-... | <span class="badge badge-free">No API</span> |
| [Nepse Value Dividend Screener]({{ '/en/skills/nepse-value-dividend-screener/' | relative_url }}) | Screen NEPSE stocks for high dividend yield + reasonable valuation | <span class="badge badge-free">No API</span> |
| [Nepse VCP Screener]({{ '/en/skills/nepse-vcp-screener/' | relative_url }}) | Screen the NEPSE (Nepal Stock Exchange) universe for Mark Minervini's Volatility Contraction Pattern (VCP) | <span class="badge badge-free">No API</span> |
| [Options Strategy Advisor]({{ '/en/skills/options-strategy-advisor/' | relative_url }}) | Options trading strategy analysis and simulation tool | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Pair Trade Screener]({{ '/en/skills/pair-trade-screener/' | relative_url }}) | Statistical arbitrage tool for identifying and analyzing pair trading opportunities | <span class="badge badge-api">FMP Required</span> |
| [Parabolic Short Trade Planner]({{ '/en/skills/parabolic-short-trade-planner/' | relative_url }}) | Screen US equities for parabolic exhaustion patterns and generate conditional pre-market short plans, then evaluate i... | <span class="badge badge-api">FMP Required</span> |
| [PEAD Screener]({{ '/en/skills/pead-screener/' | relative_url }}) | Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns | <span class="badge badge-api">FMP Required</span> |
| [Portfolio Manager]({{ '/en/skills/portfolio-manager/' | relative_url }}) | Comprehensive portfolio analysis using Alpaca MCP Server integration to fetch holdings and positions, then analyze as... | <span class="badge badge-api">Alpaca Required</span> |
| [Position Sizer]({{ '/en/skills/position-sizer/' | relative_url }}) ★ | Calculate risk-based position sizes for long stock trades | <span class="badge badge-free">No API</span> |
| [Scenario Analyzer]({{ '/en/skills/scenario-analyzer/' | relative_url }}) | ニュースヘッドラインを入力として18ヶ月シナリオを分析するスキル。 scenario-analystエージェントで主分析を実行し、 strategy-reviewerエージェントでセカンドオピニオンを取得。 1次・2次・3次影響、推奨... | <span class="badge badge-free">No API</span> |
| [Sector Analyst]({{ '/en/skills/sector-analyst/' | relative_url }}) | This skill should be used when analyzing sector rotation patterns and market cycle positioning | <span class="badge badge-free">No API</span> |
| [Signal Postmortem]({{ '/en/skills/signal-postmortem/' | relative_url }}) | Record and analyze post-trade outcomes for signals generated by edge pipeline and other skills | <span class="badge badge-free">No API</span> |
| [Skill Designer]({{ '/en/skills/skill-designer/' | relative_url }}) | Design new Claude skills from structured idea specifications | <span class="badge badge-free">No API</span> |
| [Skill Idea Miner]({{ '/en/skills/skill-idea-miner/' | relative_url }}) | Mine Claude Code session logs for skill idea candidates | <span class="badge badge-free">No API</span> |
| [Skill Integration Tester]({{ '/en/skills/skill-integration-tester/' | relative_url }}) | Validate multi-skill workflows defined in CLAUDE | <span class="badge badge-free">No API</span> |
| [Stanley Druckenmiller Investment]({{ '/en/skills/stanley-druckenmiller-investment/' | relative_url }}) | Druckenmiller Strategy Synthesizer - Integrates 8 upstream skill outputs (Market Breadth, Uptrend Analysis, Market To... | <span class="badge badge-free">No API</span> |
| [Strategy Pivot Designer]({{ '/en/skills/strategy-pivot-designer/' | relative_url }}) | Detect backtest iteration stagnation and generate structurally different strategy pivot proposals when parameter tuni... | <span class="badge badge-free">No API</span> |
| [Technical Analyst]({{ '/en/skills/technical-analyst/' | relative_url }}) | This skill should be used when analyzing weekly price charts for stocks, stock indices, cryptocurrencies, or forex pairs | <span class="badge badge-free">No API</span> |
| [Theme Detector]({{ '/en/skills/theme-detector/' | relative_url }}) ★ | Detect and analyze trending market themes across sectors | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [Trade Hypothesis Ideator]({{ '/en/skills/trade-hypothesis-ideator/' | relative_url }}) | Generate falsifiable trade strategy hypotheses from market data, trade logs, and journal snippets | <span class="badge badge-free">No API</span> |
| [Trader Memory Core]({{ '/en/skills/trader-memory-core/' | relative_url }}) | Track investment theses across their lifecycle — from screening idea to closed position with postmortem | <span class="badge badge-free">No API</span> <span class="badge badge-optional">FMP Optional</span> |
| [Trading Skills Navigator]({{ '/en/skills/trading-skills-navigator/' | relative_url }}) | Recommend the right trading workflow, skillset, API profile, and setup path from a natural-language goal | <span class="badge badge-free">No API</span> |
| [Uptrend Analyzer]({{ '/en/skills/uptrend-analyzer/' | relative_url }}) | Analyzes market breadth using Monty's Uptrend Ratio Dashboard data to diagnose the current market environment | <span class="badge badge-free">No API</span> |
| [US Market Bubble Detector]({{ '/en/skills/us-market-bubble-detector/' | relative_url }}) ★ | Evaluates market bubble risk through quantitative data-driven analysis using the revised Minsky/Kindleberger framewor... | <span class="badge badge-free">No API</span> |
| [US Stock Analysis]({{ '/en/skills/us-stock-analysis/' | relative_url }}) ★ | Comprehensive US stock analysis including fundamental analysis (financial metrics, business quality, valuation), tech... | <span class="badge badge-free">No API</span> |
| [Value Dividend Screener]({{ '/en/skills/value-dividend-screener/' | relative_url }}) | Screen US stocks for high-quality dividend opportunities combining value characteristics (P/E ratio under 20, P/B rat... | <span class="badge badge-api">FMP Required</span> <span class="badge badge-optional">FINVIZ Optional</span> |
| [VCP Screener]({{ '/en/skills/vcp-screener/' | relative_url }}) ★ | Screen S&P 500 stocks for Mark Minervini's Volatility Contraction Pattern (VCP) | <span class="badge badge-api">FMP Required</span> |

★ = Hand-written detailed guide with examples, troubleshooting, and CLI reference.

See the [Skill Catalog]({{ '/en/skill-catalog/' | relative_url }}) for additional descriptions of all skills.
