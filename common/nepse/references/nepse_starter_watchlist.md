# NEPSE Watchlist

The plaintext file [`data/nepse_starter_watchlist.txt`](../../../data/nepse_starter_watchlist.txt) holds NEPSE symbols, one per line. Originally shipped as a 26-name *starter* set across the 13 sectors. **As of 2026-05-18 it was expanded to the full ~350-symbol NEPSE universe** (all symbols visible in `data/constituents.csv` after the daily fetcher's first run).

> **Important — knowledge-cutoff caveat:** the original curated 26 names were prominent NEPSE blue chips through early 2026. The expanded list mirrors whatever sharesansar's `/today-share-price` page returned at the time of regeneration. Listings, mergers, delistings, and trading-status changes are reflected automatically when you re-run the regenerator.

---

## How to refresh

The file is generated from `data/constituents.csv`, which the daily fetcher (`scripts/fetch_nepse_snapshot.py`) maintains. To rebuild the watchlist with the current universe:

```python
import csv
from pathlib import Path
symbols = sorted({
    (row.get("symbol") or "").strip().upper()
    for row in csv.DictReader(Path("data/constituents.csv").open())
    if (row.get("symbol") or "").strip()
})
Path("data/nepse_starter_watchlist.txt").write_text("\n".join(symbols) + "\n")
```

The watchlist updates organically as new IPOs list (they appear in next-day MeroShare/sharesansar snapshots → into `constituents.csv` → into the watchlist on next regeneration).

---

## What this list is (and isn't)

**It IS:** the operational NEPSE universe — every symbol your screeners can consider. Most screening skills filter internally by liquidity and history-length, so passing the full list is safe.

**It is NOT:**
- A buy list. Inclusion here means "trades on NEPSE," not "good to buy today."
- A registry edit. The `constituents:` block in [`config/registry.yaml`](../../../config/registry.yaml) is not parsed by the foundation code — the universe comes from the backend (`NepseClient.list_constituents()`). This file is what you'd pass to screener `--symbols` flags.

---

## How to use it

The plaintext version at [`data/nepse_starter_watchlist.txt`](../../../data/nepse_starter_watchlist.txt) holds the same 26 symbols, one per line. Pipe it into any NEPSE screener that accepts `--symbols`:

```bash
python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
  --symbols $(cat data/nepse_starter_watchlist.txt | tr '\n' ' ') \
  --output-dir reports/
```

Same pattern works for `nepse-canslim-screener`, `nepse-value-dividend-screener`, and any other screener that takes `--symbols`. Sector-level skills (breadth analyzer, sector analyst, uptrend analyzer) don't need it — they fetch the full universe from the backend.

---

## The 26 names

### Commercial Banks (BANKING) — 7

The dominant NEPSE sector by market cap. All seven are on most brokerages' "top 10 traded" list any given week.

| Symbol | Name | Why it's here |
|---|---|---|
| `NABIL` | Nabil Bank | Largest private commercial bank by deposit base; consistently high turnover |
| `NICA` | NIC Asia Bank | Historically top-3 turnover among BFIs |
| `EBL` | Everest Bank | Punjab National Bank joint-venture; long-running blue chip |
| `HBL` | Himalayan Bank | Oldest joint-venture private bank in Nepal |
| `GBIME` | Global IME Bank | One of the largest commercial banks post-merger |
| `SCB` | Standard Chartered Nepal | Foreign-affiliated; defensive name |
| `NMB` | NMB Bank | Top-tier commercial bank |

### Development Bank (DEVELOPMENT_BANK) — 1

| Symbol | Name | Why it's here |
|---|---|---|
| `MNBBL` | Muktinath Bikas Bank | Most-liquid development bank |

### Microfinance (MICROFINANCE) — 2

Microfinance is volatile — speculative runs are common. Two reference names:

| Symbol | Name | Why it's here |
|---|---|---|
| `CBBL` | Chhimek Laghubitta | Largest microfinance institution by assets |
| `NUBL` | Nirdhan Utthan Laghubitta | Top-3 microfinance by daily turnover |

### Hydropower (HYDROPOWER) — 5

NEPSE's largest sector by company count (~97 names). Watch a handful, not the whole sector.

| Symbol | Name | Why it's here |
|---|---|---|
| `UPPER` | Upper Tamakoshi Hydropower | Largest hydropower IPO ever; widely held |
| `CHCL` | Chilime Hydropower | Long-running profitable IPP |
| `NHPC` | National Hydro Power | Large-cap hydropower |
| `AHPC` | Arun Valley Hydropower | Mid-cap hydropower with consistent dividends |
| `SHPC` | Sanima Mai Hydropower | Liquid hydropower name |

### Life Insurance (LIFE_INSURANCE) — 2

| Symbol | Name | Why it's here |
|---|---|---|
| `NLIC` | Nepal Life Insurance | Largest domestic life insurer |
| `LICN` | Life Insurance Corp. (Nepal) | Indian LIC affiliate |

### Non-Life Insurance (NON_LIFE_INSURANCE) — 2

| Symbol | Name | Why it's here |
|---|---|---|
| `SICL` | Sagarmatha Insurance | Top non-life insurer |
| `NICL` | Nepal Insurance Co. | Oldest non-life insurer |

### Hotels & Tourism (HOTELS) — 2

Small sector (~8 listed), but two flagship names:

| Symbol | Name | Why it's here |
|---|---|---|
| `SHL` | Soaltee Hotel | Flagship 5-star hotel name |
| `OHL` | Oriental Hotels | Yak & Yeti operator |

### Manufacturing & Processing (MANUFACTURING) — 3

| Symbol | Name | Why it's here |
|---|---|---|
| `UNL` | Unilever Nepal | FMCG blue chip; low float, high price |
| `BNL` | Bottlers Nepal (Balaju) | Coca-Cola bottler |
| `SHIVM` | Shivam Cements | Largest listed cement producer |

### Trading (TRADING) — 1

| Symbol | Name | Why it's here |
|---|---|---|
| `STC` | Salt Trading Corp. | Only major trading-sector blue chip |

### Others (OTHERS) — 1

| Symbol | Name | Why it's here |
|---|---|---|
| `NTC` | Nepal Telecom | State telecom monopoly; large-cap |

---

## Sectors intentionally skipped

These sectors are part of NEPSE's 13-sector taxonomy but not in the starter list:

- **FINANCE** (finance companies, distinct from commercial banks) — typically thinner turnover than BANKING; add specific names in your second wave if interesting setups appear
- **MUTUAL_FUNDS** — closed-end funds; different mechanics from equities, not a fit for VCP/breakout screeners
- **INVESTMENT** — limited liquidity for swing trading

You can still chart-check names in these sectors as one-offs; just don't include them in your routine watchlist.

---

## When to expand

Once you've followed the daily routine for ~2 weeks and feel comfortable, expand. Suggested second-wave additions (~30 more):

- **More BANKING**: KBL, SBI, BOK, MBL, PRVU
- **More HYDROPOWER**: KKHC, BARUN, RHPC, RADHI, AKPL
- **More MICROFINANCE**: SMFBS, MERO, DDBL
- **More INSURANCE**: ALICL, PLI, UIC, IGI, NLG, NLO
- **More MANUFACTURING**: HDL, BNT, GBL
- **More HOTELS**: TRH

Pull current top-30 from [sharesansar.com](https://www.sharesansar.com) → Market → Top Turnover (filter by 30-day average) and merge with the list above.

---

## Sources to verify against

Before relying on this list operationally:

| What | Source |
|---|---|
| Currently listed companies | [nepalstock.com.np](https://www.nepalstock.com.np) → Securities → Company List |
| Top-traded names by turnover / volume | [sharesansar.com](https://www.sharesansar.com) → Market |
| Sector membership and ticker spelling | [merolagani.com](https://merolagani.com) → search ticker |
| Margin-eligible companies | [SEBON](https://www.sebon.gov.np) margin-trading circular |

If a symbol in this list doesn't appear on any current top-30 page or has been delisted/merged, drop it. Symbols can change after corporate actions (mergers, demergers); update accordingly.
