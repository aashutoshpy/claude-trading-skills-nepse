# NEPSE Market Rules Changelog

This file is the audit log for changes to `config/nepse_rules.yaml`.
NEPSE has changed rules multiple times since late 2025 — when you
edit the YAML, add a one-line entry here so future code archaeology
is possible.

## Format

```
YYYY-MM-DD  <field> changed: <old> → <new>   (source: <URL or doc>)
```

## History

2026-05-17  Initial seed of `config/nepse_rules.yaml` for the NEPSE adaptation.
            Baseline values reflect verified state at this date:
            - trading_days_isoweekday: Mon-Fri (changed from Sun-Thu in late 2025
              after government adopted Sat+Sun weekend)
              source: https://www.sharesansar.com/newsdetail/nepal-stock-exchange-opens-monday-to-friday-under-new-government-timings-2026-04-08
            - daily_price_band_pct: 15.0 (raised from 10.0 on 2026-04-17)
              source: https://www.sharesansar.com/newsdetail/nepse-new-rules-alert-stock-limits-upgraded-to-15-starting-today-market-to-suspend-at-8-index-change-2026-04-20
            - pre_opening.price_band_pct: 3.0 (raised from 2.0 on 2026-04-17)
              source: as above
            - circuit_breakers: two-tier 5% (11:00-13:00 → halt_15min) / 8% (13:00-15:00 → close_for_day)
              (simplified from prior 4%/5%/6% three-tier)
            - amo: 18:00-06:00 next-session queueing window (permitted April 2026)
              source: https://kathmandupost.com/money/2026/04/16/nepse-allows-round-the-clock-order-placement-as-trading-rules-revised
            - margin: enabled with 30% initial / 20% maintenance (live mid-April 2026)
              source: https://eng.bajarkochirfar.com/2026/03/26/nepse-opens-the-way-for-margin-trading-procedure-2082-passed-now-the-way-to-buy-shares-by-paying-30-percent-is-open/
            - settlement_t_plus: 2 (no T+1 transition announced)
            - short_selling_enabled: false (SEBON has discussed; no 2026 enablement)
            - capital_gains_tax: 5% LT (>365d) / 7.5% ST; proposed uniform 10% not enacted
              source: https://taxadvisornepal.com/capital-gain-tax-in-nepal/

## Pending / known upcoming changes

- Session start may extend from 11:00 to 10:00 (NEPSE board approved internally;
  not live as of 2026-05-17). When live, edit `session.open` to "10:00" and
  add an entry above.
  source: https://news.nepsetrading.com/preparation-underway-to-extend-nepse-trading-hours-market-may-open-at-10-am
