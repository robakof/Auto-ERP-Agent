"""Integration test — real send to KSeF Demo.

Requires KSEF_TOKEN, KSEF_NIP, KSEF_BASE_URL, KSEF_ENV in environment.
Run manually: py -m pytest tests/ksef/test_send_integration.py -v -m integration
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

_SKIP_REASON = "KSEF_TOKEN not set — skipping real API test"
_HAS_TOKEN = bool(os.getenv("KSEF_TOKEN"))


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_TOKEN, reason=_SKIP_REASON)
def test_send_real_fs_to_demo(tmp_path: Path) -> None:
    """Send FS-59 XML to api-demo.ksef.mf.gov.pl, verify ACCEPTED + UPO."""
    from core.ksef.adapters.encryption import KSeFEncryption
    from core.ksef.adapters.http import KSeFHttp
    from core.ksef.adapters.ksef_api import KSeFApiClient
    from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
    from core.ksef.adapters.repo import ShipmentRepository
    from core.ksef.config import load_config
    from core.ksef.domain.shipment import ShipmentStatus
    from core.ksef.usecases.send_invoice import SendInvoiceUseCase

    cfg = load_config()
    http = KSeFHttp(base_url=cfg.base_url)
    api = KSeFApiClient(http)
    provider = EnvTokenProvider(token=cfg.ksef_token or "", nip=cfg.nip)
    auth = KSefAuth(api, provider)

    certs = api.get_public_key_certificates()
    sym_cert = next(c for c in certs if "SymmetricKeyEncryption" in c.usage)
    encryption = KSeFEncryption(sym_cert.certificate_b64)

    db_path = tmp_path / "ksef_test.db"
    repo = ShipmentRepository(db_path)
    repo.init_schema()

    upo_dir = tmp_path / "upo"
    uc = SendInvoiceUseCase(
        api=api, auth=auth, repo=repo, encryption=encryption,
        upo_dir=upo_dir, poll_timeout_s=120.0,
    )

    xml_dir = Path(__file__).resolve().parents[2] / "output" / "ksef"
    candidates = list(xml_dir.glob("ksef_FS-59_*.xml"))
    assert candidates, f"No FS-59 XML found in {xml_dir}"
    xml_path = candidates[0]

    from datetime import date
    from lxml import etree

    tree = etree.parse(str(xml_path))
    ns = {"f": tree.getroot().nsmap.get(None, "")}
    p2 = tree.find(".//f:Fa/f:P_2", ns)
    p1 = tree.find(".//f:Fa/f:P_1", ns)
    nr = p2.text if p2 is not None else "FS-59"
    data_wyst = date.fromisoformat(p1.text) if p1 is not None and p1.text else date.today()

    result = uc.execute(xml_path, gid=59, rodzaj="FS", nr_faktury=nr, data_wystawienia=data_wyst)

    assert result.status == ShipmentStatus.ACCEPTED, f"Expected ACCEPTED, got {result.status}"
    assert result.ksef_number is not None
    assert result.upo_path is not None
    assert result.upo_path.exists()
    print(f"\nKSeF number: {result.ksef_number}")
    print(f"UPO path: {result.upo_path}")
