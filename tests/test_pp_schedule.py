"""Testy pp_schedule.build_schedule — mock demand/efficiency/capacity."""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_bom import EfficiencyEntry
from tools.lib.pp_capacity import DayCapacity
from tools.lib.pp_schedule import build_schedule, ScheduleSlot, _to_date


# ── Fixture helpers ───────────────────────────────────────────────────────────

def _cap(d: date, hours: float, persons: int = 3) -> DayCapacity:
    return DayCapacity(date=d, hours_per_day=hours, persons=persons,
                       regular_hours=8.0, overtime_hours=0.0)


def _eff(czni: str, uph: float) -> EfficiencyEntry:
    return EfficiencyEntry(czni_kod=czni, units_per_hour=uph)


def _order(czni: str, nazwa: str, ilosc: float, deadline: date, nr: str,
           kontrahent: str = "KNT") -> dict:
    return {
        "Nr_Zamowienia": nr,
        "Data_Realizacji": deadline,
        "Towar_Kod": czni,
        "Towar_Nazwa": nazwa,
        "Ilosc": ilosc,
        "Kontrahent_Kod": kontrahent,
    }


def _cap_range(start: date, days: int, hours: float) -> dict[date, DayCapacity]:
    """Tworzy capacity dla zakresu dat (days consecutive days)."""
    return {
        start + timedelta(days=i): _cap(start + timedelta(days=i), hours)
        for i in range(days)
    }


# ── Testy _to_date ───────────────────────────────────────────────────────────

def test_to_date_date():
    d = date(2026, 5, 4)
    assert _to_date(d) == d

def test_to_date_datetime():
    from datetime import datetime
    dt = datetime(2026, 5, 4, 8, 0)
    assert _to_date(dt) == date(2026, 5, 4)

def test_to_date_none():
    assert _to_date(None) is None


# ── Testy podstawowe ─────────────────────────────────────────────────────────

START = date(2026, 5, 4)  # poniedziałek

def test_schedule_jeden_produkt_jeden_dzien():
    """30 szt / 30 szt/h = 1h; capacity 8h → wszystko w 1 dniu."""
    demand = [_order("CZNI001", "Znicz A", 30, date(2026, 5, 10), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    assert len(slots) == 1
    assert slots[0].date == START
    assert slots[0].czni_kod == "CZNI001"
    assert abs(slots[0].qty - 30) < 0.01
    assert abs(slots[0].hours_needed - 1.0) < 0.01


def test_schedule_wiele_dni():
    """240 szt / 30 szt/h = 8h; capacity 4h/dzień → 2 dni."""
    demand = [_order("CZNI001", "Znicz A", 240, date(2026, 5, 15), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 4.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    assert len(slots) == 2
    assert slots[0].date == START
    assert slots[1].date == START + timedelta(days=1)
    total_qty = sum(s.qty for s in slots)
    assert abs(total_qty - 240) < 0.01


def test_schedule_pomija_dni_zero_mocy():
    """Dni z hours=0 są pomijane."""
    demand = [_order("CZNI001", "Znicz A", 120, date(2026, 5, 15), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = {
        START: _cap(START, 0),                           # pomiń
        START + timedelta(1): _cap(START + timedelta(1), 4.0),
        START + timedelta(2): _cap(START + timedelta(2), 4.0),
    }

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    assert all(s.hours_needed > 0 for s in slots)
    assert slots[0].date == START + timedelta(1)


def test_schedule_dwa_produkty_edf():
    """Produkt z wcześniejszym deadlinem planowany pierwszy."""
    d_wczes = date(2026, 5, 8)
    d_pozny = date(2026, 5, 20)
    demand = [
        _order("CZNI002", "Znicz B", 60, d_pozny,  "ZO/002"),
        _order("CZNI001", "Znicz A", 60, d_wczes,  "ZO/001"),
    ]
    eff = {
        "CZNI001": _eff("CZNI001", 30),
        "CZNI002": _eff("CZNI002", 30),
    }
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    first_codes = [s.czni_kod for s in slots if s.date == START]
    assert "CZNI001" in first_codes


def test_schedule_priorytet_wyprzedza_edf():
    """Zamówienie z priorytetem idzie przed wcześniejszym deadlinem bez priorytetu."""
    d_wczes = date(2026, 5, 8)
    d_pozny = date(2026, 5, 20)
    demand = [
        _order("CZNI001", "Znicz A", 60, d_wczes, "ZO/001"),  # wcześniej, bez priorytetu
        _order("CZNI002", "Znicz B", 60, d_pozny, "ZO/002"),  # późny, z priorytetem
    ]
    eff = {
        "CZNI001": _eff("CZNI001", 30),
        "CZNI002": _eff("CZNI002", 30),
    }
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, {"ZO/002"}, START)

    first_codes = [s.czni_kod for s in slots if s.date == START]
    assert "CZNI002" in first_codes


def test_schedule_produced_pokrywa_calkowicie():
    """Zamówienie w pełni pokryte → znika z harmonogramu."""
    demand = [_order("CZNI001", "Znicz A", 100, date(2026, 5, 10), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {"CZNI001": 100.0}, cap, set(), START)

    assert len(slots) == 0


def test_schedule_produced_czesciowe():
    """Produced pokrywa połowę → harmonogram dla drugiej połowy."""
    demand = [_order("CZNI001", "Znicz A", 60, date(2026, 5, 10), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {"CZNI001": 30.0}, cap, set(), START)

    total_qty = sum(s.qty for s in slots)
    assert abs(total_qty - 30.0) < 0.01


def test_schedule_agregacja_ten_sam_tydzien():
    """2 zamówienia CZNI001 z deadlines w tym samym tygodniu → agregowane (1 seria slotów)."""
    mon = date(2026, 5, 4)  # poniedziałek tygodnia 19
    fri = date(2026, 5, 8)  # piątek tego samego tygodnia
    demand = [
        _order("CZNI001", "Znicz A", 30, mon, "ZO/001"),
        _order("CZNI001", "Znicz A", 30, fri, "ZO/002"),
    ]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    # Powinny byc scalone w jedną serie — łączna qty = 60
    total_qty = sum(s.qty for s in slots)
    assert abs(total_qty - 60.0) < 0.01


def test_schedule_rozne_tygodnie_rozne_grupy():
    """2 zamówienia CZNI001 z deadlines w różnych tygodniach → osobne serie."""
    w1 = date(2026, 5, 8)   # tydzień 19
    w2 = date(2026, 5, 18)  # tydzień 21
    demand = [
        _order("CZNI001", "Znicz A", 30, w1, "ZO/001"),
        _order("CZNI001", "Znicz A", 30, w2, "ZO/002"),
    ]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 30, 8.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    # Dwie grupy → różne deadlines w slotach
    deadlines = {s.deadline for s in slots}
    assert len(deadlines) == 2


def test_schedule_brak_efficiency_pominięcie():
    """Produkt bez efficiency → pomijany (nie crashuje)."""
    demand = [
        _order("CZNI999", "Brak eff", 60, date(2026, 5, 10), "ZO/001"),
        _order("CZNI001", "Znicz A",  30, date(2026, 5, 10), "ZO/002"),
    ]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, set(), START)

    czni_kody = {s.czni_kod for s in slots}
    assert "CZNI999" not in czni_kody
    assert "CZNI001" in czni_kody


def test_schedule_pusty_demand():
    slots = build_schedule([], {"CZNI001": _eff("CZNI001", 30)}, {}, {}, set(), START)
    assert slots == []


def test_schedule_slot_pola():
    """Sprawdza wszystkie pola ScheduleSlot."""
    demand = [_order("CZNI001", "Znicz A", 30, date(2026, 5, 10), "ZO/001")]
    eff = {"CZNI001": _eff("CZNI001", 30)}
    cap = _cap_range(START, 10, 8.0)

    slots = build_schedule(demand, eff, {}, cap, {"ZO/001"}, START)

    s = slots[0]
    assert isinstance(s, ScheduleSlot)
    assert s.czni_nazwa == "Znicz A"
    assert "ZO/001" in s.order_numbers
    assert s.priority is True
    assert s.deadline == date(2026, 5, 10)
