"""Walidacja XML przeciw XSD — funkcja modulowa (bezstanowa).

Uzycie:
    valid, errors = validate(xml_bytes, Path("schemat.xsd"))
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree


def validate(xml_bytes: bytes, xsd_path: Path) -> tuple[bool, list[str]]:
    """Zwraca (valid, errors). Error format: 'Linia N: message'."""
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD nie istnieje: {xsd_path}")

    schema = etree.XMLSchema(etree.parse(str(xsd_path)))
    doc = etree.fromstring(xml_bytes)
    if schema.validate(doc):
        return True, []

    errors = [f"Linia {e.line}: {e.message}" for e in schema.error_log]
    return False, errors
