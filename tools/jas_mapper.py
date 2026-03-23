"""
jas_mapper.py — Mapowanie wierszy AILO.wz_jas_export → CreateShipmentRequest.

Jeden WZ (wz_id) = wiele wierszy (jeden per typ palety) → jeden shipment z listą cargo[].
Wiersze z typ_opakowania = NULL (brak WMS) → pomijane w cargo.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()


def _loading_place() -> dict:
    """Stały adres nadawcy z .env."""
    return {"address": {
        "name":    os.getenv("JAS_LOADING_NAME", ""),
        "street":  os.getenv("JAS_LOADING_STREET", ""),
        "houseNo": os.getenv("JAS_LOADING_HOUSE_NO", ""),
        "city":    os.getenv("JAS_LOADING_CITY", ""),
        "zipCode": os.getenv("JAS_LOADING_ZIP", ""),
        "country": os.getenv("JAS_LOADING_COUNTRY", "PL"),
    }}


def _delivery_place(row: dict) -> dict:
    return {"address": {
        "name":    row.get("odbiorca_nazwa") or "",
        "street":  row.get("odbiorca_ulica") or "",
        "houseNo": row.get("odbiorca_nr_domu") or "",
        "city":    row.get("odbiorca_miasto") or "",
        "zipCode": row.get("odbiorca_kod_pocztowy") or "",
        "country": row.get("odbiorca_kraj") or "PL",
    }}


def _cargo_item(row: dict) -> Optional[dict]:
    """Zwraca cargo dict lub None gdy brak danych WMS."""
    if not row.get("typ_opakowania") or not row.get("ilosc"):
        return None
    return {
        "package": {
            "type":     row["typ_opakowania"],
            "quantity": int(row["ilosc"]),
        },
        "dimensions": {
            "length": float(row["dlugosc_cm"] or 0),
            "width":  float(row["szerokosc_cm"] or 0),
            "height": float(row["wysokosc_cm"] or 0),
            "weight": float(row["waga_kg_max"] or 0),
        },
    }


def _delivery_date(row: dict) -> Optional[str]:
    """Konwertuje datę ERP na ISO 8601."""
    val = row.get("data_realizacji_zs")
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def rows_to_shipment(rows: list[dict]) -> Optional[dict]:
    """
    Konwertuje listę wierszy wz_jas_export (ten sam wz_id) → CreateShipmentRequest.
    Zwraca None gdy brak jakichkolwiek pozycji cargo.
    """
    if not rows:
        return None

    base = rows[0]
    cargo_items = [c for r in rows if (c := _cargo_item(r)) is not None]
    if not cargo_items:
        return None

    delivery = _delivery_place(base)
    return {
        "shipment": {
            "loadingPlace":  _loading_place(),
            "deliveryPlace": delivery,
            "recipient":     delivery,
            "customerRefNo": base.get("numer_wz") or "",
            "goodsName":     os.getenv("JAS_GOODS_NAME", ""),
            "deliveryDate":  _delivery_date(base),
            "remarks":       base.get("opis") or None,
        },
        "cargo":              cargo_items,
        "additionalServices": [],
    }
