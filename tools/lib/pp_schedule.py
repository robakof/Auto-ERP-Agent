"""pp_schedule.py — Algorytm harmonogramu produkcji EDF + priorytet + agregacja.

Algorytm:
1. Agregacja zamówień per (czni_kod, iso_week(deadline)).
2. Odjęcie już wyprodukowanych (FIFO: najwcześniejsze deadlines pierwsze).
3. Sortowanie: priorytet → (0, deadline), reszta → (1, deadline).
4. Przydział slotów dzień po dniu (EDF), z pominięciem dni o zerowych mocach.
"""
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from tools.lib.pp_bom import EfficiencyEntry
from tools.lib.pp_capacity import DayCapacity

_MAX_DAYS_AHEAD = 500   # bezpiecznik — nie szukaj dalej niż ~1.5 roku


@dataclass
class ScheduleSlot:
    date: date
    czni_kod: str
    czni_nazwa: str
    qty: float              # ilość do wyprodukowania w tym slocie
    hours_needed: float     # godziny potrzebne na ten slot
    order_numbers: list[str] = field(default_factory=list)
    deadline: date = None
    priority: bool = False


def build_schedule(
    demand: list[dict],
    efficiency: dict[str, EfficiencyEntry],
    produced: dict[str, float],
    capacity: dict[date, DayCapacity],
    priorities: set[str],
    start_date: date,
) -> list[ScheduleSlot]:
    """Buduje harmonogram produkcji.

    demand        — wiersze z pp_demand.fetch_demand (dict z kluczami ERP)
    efficiency    — dict[czni_kod, EfficiencyEntry] z pp_bom.load_efficiency
    produced      — dict[czni_kod, qty] z pp_produced (lub {} jeśli niedostępne)
    capacity      — dict[date, DayCapacity] z pp_capacity.load_capacity
    priorities    — zbiór Nr_Zamowienia z Priorytet=1
    start_date    — od kiedy planujemy
    """
    tasks = _aggregate_demand(demand, efficiency, produced, priorities)
    tasks.sort(key=lambda t: (0 if t["priority"] else 1, t["deadline"]))
    return _assign_slots(tasks, efficiency, capacity, start_date)


# ── Agregacja popytu ──────────────────────────────────────────────────────────

def _aggregate_demand(
    demand: list[dict],
    efficiency: dict[str, EfficiencyEntry],
    produced: dict[str, float],
    priorities: set[str],
) -> list[dict]:
    """Grupuje demand po (czni_kod, iso_week), odejmuje produced (FIFO)."""
    groups = _group_by_week(demand, efficiency, priorities)
    return _subtract_produced(groups, produced)


def _group_by_week(
    demand: list[dict],
    efficiency: dict[str, EfficiencyEntry],
    priorities: set[str],
) -> dict[str, list[dict]]:
    """Grupuje wiersze po czni_kod → lista grup tygodniowych (posortowana wg deadline)."""
    week_groups: dict[tuple, dict] = {}

    for row in demand:
        czni_kod = row.get("Towar_Kod")
        if not czni_kod or czni_kod not in efficiency:
            continue
        deadline = _to_date(row.get("Data_Realizacji"))
        if deadline is None:
            continue

        iso_year, iso_week, _ = deadline.isocalendar()
        key = (czni_kod, iso_year, iso_week)

        if key not in week_groups:
            week_groups[key] = {
                "czni_kod": czni_kod,
                "czni_nazwa": row.get("Towar_Nazwa", ""),
                "qty": 0.0,
                "deadline": deadline,
                "order_numbers": [],
                "priority": False,
            }

        g = week_groups[key]
        g["qty"] += float(row.get("Ilosc") or 0)
        if deadline < g["deadline"]:
            g["deadline"] = deadline

        nr = row.get("Nr_Zamowienia")
        nr_str = str(nr) if nr is not None else None
        if nr_str and nr_str not in g["order_numbers"]:
            g["order_numbers"].append(nr_str)
        if nr_str and nr_str in priorities:
            g["priority"] = True

    # Pogrupuj per czni_kod, posortuj po deadline (FIFO dla odjęcia produced)
    by_czni: dict[str, list[dict]] = defaultdict(list)
    for g in week_groups.values():
        by_czni[g["czni_kod"]].append(g)
    for lst in by_czni.values():
        lst.sort(key=lambda g: g["deadline"])
    return by_czni


def _subtract_produced(
    by_czni: dict[str, list[dict]],
    produced: dict[str, float],
) -> list[dict]:
    """Odejmuje już wyprodukowane FIFO (najwcześniejszy deadline pierwszy)."""
    tasks = []
    for czni_kod, groups in by_czni.items():
        remaining = float(produced.get(czni_kod, 0))
        for g in groups:
            if remaining >= g["qty"]:
                remaining -= g["qty"]
                continue
            g = dict(g)  # kopia — nie mutuj oryginału
            g["qty"] -= remaining
            remaining = 0
            tasks.append(g)
    return tasks


# ── Przydział slotów ──────────────────────────────────────────────────────────

def _assign_slots(
    tasks: list[dict],
    efficiency: dict[str, EfficiencyEntry],
    capacity: dict[date, DayCapacity],
    start_date: date,
) -> list[ScheduleSlot]:
    """Przydziela sloty dzień po dniu (EDF). Zwraca listę ScheduleSlot."""
    slots = []
    current_date = start_date
    remaining_today = _hours_for(capacity, current_date)

    for task in tasks:
        czni_kod = task["czni_kod"]
        uph = efficiency[czni_kod].units_per_hour
        hours_left = task["qty"] / uph

        while hours_left > 1e-6:
            if current_date is None:
                warnings.warn(
                    f"[SCHEDULE] Brak mocy produkcyjnych dla {czni_kod} "
                    f"(deadline {task['deadline']}) — pominięto resztę",
                    stacklevel=2,
                )
                break
            current_date, remaining_today = _advance_to_working_day(
                capacity, current_date, remaining_today, start_date
            )
            if current_date is None:
                warnings.warn(
                    f"[SCHEDULE] Brak mocy produkcyjnych dla {czni_kod} "
                    f"(deadline {task['deadline']}) — pominięto resztę",
                    stacklevel=2,
                )
                break

            today_h = min(hours_left, remaining_today)
            slots.append(ScheduleSlot(
                date=current_date,
                czni_kod=czni_kod,
                czni_nazwa=task["czni_nazwa"],
                qty=round(today_h * uph, 4),
                hours_needed=round(today_h, 4),
                order_numbers=list(task["order_numbers"]),
                deadline=task["deadline"],
                priority=task["priority"],
            ))

            hours_left -= today_h
            remaining_today -= today_h

    return slots


def _advance_to_working_day(
    capacity: dict[date, DayCapacity],
    current_date: date,
    remaining_today: float,
    start_date: date,
) -> tuple[date | None, float]:
    """Przesuwa current_date do dnia z mocami > 0. Zwraca (date, hours) lub (None, 0)."""
    limit = start_date + timedelta(days=_MAX_DAYS_AHEAD)
    while remaining_today <= 0 and current_date < limit:
        current_date += timedelta(days=1)
        remaining_today = _hours_for(capacity, current_date)
    if current_date >= limit:
        return None, 0.0
    return current_date, remaining_today


def _hours_for(capacity: dict[date, DayCapacity], d: date) -> float:
    """Zwraca dostępne godziny dla daty. Jeśli brak w pliku → 0 (bez warnu)."""
    dc = capacity.get(d)
    return dc.hours_per_day if dc else 0.0


def _to_date(val) -> date | None:
    if isinstance(val, date) and not hasattr(val, "hour"):
        return val
    if hasattr(val, "date"):
        return val.date()
    return None
