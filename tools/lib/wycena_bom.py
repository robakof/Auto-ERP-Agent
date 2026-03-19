"""
wycena_bom.py — Definicja 16 wierszy BOM i obliczenia mianowników dla generatora Wyceny Zniczy.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class BomRow:
    wlasciwosc: str          # kolumna E
    nazwa: str               # kolumna G
    akronim: Optional[str]   # kolumna H
    mianownik: Optional[object]  # kolumna J (liczba lub None)


def build_bom_rows(
    paletka: Optional[float],
    paleta: Optional[float],
    szklo_akronim: Optional[str],
    offer_group_id: int,
) -> list[BomRow]:
    """
    Zwraca 16 wierszy BOM dla jednego produktu.

    paletka: TwJ_PrzeliczL gdzie TwJ_JmZ = 'opak.'
    paleta:  TwJ_PrzeliczL gdzie TwJ_JmZ = 'paleta'
    szklo_akronim: kod surowca Szkło z algorytmu wyszukiwania lub None
    offer_group_id: ID grupy oferty — wyznacza mianownik Szkła (0.99)
    """
    folia_pakowa = math.ceil((1000 / 45) * paletka) if paletka is not None else None
    folia_stretch = paleta * 2 if paleta is not None else None
    szklo_mianownik = 0.99 if offer_group_id is not None else 0.98

    return [
        BomRow("Surowiec", "Dekiel",                   None,          1),
        BomRow("Surowiec", "Brokat",                   None,          None),
        BomRow("Surowiec", "Etykieta",                 "ET0077",      1),
        BomRow("Surowiec", "Folia pakowa",             "FO0003",      folia_pakowa),
        BomRow("Surowiec", "Folia Stretch",            "FO0004",      folia_stretch),
        BomRow("Surowiec", "Paletka",                  None,          paletka),
        BomRow("Surowiec", "Farba lakier do szkła",    None,          None),
        BomRow("Surowiec", "Spód",                     None,          1),
        BomRow("Surowiec", "Szkło",                    szklo_akronim, szklo_mianownik),
        BomRow("Surowiec", "Wkład",                    None,          1),
        BomRow("Koszt",    "Energia Otorowo",           None,          1),
        BomRow("Koszt",    "Godzina pracy malarni",    None,          None),
        BomRow("Koszt",    "Dodatkowe koszty Otorowo", None,          1),
        BomRow("Koszt",    "Roboczogodzina Otorowo",   None,          None),
        BomRow("Koszt",    "Premia",                   None,          1),
        BomRow("Koszt",    "BDO",                      None,          1),
    ]
