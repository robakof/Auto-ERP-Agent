"""pp_gap.py — Gap analysis: zapotrzebowanie vs stany OTOR_SUR.

Formuła: zapotrzebowanie = SUM(ilosc_czni / mianownik) per surowiec.
CZNI bez BOM w słowniku → RuntimeError (brak BOM = błędna decyzja zakupowa).
"""
from collections import defaultdict
from dataclasses import dataclass

from tools.lib.pp_bom import BomEntry


@dataclass
class GapRow:
    surowiec_kod: str
    surowiec_nazwa: str
    potrzeba: float
    dostepne: float
    brak: float


def compute_gap(
    demand: list[dict],
    bom: dict[str, list[BomEntry]],
    supply: dict[str, float],
) -> tuple[list[GapRow], list[str]]:
    """Oblicza gap analysis.

    Zwraca (gaps, warnings).
    Rzuca RuntimeError jeśli CZNI z zamówień nie ma BOM.
    """
    total_needed: dict[str, float] = defaultdict(float)
    sur_nazwa: dict[str, str] = {}
    warnings_out: list[str] = []

    for row in demand:
        czni_kod = row.get("Towar_Kod", "")
        ilosc = float(row.get("Ilosc") or 0)
        if not czni_kod or ilosc == 0:
            continue
        if czni_kod not in bom:
            raise RuntimeError(
                f"Brak BOM dla {czni_kod} w pliku wyceny — "
                "uzupełnij plik przed uruchomieniem."
            )
        for entry in bom[czni_kod]:
            needed = ilosc / entry.mianownik
            total_needed[entry.surowiec_kod] += needed
            sur_nazwa[entry.surowiec_kod] = entry.surowiec_nazwa

    gaps: list[GapRow] = []
    for sur_kod, potrzeba in total_needed.items():
        dostepne = supply.get(sur_kod, 0.0)
        brak = max(0.0, potrzeba - dostepne)
        gaps.append(GapRow(
            surowiec_kod=sur_kod,
            surowiec_nazwa=sur_nazwa.get(sur_kod, ""),
            potrzeba=round(potrzeba, 4),
            dostepne=dostepne,
            brak=round(brak, 4),
        ))

    gaps.sort(key=lambda r: r.brak, reverse=True)
    return gaps, warnings_out
