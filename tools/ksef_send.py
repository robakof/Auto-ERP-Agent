"""Wysyla fakture XML na KSeF (Demo/Prod) — encrypt + session + send + poll + UPO.

CLI:
    py tools/ksef_send.py output/ksef/ksef_FS-59_04_26_SPKR_2026-04-14.xml
    py tools/ksef_send.py --dry-run output/ksef/ksef_FS-59_04_26_SPKR_2026-04-14.xml
    py tools/ksef_send.py --gid 59 --rodzaj FS output/ksef/ksef_FS-59_04_26_SPKR_2026-04-14.xml
    py tools/ksef_send.py --poll-timeout 180 output/ksef/*.xml

Parametry z .env: KSEF_ENV, KSEF_BASE_URL, KSEF_TOKEN, KSEF_NIP.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.encryption import KSeFEncryption
from core.ksef.adapters.http import KSefHttp
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.config import load_config
from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.usecases.send_invoice import SendInvoiceUseCase

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ksef.db"
_UPO_DIR = Path(__file__).resolve().parent.parent / "output" / "ksef" / "upo"

_FILENAME_FS = re.compile(r"ksef_FS-(\d+)_")
_FILENAME_FSK = re.compile(r"ksef_kor_FSK-(\d+)_")


def main() -> int:
    args = _parse_args()
    results = []
    for xml_path in args.xml_files:
        gid, rodzaj = _extract_gid_rodzaj(xml_path, args.gid, args.rodzaj)
        nr, data_wyst = _extract_from_xml(xml_path)
        if args.dry_run:
            print(f"[DRY-RUN] {xml_path.name}: GID={gid} rodzaj={rodzaj} nr={nr} data={data_wyst}")
            continue
        result = _send_one(xml_path, gid, rodzaj, nr, data_wyst, args.poll_timeout)
        results.append(result)
        _print_result(xml_path, result)

    if args.dry_run:
        return 0
    return 0 if all(r.status == ShipmentStatus.ACCEPTED for r in results) else 1


def _send_one(xml_path, gid, rodzaj, nr, data_wyst, poll_timeout):
    cfg = load_config()
    http = KSefHttp(base_url=cfg.base_url)
    api = KSeFApiClient(http)
    token_provider = EnvTokenProvider(token=cfg.ksef_token or "", nip=cfg.nip)
    auth = KSefAuth(api, token_provider)

    sym_cert = _get_sym_cert(api)
    encryption = KSeFEncryption(sym_cert)

    repo = ShipmentRepository(_DB_PATH)
    repo.init_schema()

    uc = SendInvoiceUseCase(
        api=api, auth=auth, repo=repo, encryption=encryption,
        poll_timeout_s=poll_timeout, upo_dir=_UPO_DIR,
    )
    return uc.execute(xml_path, gid, rodzaj, nr, data_wyst)


def _get_sym_cert(api: KSeFApiClient) -> str:
    certs = api.get_public_key_certificates()
    match = next((c for c in certs if "SymmetricKeyEncryption" in c.usage), None)
    if match is None:
        print("BLAD: Brak certyfikatu SymmetricKeyEncryption z KSeF")
        sys.exit(2)
    return match.certificate_b64


def _extract_gid_rodzaj(
    xml_path: Path, gid_override: int | None, rodzaj_override: str | None,
) -> tuple[int, str]:
    name = xml_path.name
    if gid_override and rodzaj_override:
        return gid_override, rodzaj_override

    m_fsk = _FILENAME_FSK.search(name)
    if m_fsk:
        return gid_override or int(m_fsk.group(1)), rodzaj_override or "FSK"
    m_fs = _FILENAME_FS.search(name)
    if m_fs:
        return gid_override or int(m_fs.group(1)), rodzaj_override or "FS"

    print(f"BLAD: Nie mozna wyciagnac GID/rodzaj z nazwy pliku: {name}")
    print("Uzyj --gid N --rodzaj FS|FSK")
    sys.exit(2)


def _extract_from_xml(xml_path: Path) -> tuple[str, date]:
    """Parse P_2 (numer) i P_1 (data wystawienia) z XML."""
    tree = etree.parse(str(xml_path))
    ns = {"f": tree.getroot().nsmap.get(None, "")}
    p2 = tree.find(".//f:Fa/f:P_2", ns)
    p1 = tree.find(".//f:Fa/f:P_1", ns)
    nr = p2.text if p2 is not None and p2.text else xml_path.stem
    data_str = p1.text if p1 is not None and p1.text else ""
    try:
        data_wyst = date.fromisoformat(data_str)
    except ValueError:
        data_wyst = date.today()
    return nr, data_wyst


def _print_result(xml_path, result) -> None:
    status_mark = "OK" if result.status == ShipmentStatus.ACCEPTED else "FAIL"
    print(f"[{status_mark}] {xml_path.name}")
    print(f"  Status:     {result.status.value}")
    print(f"  Wysylka ID: {result.wysylka_id}")
    if result.ksef_number:
        print(f"  KSeF nr:    {result.ksef_number}")
    if result.upo_path:
        print(f"  UPO:        {result.upo_path}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wyslij fakture XML na KSeF")
    p.add_argument("xml_files", nargs="+", type=Path, help="Pliki XML do wyslania")
    p.add_argument("--gid", type=int, default=None, help="GID ERP (override)")
    p.add_argument("--rodzaj", choices=["FS", "FSK"], default=None, help="Rodzaj dokumentu (override)")
    p.add_argument("--dry-run", action="store_true", help="Pokaz co bylby wyslane, bez wysylki")
    p.add_argument("--poll-timeout", type=float, default=120.0, help="Timeout pollingu statusu (s)")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(main())
