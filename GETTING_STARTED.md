# Getting Started — Trading NEPSE with Claude Trading Skills

A hands-on, no-jargon walkthrough for amateur NEPSE traders. You'll go from a fresh clone to a working daily/weekly trading rhythm.

**You'll need:**

- A computer with Python 3.9+
- A [MeroShare](https://meroshare.cdsc.com.np) account (for your portfolio + dividends + IPOs)
- A broker account with online TMS (Trading Management System) for placing orders
- ~30 minutes/day before market open (11:00 NPT) for the routine
- ~1 hour/week on weekends for portfolio review

**You'll NOT get:** financial advice, an auto-trader, a signal service, or any guarantee of profit. This is a tool that turns your judgment into a structured process.

---

## Table of contents

- [0. The mental model](#0-the-mental-model)
- [1. One-time setup (Day 0)](#1-one-time-setup-day-0)
- [2. Your daily 30 minutes](#2-your-daily-30-minutes-pre-market-before-1100-npt)
- [3. Your weekly hour](#3-your-weekly-hour-weekends)
- [4. When you close a trade](#4-when-you-close-a-trade)
- [5. Every quarter](#5-every-quarter)
- [6. Glossary](#6-glossary)
- [7. Common issues](#7-common-issues)
- [8. Where to go next](#8-where-to-go-next)
- [9. Disclaimer](#9-disclaimer)

---

## 0. The mental model

This repo is a **toolbox, not a robot**. Think of it as a kitchen full of well-labeled knives — each Python script is one tool that does one job. You decide when and how to use them.

A normal trading day looks like this:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Run scripts  │ →  │  Reports in  │ →  │   Your eyes  │ →  │  Manual buy  │
│ in terminal  │    │  reports/    │    │  + judgment  │    │  at your TMS │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
                                   ┌──────────────────────┐
                                   │  Record the thesis   │
                                   │  in state/theses/    │
                                   └──────────────────────┘
```

Five workflows define **the order to run things in**. The two most-used:

| Workflow | When | What it does |
|---|---|---|
| [`nepse-market-regime-daily`](workflows/nepse-market-regime-daily.yaml) | Every morning before 11:00 NPT | Tells you whether today is a *go* or a *no-go* for new trades |
| [`nepse-swing-opportunity-daily`](workflows/nepse-swing-opportunity-daily.yaml) | After the regime check says *go* | Finds candidates, sizes them, builds a trade plan |

If you remember nothing else: **regime first, screener second, sizing third, order at TMS last, record the thesis after.**

---

## 1. One-time setup (Day 0)

### 1.1 Install Python

You need **Python 3.9 or newer**. Check:

```bash
python3 --version
```

If it says `3.9.x`, `3.10.x`, `3.11.x`, or `3.12.x`, you're good. Otherwise install from [python.org](https://www.python.org/downloads/).

### 1.2 Clone the repo + install dependencies

```bash
git clone https://github.com/aashutoshpy/claude-trading-skills-nepse.git
cd claude-trading-skills-nepse
pip install -e .
```

`pip install -e .` installs the libraries the scripts need: `pyyaml`, `requests`, `scipy`, `yfinance`. The `-e` flag means "editable" — if you later edit a script, your changes take effect immediately.

If `pip` doesn't exist, try `pip3` or `python3 -m pip install -e .`.

### 1.3 Verify the foundation works

```bash
python3 -m pytest common/nepse/tests/ -v
```

You should see **57 tests pass** in well under a second. If they pass, the NEPSE data layer is wired up correctly. If they fail, see [§7 Common issues](#7-common-issues).

### 1.4 Pick a backend

A *backend* is the thing that fetches NEPSE data. Three exist:

| Backend | Status (May 2026) | Setup |
|---|---|---|
| `csv` **(recommended)** | Works offline against local CSVs you populate via the daily fetcher (next section). | None — built in. |
| `nepalstock` | Broken — server has an incomplete TLS chain *and* returns 401 to direct API calls (anti-bot). Shipped for the day they fix it. | None. `NEPSE_INSECURE_TLS=1` gets past TLS but not the 401. |
| `community` | Broken — the only PyPI lib (`nepse-api 1.x`) depends on a 3rd-party token service (`samrid.me`) and a domain (`newweb.nepalstock.com`) that have both been offline. | `pip install nepse-api` (won't work, but documented). |

**Use `csv`** by default until live-fetch backends become viable again:

```bash
export NEPSE_BACKEND=csv
```

The CSV backend reads from `data/ohlcv/<SYMBOL>.csv` files. The fetcher
(introduced next) populates them by scraping sharesansar's public
`/today-share-price` page once per trading day.

### 1.5 Pick a watchlist + (optionally) tune the margin list

You don't need to fill in the full ~284 NEPSE universe yourself — that comes from the data backend you picked in §1.4 (`NepseClient.list_constituents()` fetches it live). What you do need is two things:

1. **A watchlist** — 20–30 NEPSE names you'll actually look at and screen each morning. This isn't a registry edit; it's a list of symbols you pass to screeners via `--symbols`.
2. **A margin-eligible list** — which names are on SEBON's margin-trading circular, so the portfolio tracker's margin warnings work correctly.

This repo ships starter versions of both. Use them as-is to get going; refine over time.

#### Starter watchlist

[`data/nepse_starter_watchlist.txt`](data/nepse_starter_watchlist.txt) — 26 NEPSE blue chips diversified across 10 sectors:

```
NABIL, NICA, EBL, HBL, GBIME, SCB, NMB    (Commercial Banks)
MNBBL                                      (Development Bank)
CBBL, NUBL                                 (Microfinance)
UPPER, CHCL, NHPC, AHPC, SHPC              (Hydropower)
NLIC, LICN                                 (Life Insurance)
SICL, NICL                                 (Non-Life Insurance)
SHL, OHL                                   (Hotels)
UNL, BNL, SHIVM                            (Manufacturing)
STC                                        (Trading)
NTC                                        (Others — Nepal Telecom)
```

These have been NEPSE blue chips through early 2026 — high turnover, broad investor interest, plenty of historical data. Good practice ground for screeners and chart-checking.

Full rationale, sector-by-sector breakdown, and a "second-wave" expansion list (the next 30 names to add once comfortable) live in [`common/nepse/references/nepse_starter_watchlist.md`](common/nepse/references/nepse_starter_watchlist.md).

> **Knowledge-cutoff caveat:** these names were prominent through early 2026. Spot-check each on sharesansar.com → Company Profile before relying on them — mergers, delistings, or trading-status changes may have moved things since. The reference doc has details.

#### Starter margin-eligible list

[`config/registry.yaml`](config/registry.yaml) ships with ~19 known-eligible blue chips already populated in `margin_eligible_symbols:`. This is **a starter, not the full SEBON 123-name list.** Open the file and look at the `margin_eligible_symbols:` block — those are the names where the portfolio tracker will correctly flag margin positions and compute margin-call distance.

Before relying on margin warnings operationally, verify the list against:

- [SEBON](https://www.sebon.gov.np) → margin-trading circular (authoritative)
- Your broker's margin-stocks page

Add or remove names in `config/registry.yaml`'s `margin_eligible_symbols:` block as needed.

#### What about `constituents:`?

You'll notice the `constituents:` block in `config/registry.yaml` is empty. **Leave it that way.** The dataclass that loads this file doesn't parse `constituents:` — the universe comes from your backend, not the YAML. Eventually a `scripts/refresh_nepse_registry.py` helper will cache the list there, but for now the empty seed is intentional.

#### Sector codes (if you ever edit `config/registry.yaml`)

The 13 sector IDs are: `BANKING`, `DEVELOPMENT_BANK`, `FINANCE`, `MICROFINANCE`, `HYDROPOWER`, `LIFE_INSURANCE`, `NON_LIFE_INSURANCE`, `HOTELS`, `MANUFACTURING`, `TRADING`, `MUTUAL_FUNDS`, `INVESTMENT`, `OTHERS`. They're UPPER_SNAKE and case-sensitive.

### 1.6 Build up your OHLCV history

The VCP screener needs **~200 trading days** of OHLCV per name to detect a base. You have three paths to get there:

#### Path A — Daily forward accumulation (set-and-forget)

```bash
python3 scripts/fetch_nepse_snapshot.py
```

Scrapes sharesansar's public `/today-share-price` page (no anti-bot, no auth) and appends today's OHLCV row to `data/ohlcv/<SYMBOL>.csv` for every actively-trading NEPSE symbol (~330 on a normal day). Re-running same-day is a no-op (de-duplicated by date). After ~200 trading days you have a full base.

**Automate it with launchd** (macOS) so you don't have to remember:

```bash
sed "s|\$HOME|$HOME|g; s|\$PROJECT_DIR|$(pwd)|g" \
  launchd/com.nepse.fetch-daily.plist \
  > ~/Library/LaunchAgents/com.nepse.fetch-daily.plist
launchctl load ~/Library/LaunchAgents/com.nepse.fetch-daily.plist
```

Fires at 09:45 UTC daily (= 15:30 NPT, just after market close). Logs to `logs/launchd_nepse_fetch.log`.

Fetcher flags:

| Flag | Purpose |
|---|---|
| `--data-dir custom/path` | Override data root (default: `data/`) |
| `--symbols NABIL UPPER NICA` | Only fetch listed symbols |
| `--as-of 2026-05-17` | Date label to write (defaults to today) |
| `--dry-run` | Print what would change; no writes |

#### Path B — Backfill history per name (paste-from-browser)

To screen NABIL today instead of in 10 months, get its history *now*:

1. Open `https://www.sharesansar.com/company/NABIL` in your browser
2. Click the **Price History** tab — sharesansar renders 100–200 days of OHLCV in a table
3. Select all rows in the table, copy
4. Pipe into the importer:

```bash
# macOS — copy first, then:
pbpaste | python3 scripts/import_ohlcv_from_table.py --symbol NABIL

# Or save the paste to a file, then:
python3 scripts/import_ohlcv_from_table.py --symbol NABIL --input nabil.tsv
```

The importer is forgiving — tab/comma/whitespace-separated, header row optional, tolerates extra columns (turnover, % change, etc.). Merges into `data/ohlcv/NABIL.csv`, de-duped by date.

Repeat for each name in your watchlist (~26 names × 30 sec = 15 min one-time setup). Then re-run path A daily on top to keep it fresh.

#### Path C — Drop in your broker's CSV / a Google Sheet export

Any CSV with columns `date,open,high,low,close,volume,prev_close` (extras tolerated) dropped at `data/ohlcv/<SYMBOL>.csv` is read directly by the CSV backend. Use this if you have a broker statement export or a community-maintained dataset.

#### Required schema

```
date,open,high,low,close,volume,prev_close
2026-05-18,1180.00,1212.00,1175.00,1207.50,84320,1180.00
2026-05-17,1170.00,1196.00,1165.00,1180.00,61200,1175.00
```

Date in ISO format. Order doesn't matter — backend sorts. `prev_close` optional.

### 1.7 Smoke test the screener

Run the VCP screener on a handful of names from your watchlist:

```bash
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols NABIL UPPER NICA --output-dir reports/
```

This should write two files into `reports/`:

- `nepse_vcp_YYYY-MM-DD.json` — machine-readable
- `nepse_vcp_YYYY-MM-DD.md` — human-readable summary

Open the `.md` file. If you see a structured report (even if no setups qualify), the pipeline works. You're ready.

---

## 2. Your daily 30 minutes (pre-market, before 11:00 NPT)

NEPSE opens at 11:00 NPT and closes at 15:00 NPT, Monday through Friday. The routine below assumes you start around 10:00 — plenty of time to check, screen, plan, and queue orders.

> **Cadence reference:** this routine maps to two workflow manifests — [`nepse-market-regime-daily.yaml`](workflows/nepse-market-regime-daily.yaml) and [`nepse-swing-opportunity-daily.yaml`](workflows/nepse-swing-opportunity-daily.yaml). The YAML files are the canonical contracts; this section is the friendly version.

### Step 1 — Regime check (~5 min)

Run these three scripts in any order:

```bash
python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
  --output-dir reports/

python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
  --output-dir reports/

python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
  --output-dir reports/
```

Each writes a `.md` + `.json` pair to `reports/`. Open the three `.md` files and look for:

| Report | What to look at | Good sign | Warning sign |
|---|---|---|---|
| `nepse_breadth_*.md` | Advance/decline, % above SMA50/SMA200 | A/D positive, >50% above SMA200 | A/D negative, <30% above SMA200 |
| `nepse_uptrend_*.md` | The Uptrend Ratio (UTR) | UTR > 60% and rising | UTR < 40% or sharply falling |
| `nepse_sectors_*.md` | Sector leaders/laggards | Real leaders rotating; no single sector >40% of moves | Microfinance/hydropower bubbles, narrow leadership |

**Your decision:** is today a *go* (look for new trades) or *no-go* (just monitor existing)?

- **Go** — broadly positive breadth, UTR rising, real sector rotation → proceed to Step 2.
- **No-go** — breath collapsing, UTR diving, only one sector dragging the index → close terminal, manage existing positions today.

> A **regime** is your overall market environment for the day. *RISK_ON* means conditions favor new long trades; *RISK_OFF* means avoid adding risk; *NEUTRAL* means be choosy.

### Step 2 — Screen for candidates (~5 min)

Only if regime was *go*. First, append today's OHLCV (skip on weekends/holidays):

```bash
python3 scripts/fetch_nepse_snapshot.py
```

Then run the VCP screener against your watchlist:

```bash
NEPSE_BACKEND=csv python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols $(cat data/nepse_starter_watchlist.txt | tr '\n' ' ') \
  --output-dir reports/
```

The `$(cat ... | tr '\n' ' ')` part expands the plaintext watchlist into a space-separated symbol list. Drop the `--symbols` flag to screen the full universe (all symbols that have ≥200 days of cached history).

Open `reports/nepse_vcp_<today>.md`. You'll see a ranked list of names with **VCP setups** — Volatility Contraction Patterns, a classic Mark Minervini setup where price tightens into a base before breaking out.

Pick the **top 3–5** by score. Note their symbols.

> **VCP in plain English:** the stock is trending up, has built a series of pullbacks each smaller than the last (volatility is *contracting*), and is sitting near the high of its recent range — primed for a breakout. The screener has already calibrated for NEPSE's 15% daily price band.

### Step 3 — Chart-confirm the candidates (~10 min)

The screener can be wrong. **You** look at each chart and confirm.

For each of your 3–5 candidates:

1. Open [sharesansar.com](https://www.sharesansar.com) or [merolagani.com](https://merolagani.com).
2. Search the symbol → daily chart, 6-month view.
3. Eyeball check:
   - Is the price above its 50-day and 200-day moving averages? (Stage 2 uptrend)
   - Are the recent pullbacks getting *smaller* (tighter and tighter)?
   - Is volume drying up during the pullbacks (lower volume than the rises)?
   - Is the most recent close near the top of the recent range?

If yes to most → **keep**. If no → **drop** from your shortlist.

> If you want a structured second opinion, you can also take a screenshot of the chart and ask Claude (with the `nepse-technical-analyst` skill loaded) to review it — that skill is **image-input only**, no CLI.

### Step 4 — Size each position (~3 min per name)

For each name that survived Step 3, decide your entry and stop:

- **Entry** = a price slightly above today's high (the breakout trigger).
- **Stop** = a price below the recent base low (your "I'm wrong" exit).

Then size the position based on your account:

```bash
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 1000000 \
  --entry 425.00 \
  --stop 400.00 \
  --risk-pct 1.0 \
  --output-dir reports/
```

Substitute your numbers:

- `--account-size 1000000` — your total trading account in NPR (NRs. 10 lakh in this example)
- `--entry 425.00` — entry price (in NPR)
- `--stop 400.00` — stop-loss price (in NPR)
- `--risk-pct 1.0` — how much of the account you're willing to lose if the stop hits (1% is a common starting point)

The script tells you exactly how many shares to buy.

> **1R** is your *risk unit* — the rupee amount you lose if the stop hits. With a 10-lakh account and 1% risk, 1R = NRs. 10,000. A *2R target* is a price where your gain would be twice that risk (NRs. 20,000). Pros usually target 2R–3R per trade.

### Step 5 — Build the trade plan (~3 min)

The trade planner takes the screener's JSON output plus your sizing and builds a complete plan:

```bash
python3 skills/nepse-breakout-trade-planner/scripts/plan_breakouts.py \
  --vcp-json reports/nepse_vcp_<today>.json \
  --account-size 1000000 \
  --risk-pct 1.0 \
  --output-dir reports/
```

Open `reports/nepse_trade_plans_<today>.md`. For each candidate it gives you:

- **Entry trigger** — buy if price prints at or above this level
- **Stop-loss** — price that closes the trade as a loss
- **1R / 2R / 3R targets** — partial-take levels
- **AMO instructions** — if you can't be at the terminal at 11:00, the plan tells you how to queue an order in the AMO window (18:00–06:00 NPT)
- **Share count** — based on your account size and risk

This is the document you act on.

### Step 6 — Place the order at your broker (~3 min)

Open your broker's TMS web UI. For each plan you intend to take:

1. New Order → Buy → Limit
2. Symbol = the ticker in your plan
3. Quantity = share count from the plan
4. Limit price = the entry trigger from the plan
5. Validity = **Day** (or **GTC** if your broker supports it)

If you can't watch the market live, queue an **AMO** (After-Market Order) in the 18:00–06:00 window — your broker will release it when the market opens.

> **Manual is the only option.** NEPSE has no public broker API. Every order goes through the broker's web UI or by phone. Every plan from this repo ends here.

### Step 7 — Record the thesis (~1 min)

The moment you place an order, log it:

```bash
python3 skills/trader-memory-core/scripts/thesis_ingest.py \
  --source vcp-screener \
  --input reports/nepse_vcp_<today>.json \
  --state-dir state/theses/
```

This reads the screener output and creates an `IDEA` thesis file in `state/theses/`. The thesis records *why you're taking this trade* before you know the outcome — your future self will thank you.

When the order fills, transition it to `ACTIVE`:

```bash
# Replace <id> with the thesis ID printed by thesis_ingest
python3 skills/trader-memory-core/scripts/thesis_store.py --state-dir state/theses/ \
  transition <id> ENTRY_READY --reason "validated"

python3 skills/trader-memory-core/scripts/thesis_store.py --state-dir state/theses/ \
  open-position <id> --actual-price 425.00 --actual-date 2026-05-18 --shares 235
```

If you took the order but didn't get filled by end-of-day, leave the thesis at `ENTRY_READY` and try again tomorrow.

---

## 3. Your weekly hour (weekends)

Once a week — Saturday or Sunday — review your full portfolio. Maps to [`nepse-core-portfolio-weekly.yaml`](workflows/nepse-core-portfolio-weekly.yaml).

### 3.1 Export your portfolio from MeroShare

1. Log into [meroshare.cdsc.com.np](https://meroshare.cdsc.com.np).
2. Click **My Portfolio**.
3. Click **Export** (button at top right).

MeroShare downloads a CSV. Open it in Excel/Google Sheets. **The columns won't match what this repo expects** — MeroShare's export uses Nepali-format headers and includes columns you don't need.

Rename / reshape the file so it has **exactly these columns** (the script will refuse rows that don't match):

| Column | Type | Required | Notes |
|---|---|---|---|
| `symbol` | string (uppercase) | yes | e.g., `NABIL` |
| `shares` | number | yes | Fractional OK |
| `avg_cost` | number | yes | Your weighted average cost in NPR |
| `entry_date` | YYYY-MM-DD | optional | When you opened the position. Used for capital-gains-tax classification. |
| `is_margin` | true/false | optional | Whether the position is held on margin. Defaults to `false`. |

Example CSV:

```csv
symbol,shares,avg_cost,entry_date,is_margin
NABIL,100,1180.00,2025-12-15,false
UPPER,200,425.00,2026-03-22,true
NICA,50,890.00,2026-04-10,false
```

Save the file as `data/nepse_portfolio.csv` (create the `data/` folder if needed: `mkdir -p data`).

### 3.2 Run the portfolio tracker

```bash
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv data/nepse_portfolio.csv \
  --output-dir reports/
```

Open `reports/nepse_portfolio_<today>.md`. You'll see:

- **Per-position P&L** in NPR and %
- **Sector concentration** — % of portfolio in each of the 13 NEPSE sectors
- **Margin warnings** — for each margin position, distance to the maintenance-margin call price
- **Cross-check warning** — if any position you tagged `is_margin=true` is *not* on the SEBON 123-name margin-eligible list, you'll see a flag

### 3.3 Decide what to act on

For each position in the report, ask:

1. **Sector concentration** — is any single sector >30% of your portfolio? Consider trimming.
2. **Margin warning** — is the call distance <10%? Consider reducing the position to drop margin usage.
3. **Stop violated** — has price closed below your original stop (from the trade plan)? Time to exit.
4. **Target hit** — has price tagged 1R/2R/3R? Consider trimming a portion (`trim` subcommand below).

### 3.4 Update theses for trims and closes

For partial sells (taking profit at a target):

```bash
python3 skills/trader-memory-core/scripts/thesis_store.py --state-dir state/theses/ \
  trim <id> --shares-sold 50 --price 478.00 --date 2026-05-18
```

For full exits:

```bash
python3 skills/trader-memory-core/scripts/thesis_store.py --state-dir state/theses/ \
  close <id> \
  --exit-reason target_hit \
  --actual-price 510.00 \
  --actual-date 2026-05-18
```

Valid `--exit-reason` values: `stop_hit`, `target_hit`, `time_stop`, `manual`.

### 3.5 Check review-due theses

Some positions deserve a periodic look-back even if nothing has changed price-wise:

```bash
python3 skills/trader-memory-core/scripts/thesis_review.py \
  --state-dir state/theses/ review-due --as-of 2026-05-18
```

This lists theses that haven't been touched in a while. Look at each, decide *thesis still valid?* and either:

- Mark it reviewed: `... mark-reviewed <id> --outcome OK`
- Or close it if the original reason is gone.

---

## 4. When you close a trade

The moment you exit any position, do the close-and-learn loop. Maps to [`nepse-trade-memory-loop.yaml`](workflows/nepse-trade-memory-loop.yaml).

### 4.1 Close the thesis

```bash
python3 skills/trader-memory-core/scripts/thesis_store.py --state-dir state/theses/ \
  close <id> \
  --exit-reason target_hit \
  --actual-price 510.00 \
  --actual-date 2026-05-18
```

### 4.2 Generate the postmortem

```bash
python3 skills/trader-memory-core/scripts/thesis_review.py \
  --state-dir state/theses/ postmortem <id>
```

Writes a markdown postmortem to `state/journal/pm_<id>.md`. It includes entry/exit prices, return %, holding period, and prompts to fill in *what worked* / *what didn't* / *what to do differently*.

Read it. Be honest with yourself.

### 4.3 Estimate the tax

```bash
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --symbol NABIL \
  --entry-price 425.00 \
  --exit-price 510.00 \
  --shares 235 \
  --holding-days 180
```

You'll see:

- **Tax rate** — 7.5% if held ≤365 days (short-term), 5% if held >365 days (long-term)
- **Tax amount** in NPR
- **Net gain** after tax
- **Days to long-term** if you sold close to the 365-day mark — the script tells you how many more days you'd have needed to hold to qualify for the lower rate

> Nepal's capital gains rates as of May 2026: **5% long-term (>365 days)** and **7.5% short-term**. The government has *proposed* a uniform **10%** but it's not enacted. Your broker withholds the tax at sale.

### 4.4 Holding-period awareness

If a position is close to crossing into long-term, the trade planner's exit timing matters. For positions sitting near a target with <30 days to the long-term threshold, consider waiting if the chart still looks fine. Use:

```bash
python3 skills/nepse-capital-gains-tax-notes/scripts/estimate_tax.py \
  --entry-price 425.00 --exit-price 510.00 --shares 235 --holding-days 340
```

The output will show the savings if you wait the extra 26 days.

---

## 5. Every quarter

Nepali fiscal year quarters end at **Ashwin, Poush, Chaitra, Ashadh** (roughly mid-Oct, mid-Jan, mid-Apr, mid-Jul). Companies have a statutory 30-day window after the quarter-end to file results. Two to three weeks after each quarter-end, do the quarterly review. Maps to [`nepse-quarterly-results-review.yaml`](workflows/nepse-quarterly-results-review.yaml).

### 5.1 Refresh the registry if listings have changed

Check NEPSE's *listed companies* page and SEBON's margin-eligible circular. Any additions/delistings? Update `config/registry.yaml`.

### 5.2 Generate the quarterly earnings calendar

```bash
python3 skills/nepse-earnings-calendar/scripts/generate_calendar.py \
  --output-dir reports/
```

Open `reports/nepse_earnings_calendar_<today>.md`. You'll see expected filing dates per company, based on the Nepali FY quarter-end + 30-day statutory window.

### 5.3 Score post-earnings reactions

For any name you hold or watch that recently filed:

```bash
python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
  --symbol NABIL --report-date 2026-04-30 \
  --output-dir reports/
```

The output scores the post-filing reaction on five factors (gap, trend, volume, distance to MA200, distance to MA50). High scores indicate a strong, sustainable reaction worth a momentum entry; low scores indicate a fade.

### 5.4 Postmortem every closed position from the quarter

For each thesis you closed in the last quarter, run the postmortem if you didn't already:

```bash
python3 skills/trader-memory-core/scripts/thesis_review.py \
  --state-dir state/theses/ postmortem <id>
```

### 5.5 Update your mental playbook

Look across the quarter's postmortems. Which screener calls were profitable? Which setups failed most often? Which sector concentrations hurt? Write notes to yourself — these inform next quarter's bias.

---

## 6. Glossary

The vocabulary you'll see in reports, in order of how often it shows up.

**Regime** — overall market environment. `RISK_ON` = green light for new trades; `RISK_OFF` = preserve capital; `NEUTRAL` = be selective. Set by §2 Step 1.

**Stage 2** — Mark Minervini's term for a stock in a sustained uptrend, trading above both its 50-day and 200-day moving averages, with both averages rising. The only stage where VCP setups are tradeable.

**VCP (Volatility Contraction Pattern)** — a base where each pullback is *smaller* than the last and volume *dries up* on the pullbacks. Indicates absorption before a likely breakout.

**Contraction** — one of the smaller pullbacks inside a VCP base. A "clean" VCP usually has 2–4 contractions.

**Breadth** — how *many* stocks are moving up vs down, regardless of the index level. Strong breadth (a wide A/D, many names above SMA200) means the rally has support. Weak breadth means a few large caps are masking distribution.

**Advance/Decline (A/D)** — count of stocks closing higher minus those closing lower on the day. Cumulative A/D over weeks is a breadth indicator.

**UTR (Uptrend Ratio)** — percent of NEPSE names trading above their 200-day SMA. >60% is healthy; <40% is bearish.

**1R / 2R / 3R** — multiples of your *risk unit*. 1R = the rupee amount you'd lose if the stop hits. 2R target = a take-profit price where your gain is twice that risk. Common targeting: trim ⅓ at 1R, ⅓ at 2R, hold ⅓ for 3R+.

**Risk %** — fraction of your account you're willing to lose on one trade. 1% is a textbook starting point; new traders often use 0.5%.

**Stop-loss** — the price at which you exit a losing trade. Either a *percent stop* (X% below entry) or a *swing-low stop* (just below the most recent low in the base). Wider stops mean fewer shares for the same risk.

**ATR (Average True Range)** — average size of a daily price move over the last N days (usually 14). Wider ATR = more volatile name = wider stops needed.

**AMO (After-Market Order)** — orders queued between 18:00 and 06:00 NPT for the next trading session. Lets you place orders without being at the terminal at 11:00.

**Circuit breaker** — NEPSE-wide trading halt rules. If the index moves ±5% between 11:00–13:00, the whole market halts for 15 minutes. If the index moves ±8% between 13:00–15:00, the market closes for the day.

**15% daily price band** — individual stocks can move at most ±15% from yesterday's close. Hits the *upper circuit* (limit up) at +15%, *lower circuit* (limit down) at −15%. Raised from 10% on April 17, 2026.

**Pre-opening band** — 3% range around yesterday's close during the pre-opening session, used for price discovery. Raised from 2% in April 2026.

**T+2 settlement** — trades settle (cash and shares change hands) 2 business days after the trade date. Means you can't sell what you bought today until day +2.

**Margin call** — your broker demands more collateral because your margin position has lost too much. SEBON: **30% initial** (minimum equity to open), **20% maintenance** (minimum equity to hold). The portfolio tracker tells you your distance to the call.

**Margin-eligible** — only 123 of the ~284 NEPSE names are approved for margin trading (as of mid-April 2026). `config/registry.yaml` holds the list.

**Bonus dividend vs cash dividend** — NEPSE companies often pay dividends as *bonus shares* (you get extra shares) rather than cash. A "10% bonus" means 10 new shares for every 100 held. Recalculate your `avg_cost` after a bonus.

**BFI** — Banks and Financial Institutions. The dominant sector group on NEPSE: commercial banks, development banks, finance companies, microfinance.

**Microfinance** — small-loan financial institutions. Volatile sector, prone to speculative runs.

**Hydropower** — largest NEPSE sector by company count (97 names) but small by market cap. Seasonal cash flows tied to monsoon.

---

## 7. Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| "Screener returned 0 candidates" | With `csv` backend: not enough history yet (VCP needs ~200 days); the per-symbol CSV is short. Otherwise: `--symbols` was empty/wrong, or there are genuinely no setups today. | If you just installed the repo, you need to run `scripts/fetch_nepse_snapshot.py` daily for ~200 trading days OR paste historical OHLCV into the CSVs manually. Setup-empty days are normal in weak regimes. |
| `ModuleNotFoundError: No module named 'yaml'` | Dependencies not installed | `pip install -e .` from the repo root |
| `python3: command not found` | Python not installed or not on PATH | Install from [python.org](https://www.python.org/downloads/), restart terminal |
| Backend timeout / scraper error | NEPSE site changed or is down | `NEPSE_BACKEND=community python3 ...` (install with `pip install nepse-api` first) |
| Default `nepalstock` scraper returns `CERTIFICATE_VERIFY_FAILED` or `401 UNAUTHORIZED ACCESS` | nepalstock.com.np has both an incomplete TLS chain AND anti-bot defenses (rejects direct API access). The scraper backend currently can't pass these reliably. | The scraper is **not operationally functional** against the live site right now. Use the **community backend** instead (next row). `NEPSE_INSECURE_TLS=1` gets you past the TLS gate but you'll still hit the 401 — the env flag is shipped for when nepalstock fixes their auth side, not a complete fix today. |
| Community backend says "No supported NEPSE community library is installed/importable" even after `pip install nepse-api` | The PyPI package `nepse-api 1.x` installs as top-level module `nepse` (not `nepse_api`), and it uses Python's `cgi` stdlib module — **removed in Python 3.13+** | Run `python3 --version`. If **3.12 or older**: `pip install nepse-api && NEPSE_BACKEND=community python3 ...` should work (the backend now tries `import nepse` first). If **3.13 or newer**: `pip install legacy-cgi nepse-api`, then retry. If your env is 3.13+ and the polyfill doesn't take, the cleanest path is a fresh Python 3.12 env: `conda create -n nepse-3.12 python=3.12 && conda activate nepse-3.12 && pip install -e . && pip install nepse-api`. |
| MeroShare CSV columns don't match | MeroShare export uses Nepali headers + extras | Open in spreadsheet → rename/keep only `symbol, shares, avg_cost, entry_date, is_margin` → save as CSV |
| "Stop hit immediately" after a buy | NEPSE's 15% band can cause big single-day moves; your stop was too tight | Widen the percent stop to ~7–10% or use the swing-low method |
| Margin warning on a non-margin position | Your CSV row has `is_margin=true` but the symbol isn't on SEBON's list | Verify against `config/registry.yaml` `margin_eligible_symbols`; fix the CSV |
| Tax estimate says short-term but you held >365 days | `entry_date` in your portfolio CSV is wrong or missing | Edit the CSV; the tax script reads holding-days from this field |
| `reports/` folder doesn't exist | First-ever run | Scripts create it automatically; or `mkdir reports/` to pre-create |
| Pre-opening price doesn't match scripts | Pre-opening 3% band differs from the regular 15% band | Wait for 11:00 open; scripts assume regular session |

If a script raises an unexpected error, the traceback usually points at the right file. Read it; nine times out of ten it's a config/path issue, not a code bug.

---

## 8. Where to go next

When you're ready to go deeper:

- [README.md](README.md) — full skill catalog, all 27 NEPSE skills with one-line summaries
- [workflows/README.md](workflows/README.md) — the canonical workflow contract, schema, validator codes
- [docs/en/skill-catalog.md](docs/en/skill-catalog.md) — skill-by-skill long-form reference
- [config/nepse_rules.yaml](config/nepse_rules.yaml) — every NEPSE rule the scripts depend on, in one file
- [common/nepse/references/nepse_market_rules_changelog.md](common/nepse/references/nepse_market_rules_changelog.md) — chronological log of NEPSE rule changes
- Any [skills/nepse-*/SKILL.md](skills/) — per-skill flags, edge cases, and worked examples

Less-used but useful when relevant:

- **`nepse-canslim-screener`** — alternative to VCP, screens on the CANSLIM 7-factor framework
- **`nepse-value-dividend-screener`** — for income-style trades around the Bhadra–Mangsir AGM cycle
- **`nepse-kanchi-dividend-sop`** — full 5-step dividend-investing workflow
- **`nepse-margin-eligibility`** — quick check whether a ticker is on SEBON's margin list + margin-call distance calc
- **`nepse-macro-regime-detector`** — combines NRB repo, USD/NPR, Nifty, Brent, gold into a regime label
- **`nepse-theme-detector`** — identifies active themes (monsoon hydropower, rate-cut financials, etc.)

---

## 9. Disclaimer

This repository is for **educational and research purposes only**. It is not financial advice, investment advisory service, tax advice, legal advice, a signal service, or a broker execution platform. Trading and investing involve risk, including loss of principal. Past performance, backtests, screens, reports, and AI-generated analysis do not guarantee future results. All trading decisions, position sizing, tax/regulatory compliance, and broker usage are the user's responsibility.

Provided under the MIT License, **AS IS, WITHOUT WARRANTY**.
