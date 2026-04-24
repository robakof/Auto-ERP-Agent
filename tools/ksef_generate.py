"""Generuje KSeF FA(3) XML dla faktur sprzedazy (FS) z ERP XL.

CLI:
    py tools/ksef_generate.py --gid 59
    py tools/ksef_generate.py --gid 59 60
    py tools/ksef_generate.py --date-from 2026-04-01 --date-to 2026-04-14
    py tools/ksef_generate.py --validate output/schemat.xsd --gid 59
    py tools/ksef_generate.py --dry-run --gid 59

Thin wrapper nad core/ksef/ (adapters: erp_reader, xml_builder, xsd_validator).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef import paths as ksef_paths
from core.ksef.adapters import xsd_validator
from core.ksef.adapters.erp_reader import ErpReader, build_sql_fs
from core.ksef.adapters.xml_builder import XmlBuilder


def _utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def main() -> int:
    _utf8_stdout()
    args = _parse_args()
    if not args.gid and not args.date_from:
        print("Podaj --gid N lub --date-from YYYY-MM-DD")
        return 1

    if args.dry_run:
        print(_build_sql_preview(args))
        return 0

    from sql_query import run_query  # noqa: PLC0415 — DI nie dopuszcza core→tools
    reader = ErpReader(run_query=lambda sql: run_query(sql, inject_top=None))
    faktury = reader.fetch_faktury(
        gids=args.gid, date_from=args.date_from, date_to=args.date_to or args.date_from,
    )
    if not faktury:
        print("Brak faktur dla podanych kryteriow.")
        return 0

    out_dir = Path(args.output_dir) if args.output_dir else ksef_paths.output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    builder = XmlBuilder()
    xsd_path = Path(args.validate) if args.validate else None

    errors: list[tuple[str, list[str]]] = []
    for f in faktury:
        xml = builder.build_faktura(f)
        out_path = out_dir / _compose_filename("ksef", f.numer_faktury, f.data_wystawienia)
        out_path.write_bytes(xml)
        print(f"  [OK] {f.numer_faktury} ({len(f.wiersze)} poz.) -> {out_path.name}")
        if xsd_path:
            _validate_and_report(xml, xsd_path, f.numer_faktury, out_path.name, errors)

    print(f"\nWygenerowano {len(faktury)} faktur(y) w {out_dir}")
    return 2 if errors else 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generuj KSeF FA(3) XML z ERP XL (FS)")
    p.add_argument("--gid", type=int, nargs="+", help="GID_NUMER faktur(y)")
    p.add_argument("--date-from", dest="date_from", help="Data wystawienia od (YYYY-MM-DD)")
    p.add_argument("--date-to", dest="date_to",
                   help="Data wystawienia do (YYYY-MM-DD, domyslnie=date-from)")
    p.add_argument("--validate", metavar="XSD_PATH", help="Sciezka do pliku XSD do walidacji")
    p.add_argument("--dry-run", action="store_true", help="Pokaz SQL bez wykonania")
    p.add_argument("--output-dir", dest="output_dir", metavar="KATALOG",
                   help="Katalog wyjsciowy (domyslnie: output/ksef)")
    return p.parse_args()


def _build_sql_preview(args: argparse.Namespace) -> str:
    return build_sql_fs(
        gids=args.gid, date_from=args.date_from,
        date_to=args.date_to or args.date_from,
    )


def _compose_filename(prefix: str, numer: str, data) -> str:
    safe = numer.replace("/", "_")
    return f"{prefix}_{safe}_{data.isoformat()}.xml"


def _validate_and_report(xml: bytes, xsd: Path, numer: str, fname: str,
                         errors: list[tuple[str, list[str]]]) -> None:
    if not xsd.exists():
        print(f"  [!] XSD nie istnieje: {xsd}")
        return
    valid, errs = xsd_validator.validate(xml, xsd)
    if valid:
        print(f"  [XSD OK] {fname}")
        return
    print(f"  [XSD FAIL] {fname} - {len(errs)} bledow:")
    for e in errs[:5]:
        print(f"    {e}")
    errors.append((numer, errs))


if __name__ == "__main__":
    raise SystemExit(main())
