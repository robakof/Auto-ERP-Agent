"""Generuje KSeF FA(3) KOR XML dla korekt rabatowych (skonto + rabat transakcyjny).

Unified generator — obsługuje oba typy:
  - Skonto (TrN_ZwrNumer = 0)
  - Rabat transakcyjny (TrN_ZwrNumer = TrN_GIDNumer)

CLI:
    py tools/ksef_generate_rabat.py --gid 1
    py tools/ksef_generate_rabat.py --gid 1 2
    py tools/ksef_generate_rabat.py --date-from 2026-04-01 --date-to 2026-04-28
    py tools/ksef_generate_rabat.py --validate output/schemat_FA3.xsd --gid 1
    py tools/ksef_generate_rabat.py --dry-run --gid 1

Thin wrapper nad core/ksef/ (adapters: erp_reader, xml_builder, xsd_validator).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef import paths as ksef_paths
from core.ksef.adapters import xsd_validator
from core.ksef.adapters.erp_reader import ErpReader, SQL_PATH_FSK_RABAT
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
        sql = SQL_PATH_FSK_RABAT.read_text(encoding="utf-8")
        print(sql)
        return 0

    from sql_query import run_query  # noqa: PLC0415 — DI
    reader = ErpReader(run_query=lambda sql: run_query(sql, inject_top=None))
    korekty = reader.fetch_korekty_rabat(
        gids=args.gid, date_from=args.date_from, date_to=args.date_to or args.date_from,
    )
    if not korekty:
        print("Brak korekt rabatowych dla podanych kryteriow.")
        return 0

    out_dir = Path(args.output_dir) if args.output_dir else ksef_paths.output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    builder = XmlBuilder()
    xsd_path = Path(args.validate) if args.validate else None

    errors: list[tuple[str, list[str]]] = []
    for k in korekty:
        xml = builder.build_korekta_rabatowa(k)
        out_path = out_dir / _compose_filename(k.numer_faktury, k.data_wystawienia)
        out_path.write_bytes(xml)
        n_fa = len(k.dane_fa_korygowanych)
        print(f"  [OK] {k.numer_faktury} ({n_fa} faktur korygowanych) -> {out_path.name}")
        if xsd_path:
            _validate_and_report(xml, xsd_path, k.numer_faktury, out_path.name, errors)

    print(f"\nWygenerowano {len(korekty)} korekt(y) rabatowych w {out_dir}")
    return 2 if errors else 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generuj KSeF FA(3) KOR XML z ERP XL (korekty rabatowe)")
    p.add_argument("--gid", type=int, nargs="+", help="GID_NUMER korekt(y)")
    p.add_argument("--date-from", dest="date_from", help="Data wystawienia od (YYYY-MM-DD)")
    p.add_argument("--date-to", dest="date_to",
                   help="Data wystawienia do (YYYY-MM-DD, domyslnie=date-from)")
    p.add_argument("--validate", metavar="XSD_PATH", help="Sciezka do pliku XSD do walidacji")
    p.add_argument("--dry-run", action="store_true", help="Pokaz SQL bez wykonania")
    p.add_argument("--output-dir", dest="output_dir", metavar="KATALOG",
                   help="Katalog wyjsciowy (domyslnie: output/ksef)")
    return p.parse_args()


def _compose_filename(numer: str, data) -> str:
    safe = numer.replace("/", "_")
    return f"ksef_rabat_{safe}_{data.isoformat()}.xml"


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
