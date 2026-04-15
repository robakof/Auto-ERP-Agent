"""KSeF smoke test CLI — Block 1.

Uruchamia prawdziwy flow uwierzytelnienia na środowisku Demo (lub wskazanym
w .env), używając długożywotnego KSEF_TOKEN. Drukuje kolejne kroki i kończy
się `logout`. Nie wysyła żadnej faktury — weryfikuje wyłącznie łączność i auth.

Użycie:
    py tools/ksef_smoke.py                 # pełny flow + logout
    py tools/ksef_smoke.py --no-logout     # zostaw sesję otwartą

Wymagane w .env: KSEF_ENV, KSEF_BASE_URL, KSEF_TOKEN, KSEF_NIP.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.http import KSefHttp
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
from core.ksef.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="KSeF smoke test — auth flow only")
    parser.add_argument("--no-logout", action="store_true", help="nie wylogowuj po sukcesie")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    cfg = load_config()
    if not cfg.ksef_token:
        print("ERROR: KSEF_TOKEN wymagany w .env", file=sys.stderr)
        return 2

    print(f"[1/5] Konfiguracja: env={cfg.env} base_url={cfg.base_url} nip={cfg.nip}")

    http = KSefHttp(base_url=cfg.base_url)
    try:
        api = KSeFApiClient(http)
        auth = KSefAuth(api, EnvTokenProvider(token=cfg.ksef_token, nip=cfg.nip))

        print("[2/5] Pobieram klucze publiczne...")
        certs = api.get_public_key_certificates()
        print(f"      -> {len(certs)} certyfikatów: {[c.usage for c in certs]}")

        print("[3/5] Uwierzytelnianie (challenge -> encrypt -> poll -> redeem)...")
        access = auth.authenticate()
        print(f"      -> access_token=...{access.token[-6:]} valid_until={access.valid_until.isoformat()}")

        print("[4/5] ensure_valid() (no-op gdy token świeży)...")
        access2 = auth.ensure_valid()
        print(f"      -> token_tail=...{access2.token[-6:]}")

        if args.no_logout:
            print("[5/5] Pomijam logout (--no-logout)")
        else:
            print("[5/5] Logout...")
            auth.logout()
            print("      -> OK")

        print("\nSMOKE OK")
        return 0
    except Exception as exc:
        print(f"\nSMOKE FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        http.close()


if __name__ == "__main__":
    raise SystemExit(main())
