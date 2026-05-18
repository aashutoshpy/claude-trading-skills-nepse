# NEPSE Sector Dynamics

Per-sector drivers, regime sensitivities, and historical regimes. Use
this when interpreting the `rank_nepse_sectors.py` output to understand
*why* a sector is leading or lagging.

## Commercial Banks (BANKING)

- 18 listed names; largest by market cap; weights ~30-40% of the composite
- Drivers: NRB monetary policy (repo rate, CRR), bank lending growth,
  NPL trends, dividend cycle (Bhadra-Mangsir each year)
- Bull regime: NRB cutting rates, strong loan growth, low NPLs
- Bear regime: NRB tightening, NPL spike, regulatory clampdown
- **Currently (May 2026):** NRB tightened to 5.0% repo in Jan-Mar 2026;
  bank sector tends to lag in tightening cycles

## Development Banks

- ~17 listed names; smaller scale than commercial banks
- Drivers: same as commercial banks but with higher beta
- Often lead commercial banks by 1-2 weeks on direction changes

## Finance Companies (FINANCE)

- ~15 listed names; non-bank lending
- Drivers: NRB policy + retail credit demand
- Highest beta within the financial-services cluster
- Frequently outperforms commercial banks in late-bull phases

## Microfinance (MICROFINANCE)

- ~50 listed names; HIGHEST beta on NEPSE
- Drivers: rural credit demand, NRB MFI policy, asset-quality cycles
- Bull regime: 6-month rolling returns can exceed +200%
- Bear regime: drawdowns of -50% in 2-3 months
- **Speculative read:** when microfinance is the lone leader for 2+
  weeks, NEPSE is often near a cyclical top

## Hydropower (HYDROPOWER)

- 97 listed names — largest single sector by count
- Drivers:
  - Monsoon water levels (June-September = peak generation)
  - India-Nepal electricity export pricing
  - New project commissioning announcements
  - Government policy (PPA terms, royalty changes)
- Cycle: typically strong May-August (pre-monsoon optimism), corrects
  September-November (post-monsoon reality), basing November-April
- Index can move +/- 10% in a week on a single PPA or commissioning headline

## Life Insurance / Non-Life Insurance

- ~15 / ~20 listed names respectively
- Drivers:
  - Life: bond-yield sensitivity (carry trade), savings-rate competition
  - Non-Life: claim experience (cyclical), premium pricing
- Often lead the financial cluster in rate-cut anticipation cycles
- More defensive than banks; outperform in falling-rate regimes

## Hotels & Tourism (HOTELS)

- 8 listed names; thin trading
- Drivers: tourist arrivals (peak Oct-Mar), airline capacity, FX
- Rarely actionable except around the autumn tourist season

## Manufacturing & Processing (MANUFACTURING)

- 26 listed names; mixed underlying businesses (cement, food, textiles)
- Drivers vary widely — treat individual names, not the sector
- Sector index is noisy due to compositional heterogeneity

## Trading (TRADING)

- 4 listed names; effectively unbacktrackable as a sector
- Ignore the sector ranking unless one specific name (e.g. Bishal Bazaar)
  is moving

## Mutual Funds (MUTUAL_FUNDS)

- ~30 closed-end NAV-tracking funds
- Discount/premium to NAV is the only edge here
- Sector ranking is rarely useful (just tracks underlying holdings)

## Investment (INVESTMENT)

- 7 holding companies
- Same comment as mutual funds — track NAV discount/premium per name

## Others

- 10-name catch-all
- Skip the sector ranking signal here

## Rotation Heuristics

| Signal | Implied regime |
|---|---|
| Banks #1, microfinance #13 | Risk-off; macro tightening |
| Microfinance #1, banks #5+ | Risk-on speculative; watch for top |
| Hydropower #1 in May-July | Pre-monsoon momentum (often persists) |
| Hydropower #13 in September-October | Post-monsoon disappointment |
| Insurance leading + banks lagging | Rate-cut anticipation |
| Manufacturing #1 | Almost always a noise / compositional artifact |

## Historical Regime Notes

- **Mar 2026:** NRB tightened repo 4.25% → 5.0%; banks and finance
  underperformed for ~6 weeks
- **Apr 2026:** Margin trading launched for 123 names — included most
  banks + several mid-cap hydropower; some leverage-driven outperformance
  in the eligible list in the first 2-3 weeks
- **Late 2025 political transition:** generalized risk-off, microfinance
  hit hardest (-40% peak-to-trough); recovery began January 2026
