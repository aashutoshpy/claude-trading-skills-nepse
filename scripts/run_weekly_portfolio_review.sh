#!/usr/bin/env bash
# NEPSE Weekly Portfolio Review — wrapper for the Claude Desktop weekly routine.
#
# Requires data/nepse_portfolio.csv (export from MeroShare → My Portfolio).
# See skills/nepse-portfolio-tracker/SKILL.md for the column schema.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REPORTS_DIR="${REPORTS_DIR:-reports}"
PORTFOLIO_CSV="${PORTFOLIO_CSV:-data/nepse_portfolio.csv}"
mkdir -p "$REPORTS_DIR"

log() { printf '\n=== %s ===\n' "$1" >&2; }

if [[ ! -f "$PORTFOLIO_CSV" ]]; then
  cat >&2 <<EOF
ERROR: portfolio CSV not found at $PORTFOLIO_CSV

To populate it:
  1. Log into meroshare.cdsc.com.np
  2. My Portfolio → Export
  3. Save as $PORTFOLIO_CSV
  4. Ensure columns match: symbol, shares, avg_cost, entry_date, is_margin
     (See skills/nepse-portfolio-tracker/SKILL.md for the schema.)

Skipping weekly review.
EOF
  exit 2
fi

log "1/2  Portfolio tracker (P&L, sector concentration, margin warnings)"
python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
  --portfolio-csv "$PORTFOLIO_CSV" --output-dir "$REPORTS_DIR"

log "2/2  Refreshing today's snapshot so positions are mark-to-market"
python3 scripts/fetch_nepse_snapshot.py

log "Done. Reports in $REPORTS_DIR/"
ls -lt "$REPORTS_DIR"/nepse_portfolio_*.{md,json} 2>/dev/null | head -4 >&2 || true
