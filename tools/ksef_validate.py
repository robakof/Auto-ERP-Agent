"""Walidacja XML KSeF względem XSD."""
import sys
from pathlib import Path
from lxml import etree

XSD_PATH = Path(__file__).parent.parent / "output" / "schemat.xsd"
XML_PATH = Path(__file__).parent.parent / "output" / "ksef" / "ksef_FRA_267_2026-03-31.xml"

def main():
    print(f"XSD: {XSD_PATH}")
    print(f"XML: {XML_PATH}")

    with open(XSD_PATH, "rb") as f:
        schema_doc = etree.parse(f)

    try:
        schema = etree.XMLSchema(schema_doc)
    except etree.XMLSchemaParseError as e:
        print(f"\nBłąd parsowania XSD (może wymagać zdalnego importu):\n{e}")
        sys.exit(1)

    with open(XML_PATH, "rb") as f:
        xml_doc = etree.parse(f)

    valid = schema.validate(xml_doc)

    if valid:
        print("\nOK XML PRAWIDLOWY — brak bledow walidacji.")
    else:
        print(f"\nBLAD XML NIEPRAWIDLOWY — {len(schema.error_log)} bledow:\n")
        for i, err in enumerate(schema.error_log, 1):
            print(f"  [{i}] Linia {err.line}: {err.message}")

if __name__ == "__main__":
    main()
