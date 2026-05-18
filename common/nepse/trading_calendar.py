"""NEPSE trading calendar — sessions, weeks, circuit rules, holidays.

All values come from `config/nepse_rules.yaml`. Skills should never
hardcode session times or weekend days because NEPSE rules have changed
multiple times since late 2025.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from common.nepse._config import NepseConfigError, load_rules

# Nepal time is UTC+5:45 (no DST)
NPT = timezone(timedelta(hours=5, minutes=45), name="NPT")


@dataclass(frozen=True)
class CircuitBreaker:
    window_open: time
    window_close: time
    index_move_pct: float
    action: str


@dataclass(frozen=True)
class TradingCalendar:
    """View over `nepse_rules.yaml` — construct via `TradingCalendar.load()`."""

    trading_days_isoweekday: tuple[int, ...]
    session_open: time
    session_close: time
    pre_opening_open: time
    pre_opening_close: time
    pre_opening_price_band_pct: float
    amo_open: time
    amo_close: time
    daily_price_band_pct: float
    circuit_breakers: tuple[CircuitBreaker, ...]
    settlement_t_plus: int
    short_selling_enabled: bool
    holidays: frozenset[date] = field(default_factory=frozenset)

    # ---- factory ----------------------------------------------------------

    @classmethod
    def load(cls) -> TradingCalendar:
        rules = load_rules()
        try:
            session = rules["session"]
            pre = rules["pre_opening"]
            amo = rules["amo"]
            breakers = tuple(_parse_breaker(b) for b in rules["circuit_breakers"])
            return cls(
                trading_days_isoweekday=tuple(rules["trading_days_isoweekday"]),
                session_open=_parse_time(session["open"]),
                session_close=_parse_time(session["close"]),
                pre_opening_open=_parse_time(pre["open"]),
                pre_opening_close=_parse_time(pre["close"]),
                pre_opening_price_band_pct=float(pre["price_band_pct"]),
                amo_open=_parse_time(amo["open"]),
                amo_close=_parse_time(amo["close"]),
                daily_price_band_pct=float(rules["daily_price_band_pct"]),
                circuit_breakers=breakers,
                settlement_t_plus=int(rules["settlement_t_plus"]),
                short_selling_enabled=bool(rules["short_selling_enabled"]),
                holidays=frozenset(_parse_holidays(rules.get("holidays", []))),
            )
        except KeyError as exc:
            raise NepseConfigError(f"nepse_rules.yaml is missing required key: {exc}") from exc

    # ---- session / week queries ------------------------------------------

    def is_trading_day(self, day: date) -> bool:
        if day in self.holidays:
            return False
        return day.isoweekday() in self.trading_days_isoweekday

    def is_session_open(self, ts: datetime) -> bool:
        if ts.tzinfo is None:
            raise ValueError("is_session_open requires a timezone-aware datetime")
        local = ts.astimezone(NPT)
        if not self.is_trading_day(local.date()):
            return False
        return self.session_open <= local.time() < self.session_close

    def is_amo_window(self, ts: datetime) -> bool:
        """AMO window wraps midnight (18:00 → 06:00 next day)."""
        if ts.tzinfo is None:
            raise ValueError("is_amo_window requires a timezone-aware datetime")
        local = ts.astimezone(NPT).time()
        return local >= self.amo_open or local < self.amo_close

    def next_trading_day(self, after: date) -> date:
        d = after + timedelta(days=1)
        for _ in range(14):  # 14 days easily covers any holiday stretch
            if self.is_trading_day(d):
                return d
            d += timedelta(days=1)
        raise NepseConfigError(
            "No trading day found within 14 days — check holiday list and trading_days_isoweekday"
        )

    def settlement_date(self, trade_date: date) -> date:
        """T+N settlement date, skipping weekends and holidays."""
        d = trade_date
        for _ in range(self.settlement_t_plus):
            d = self.next_trading_day(d)
        return d

    def trading_days_between(self, start: date, end: date) -> int:
        """Inclusive count of trading days in [start, end]."""
        if end < start:
            return 0
        count = 0
        d = start
        while d <= end:
            if self.is_trading_day(d):
                count += 1
            d += timedelta(days=1)
        return count

    # ---- circuit breaker --------------------------------------------------

    def circuit_breaker_for(self, ts: datetime, index_move_pct: float) -> CircuitBreaker | None:
        """Return the breaker triggered at `ts` for an index move, or None."""
        if ts.tzinfo is None:
            raise ValueError("circuit_breaker_for requires a timezone-aware datetime")
        local = ts.astimezone(NPT).time()
        for cb in self.circuit_breakers:
            if cb.window_open <= local < cb.window_close and abs(index_move_pct) >= cb.index_move_pct:
                return cb
        return None


# ---- helpers --------------------------------------------------------------


def _parse_time(value: str) -> time:
    h, m = value.split(":")
    return time(hour=int(h), minute=int(m))


def _parse_breaker(raw: dict) -> CircuitBreaker:
    window = raw["session_window"]
    return CircuitBreaker(
        window_open=_parse_time(window[0]),
        window_close=_parse_time(window[1]),
        index_move_pct=float(raw["index_move_pct"]),
        action=str(raw["action"]),
    )


def _parse_holidays(raw: Iterable) -> Iterable[date]:
    for entry in raw:
        if isinstance(entry, date):
            yield entry
        elif isinstance(entry, str):
            yield date.fromisoformat(entry)
        elif isinstance(entry, dict) and "date" in entry:
            value = entry["date"]
            yield value if isinstance(value, date) else date.fromisoformat(str(value))
