"""KSeF Demo smoke — real HTTP call do api-demo.ksef.mf.gov.pl.

Skipped gdy brak KSEF_TOKEN w env (lokalny CI bez sekretów).
Uruchomienie: `pytest -m integration tests/integration/test_ksef_demo_smoke.py -v`.
"""
from __future__ import annotations

import os

import pytest

from core.ksef.adapters.http import KSefHttp
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
from core.ksef.config import load_config

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def cfg():
    if not os.getenv("KSEF_TOKEN"):
        pytest.skip("KSEF_TOKEN missing — integration smoke skipped")
    return load_config()


def test_ksef_demo_auth_roundtrip(cfg):
    """Full happy path: certs → authenticate → ensure_valid → logout."""
    http = KSefHttp(base_url=cfg.base_url)
    try:
        api = KSeFApiClient(http)
        auth = KSefAuth(api, EnvTokenProvider(token=cfg.ksef_token, nip=cfg.nip))

        certs = api.get_public_key_certificates()
        assert any("KsefTokenEncryption" in c.usage for c in certs), (
            "KsefTokenEncryption cert not present in Demo"
        )

        access = auth.authenticate()
        assert access.token

        access2 = auth.ensure_valid()
        assert access2.token == access.token  # fresh, no refresh

        auth.logout()
        assert auth.current_access_token is None
    finally:
        http.close()
