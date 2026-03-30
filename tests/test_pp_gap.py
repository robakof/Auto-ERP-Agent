"""Testy pp_gap.compute_gap — mockowane dane."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_bom import BomEntry
from tools.lib.pp_gap import compute_gap, GapRow

_BOM = {
    "CZNI001": [
        BomEntry("CZNI001", "SZ0324", "Szkło", 0.98),
        BomEntry("CZNI001", "WK0001", "Wkład", 1.0),
        BomEntry("CZNI001", "FO0003", "Folia", 125.0),
    ],
    "CZNI002": [
        BomEntry("CZNI002", "SZ0324", "Szkło", 1.0),
    ],
}

_DEMAND = [
    {"Towar_Kod": "CZNI001", "Ilosc": 1000},
    {"Towar_Kod": "CZNI002", "Ilosc": 500},
]

_SUPPLY = {
    "SZ0324": 2000.0,
    "WK0001": 500.0,
    "FO0003": 10.0,
}


def test_compute_gap_podstawowy():
    gaps, warns = compute_gap(_DEMAND, _BOM, _SUPPLY)
    by_kod = {g.surowiec_kod: g for g in gaps}
    # SZ0324: 1000/0.98 + 500/1.0 = 1020.41 + 500 = 1520.41 → dostepne 2000 → brak 0
    assert by_kod["SZ0324"].brak == 0.0
    # WK0001: 1000/1 = 1000 → dostepne 500 → brak 500
    assert by_kod["WK0001"].brak == 500.0
    # FO0003: 1000/125 = 8 → dostepne 10 → brak 0
    assert by_kod["FO0003"].brak == 0.0


def test_compute_gap_sortowanie_brak_desc():
    gaps, _ = compute_gap(_DEMAND, _BOM, _SUPPLY)
    braki = [g.brak for g in gaps]
    assert braki == sorted(braki, reverse=True)


def test_compute_gap_brak_bom_warning_i_pominięcie():
    demand = [{"Towar_Kod": "CZNI999", "Ilosc": 100}]
    gaps, warns = compute_gap(demand, _BOM, _SUPPLY)
    assert gaps == [], "Produkt bez BOM nie trafia do gap analysis"
    assert any("CZNI999" in w for w in warns), "Powinien być warning o braku BOM"


def test_compute_gap_surowiec_bez_stanu():
    supply_bez = {}
    gaps, _ = compute_gap([{"Towar_Kod": "CZNI002", "Ilosc": 100}], _BOM, supply_bez)
    by_kod = {g.surowiec_kod: g for g in gaps}
    assert by_kod["SZ0324"].dostepne == 0.0
    assert by_kod["SZ0324"].brak == 100.0


def test_compute_gap_ilosc_zero_pomijana():
    demand = [{"Towar_Kod": "CZNI001", "Ilosc": 0}]
    gaps, _ = compute_gap(demand, _BOM, _SUPPLY)
    assert gaps == []


def test_compute_gap_pusta_lista():
    gaps, warns = compute_gap([], _BOM, _SUPPLY)
    assert gaps == []
    assert warns == []
