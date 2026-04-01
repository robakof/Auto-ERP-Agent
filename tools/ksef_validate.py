"""Walidacja XML KSeF względem XSD."""
import sys
import argparse
from pathlib import Path
from lxml import etree

XSD_PATH = Path(__file__).parent.parent / "output" / "StrukturyDanych_v10-0E.xsd"
XML_PATH_DEFAULT = Path(__file__).parent.parent / "output" / "ksef" / "ksef_FRA_267_2026-03-31.xml"

def main():
    parser = argparse.ArgumentParser(description="Walidacja XML KSeF względem XSD FA(3).")
    parser.add_argument("xml", nargs="?", default=str(XML_PATH_DEFAULT), help="Ścieżka do pliku XML")
    parser.add_argument("--xsd", default=str(XSD_PATH), help="Ścieżka do pliku XSD")
    args = parser.parse_args()

    xsd_path = Path(args.xsd)
    xml_path = Path(args.xml)

    print(f"XSD: {xsd_path}")
    print(f"XML: {xml_path}")

    with open(xsd_path, "rb") as f:
        schema_doc = etree.parse(f)

    try:
        schema = etree.XMLSchema(schema_doc)
    except etree.XMLSchemaParseError as e:
        print(f"\nBłąd parsowania XSD (może wymagać zdalnego importu):\n{e}")
        sys.exit(1)

    with open(xml_path, "rb") as f:
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
