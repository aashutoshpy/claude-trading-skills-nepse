"""Tests for the NEPSE edge signal aggregator."""

from datetime import date

from signal_aggregator import aggregate


def _ticket(detector: str, as_of: str, candidates: list[dict], ticket_id: str = "t1") -> dict:
    return {
        "ticket_id": ticket_id,
        "detector": detector,
        "as_of": as_of,
        "candidates": candidates,
    }


# ---- basic ----------------------------------------------------------


def test_no_tickets_returns_empty():
    assert aggregate([], today=date(2026, 5, 17)) == []


def test_single_ticket_single_candidate_yields_one_signal():
    tickets = [_ticket(
        "circuit_day_continuation", "2026-05-17",
        [{"symbol": "NABIL", "sector": "BANKING"}],
    )]
    signals = aggregate(tickets, today=date(2026, 5, 17))
    assert len(signals) == 1
    assert signals[0].symbol == "NABIL"


def test_stale_tickets_filtered_out():
    tickets = [_ticket(
        "circuit_day_continuation", "2026-05-01",
        [{"symbol": "NABIL", "sector": "BANKING"}],
    )]
    signals = aggregate(tickets, today=date(2026, 5, 17), max_age_days=7)
    assert signals == []


def test_confluence_increases_when_same_symbol_in_multiple_detectors():
    tickets = [
        _ticket("circuit_day_continuation", "2026-05-17",
                [{"symbol": "NABIL", "sector": "BANKING"}], ticket_id="t1"),
        _ticket("bfi_dividend_pullback", "2026-05-17",
                [{"symbol": "NABIL", "sector": "BANKING"}], ticket_id="t2"),
    ]
    signals = aggregate(tickets, today=date(2026, 5, 17))
    assert len(signals) == 1
    s = signals[0]
    assert s.confluence == 2
    assert set(s.detectors_flagged) == {"circuit_day_continuation", "bfi_dividend_pullback"}
    assert len(s.ticket_refs) == 2


def test_sector_boost_applied_when_sector_leading():
    tickets = [_ticket(
        "circuit_day_continuation", "2026-05-17",
        [{"symbol": "NABIL", "sector": "BANKING"}],
    )]
    sig_no_boost = aggregate(tickets, today=date(2026, 5, 17), leading_sectors=["HYDROPOWER"])[0]
    sig_boost = aggregate(tickets, today=date(2026, 5, 17), leading_sectors=["BANKING"])[0]
    assert sig_boost.composite_score > sig_no_boost.composite_score
    assert sig_boost.sector_boost == 20
    assert sig_no_boost.sector_boost == 0


def test_status_classification():
    # Build a ticket with everything aligned for ACT
    tickets = [
        _ticket("circuit_day_continuation", "2026-05-17",
                [{"symbol": "NABIL", "sector": "BANKING"}]),
        _ticket("bfi_dividend_pullback", "2026-05-17",
                [{"symbol": "NABIL", "sector": "BANKING"}]),
    ]
    signals = aggregate(tickets, today=date(2026, 5, 17), leading_sectors=["BANKING"])
    assert signals[0].status in ("ACT", "WATCH")


def test_multiple_symbols_sorted_by_score_descending():
    tickets = [
        _ticket("circuit_day_continuation", "2026-05-17",
                [{"symbol": "STRONG", "sector": "BANKING"}], ticket_id="t1"),
        _ticket("bfi_dividend_pullback", "2026-05-17",
                [{"symbol": "STRONG", "sector": "BANKING"}], ticket_id="t2"),
        _ticket("microfinance_turnaround", "2026-05-10",      # older
                [{"symbol": "WEAK", "sector": "MICROFINANCE"}], ticket_id="t3"),
    ]
    signals = aggregate(tickets, today=date(2026, 5, 17), leading_sectors=["BANKING"])
    assert signals[0].symbol == "STRONG"


def test_uppercases_symbol():
    tickets = [_ticket(
        "circuit_day_continuation", "2026-05-17",
        [{"symbol": "nabil", "sector": "BANKING"}],
    )]
    signals = aggregate(tickets, today=date(2026, 5, 17))
    assert signals[0].symbol == "NABIL"


def test_bad_as_of_string_treated_as_undated():
    tickets = [_ticket(
        "circuit_day_continuation", "not-a-date",
        [{"symbol": "X", "sector": "BANKING"}],
    )]
    signals = aggregate(tickets, today=date(2026, 5, 17))
    # Falls through (recency defaults to 50)
    assert len(signals) == 1
