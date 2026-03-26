"""
jas_mapper.py — Mapowanie wierszy AILO.wz_jas_export → CreateShipmentRequest.

Jeden WZ (wz_id) = wiele wierszy (jeden per typ palety) → jeden shipment z listą cargo[].
Wiersze z typ_opakowania = NULL (brak WMS) → pomijane w cargo.
"""

import datetime
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

# Mapowanie typów opakowań ERP → JAS API
_PACKAGE_TYPE_MAP = {
    "Paleta":      "EFN",  # paleta zwykła/jednorazowa (120×80, nie EPAL)
    "Paleta-EPAL": "EPN",  # paleta EPAL (120×80)
    "Paleta-INNA": "PPN",  # paleta inna (wymiary inne niż 120×80)
}

_EMPTY_NOTIFICATIONS = {"data": {"email": "", "text": ""}, "enabled": False}
_EMPTY_PAYER = {"vatNumber": "", "contractType": "B2C", "isVatPayer": False}
_EMPTY_COD = {
    "value": 0,
    "type": "Contractor",
    "naturalPersonEmailAddress": "",
    "bank": {"accountNo": ""},
    "thirdParty": {"name": "", "vatNo": ""},
}


def _address(name: str, street: str, house_no: str, city: str,
             zip_code: str, country: str) -> dict:
    return {
        "name":          name,
        "street":        street,
        "houseNo":       house_no,
        "flatNo":        "",
        "city":          city,
        "zipCode":       zip_code,
        "country":       country,
        "contact":       "",
        "notifications": _EMPTY_NOTIFICATIONS,
        "payer":         _EMPTY_PAYER,
    }


def _loading_place() -> dict:
    return {"address": _address(
        name=      os.getenv("JAS_LOADING_NAME", ""),
        street=    os.getenv("JAS_LOADING_STREET", ""),
        house_no=  os.getenv("JAS_LOADING_HOUSE_NO", ""),
        city=      os.getenv("JAS_LOADING_CITY", ""),
        zip_code=  os.getenv("JAS_LOADING_ZIP", ""),
        country=   os.getenv("JAS_LOADING_COUNTRY", "PL"),
    )}


def _delivery_place(row: dict) -> dict:
    return {"address": _address(
        name=      row.get("odbiorca_nazwa") or "",
        street=    row.get("odbiorca_ulica") or "",
        house_no=  row.get("odbiorca_nr_domu") or "",
        city=      row.get("odbiorca_miasto") or "",
        zip_code=  row.get("odbiorca_kod_pocztowy") or "",
        country=   row.get("odbiorca_kraj") or "PL",
    )}


def _map_package_type(erp_type: str) -> str:
    return _PACKAGE_TYPE_MAP.get(erp_type, erp_type)


def _cargo_item(row: dict) -> Optional[dict]:
    """Zwraca cargo dict lub None gdy brak danych WMS."""
    if not row.get("typ_opakowania") or not row.get("ilosc"):
        return None
    return {
        "barcode": "12",
        "sscc":    "12",
        "package": {
            "type":     _map_package_type(row["typ_opakowania"]),
            "quantity": int(row["ilosc"]),
        },
        "dimensions": {
            "length": float(row["dlugosc_cm"] or 0),
            "width":  float(row["szerokosc_cm"] or 0),
            "height": float(row["wysokosc_cm"] or 0),
            "weight": float(row["waga_kg_max"] or 0),
        },
        "dangerousGoods": [],
    }


def _delivery_date(row: dict) -> Optional[str]:
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
        "request": {
            "shipment": {
                "goodsName":          os.getenv("JAS_GOODS_NAME", ""),
                "declaredValue":      0,
                "returnablePackaging": False,
                "customerRefNo":      base.get("numer_wz") or "",
                "remarks":            base.get("opis") or "",
                "loadingPlace":       _loading_place(),
                "deliveryPlace":      delivery,
                "recipient":          delivery,
                "pickupDate":         datetime.date.today().isoformat(),
                "deliveryDate":       _delivery_date(base),
                "notifications":      _EMPTY_NOTIFICATIONS,
                "cod":                _EMPTY_COD,
            },
            "documents":          [],
            "cargo":              cargo_items,
            "additionalServices": [],
        }
    }
