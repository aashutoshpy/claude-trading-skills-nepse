#!/usr/bin/env bash
# NEPSE Quarterly Results Review — wrapper for the quarterly routine.
#
# Nepali FY quarter-ends + statutory T+30 filing window:
#   Q1 ends ~Ashwin (Oct 17)  → routine fires ~Dec 1
#   Q2 ends ~Poush  (Jan 14)  → routine fires ~Mar 1
#   Q3 ends ~Chaitra (Apr 13) → routine fires ~May 28
#   Q4 ends ~Ashadh (Jul 16)  → routine fires ~Aug 30
#
# Adjust the schedule each year — NEPSE rules shift slightly per FY.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REPORTS_DIR="${REPORTS_DIR:-reports}"
mkdir -p "$REPORTS_DIR"

log() { printf '\n=== %s ===\n' "$1" >&2; }

log "1/2  Building NEPSE quarterly earnings calendar"
python3 skills/nepse-earnings-calendar/scripts/generate_calendar.py \
  --output-dir "$REPORTS_DIR"

log "2/2  Scoring post-earnings reactions (gap, trend, volume, MA200/MA50)"
# Iterate over each ticker in the watchlist file (if present) and score
# their most-recent print. If no watchlist, just score the starter set.
WATCHLIST="${WATCHLIST:-data/nepse_starter_watchlist.txt}"
if [[ -f "$WATCHLIST" ]]; then
  SYMBOLS=$(grep -v '^#' "$WATCHLIST" | tr '\n' ' ')
else
  SYMBOLS="NABIL NICA EBL UPPER CHCL NLIC"
fi

for sym in $SYMBOLS; do
  # Use today as a stand-in report-date; the analyzer falls back to most
  # recent print if today is not a filing date. (Light error tolerance
  # so one bad ticker doesn't kill the whole run.)
  python3 skills/nepse-earnings-trade-analyzer/scripts/analyze_earnings.py \
    --symbol "$sym" --report-date "$(date +%F)" --output-dir "$REPORTS_DIR" \
    2>/dev/null || printf '  skipped %s (no data or pre-filing)\n' "$sym" >&2
done

log "Done. Quarterly outputs in $REPORTS_DIR/"
ls -lt "$REPORTS_DIR"/{nepse_earnings_calendar_*,nepse_earnings_analysis_*}.md 2>/dev/null | head -10 >&2 || true
