"""
Walidacja XML KSeF względem XSD.

CLI:
    py tools/ksef_validate.py sciezka/schemat.xsd sciezka/do/pliku.xml
    py tools/ksef_validate.py sciezka/schemat.xsd output/ksef/ksef_*.xml
"""
import argparse
import sys
from pathlib import Path
from lxml import etree


def validate(xml_path, schema):
    with open(xml_path, "rb") as f:
        doc = etree.parse(f)

    if schema.validate(doc):
        return True, []

    return False, [
        f"Linia {err.line}: {err.message}" for err in schema.error_log
    ]


def main():
    p = argparse.ArgumentParser(description="Walidacja XML KSeF vs XSD")
    p.add_argument("xsd", help="Sciezka do pliku XSD")
    p.add_argument("xml", nargs="+", help="Sciezka do pliku(ow) XML")
    args = p.parse_args()

    xsd_path = Path(args.xsd)
    if not xsd_path.exists():
        print(f"XSD nie istnieje: {xsd_path}")
        sys.exit(1)

    with open(xsd_path, "rb") as f:
        try:
            schema = etree.XMLSchema(etree.parse(f))
        except etree.XMLSchemaParseError as e:
            print(f"Blad parsowania XSD:\n{e}")
            sys.exit(1)

    ok_count = 0
    fail_count = 0

    for xml_arg in args.xml:
        xml_path = Path(xml_arg)
        if not xml_path.exists():
            print(f"  [!] Plik nie istnieje: {xml_path}")
            fail_count += 1
            continue

        valid, errors = validate(xml_path, schema)
        if valid:
            print(f"  [OK] {xml_path.name}")
            ok_count += 1
        else:
            print(f"  [FAIL] {xml_path.name} — {len(errors)} bledow:")
            for err in errors[:10]:
                print(f"    {err}")
            fail_count += 1

    print(f"\nWynik: {ok_count} OK, {fail_count} FAIL")
    sys.exit(0 if fail_count == 0 else 2)


if __name__ == "__main__":
    main()
