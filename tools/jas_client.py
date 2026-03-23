"""
jas_client.py — Klient HTTP dla JAS FBG API (OAuth2 + REST).

Autentykacja: OAuth2 Resource Owner Password (grant_type=password).
Token jest cache'owany do wygaśnięcia (expires_in z odpowiedzi).

Użycie:
    client = JasClient()
    result = client.create_shipment(payload)
"""

import os
import time
import sys
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()


class JasAuthError(Exception):
    pass


class JasApiError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")


class JasClient:
    def __init__(self):
        self._auth_url   = os.getenv("JAS_AUTH_URL", "")
        self._api_url    = os.getenv("JAS_API_URL", "").rstrip("/")
        self._client_id  = os.getenv("JAS_CLIENT_ID", "")
        self._client_secret = os.getenv("JAS_CLIENT_SECRET", "")
        self._username   = os.getenv("JAS_USERNAME", "")
        self._password   = os.getenv("JAS_PASSWORD", "")
        self._scope      = os.getenv("JAS_SCOPE", "extranet_modules_access")
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _is_token_valid(self) -> bool:
        return self._token is not None and time.time() < self._token_expires_at - 30

    def authenticate(self) -> str:
        """Pobiera token OAuth2. Zwraca access_token."""
        resp = requests.post(self._auth_url, data={
            "grant_type":    "password",
            "client_id":     self._client_id,
            "client_secret": self._client_secret,
            "username":      self._username,
            "password":      self._password,
            "scope":         self._scope,
        }, timeout=15)
        if not resp.ok:
            raise JasAuthError(f"Auth failed {resp.status_code}: {resp.text}")
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._token

    def _token_header(self) -> dict:
        if not self._is_token_valid():
            self.authenticate()
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Endpointy
    # ------------------------------------------------------------------

    def create_shipment(self, payload: dict) -> dict:
        """POST /domestic-groupage-shipment/create. Zwraca odpowiedź JSON."""
        url = f"{self._api_url}/domestic-groupage-shipment/create"
        resp = requests.post(url, json=payload,
                             headers=self._token_header(), timeout=30)
        if not resp.ok:
            raise JasApiError(resp.status_code, resp.text)
        return resp.json()

    def get_shipment(self, shipment_id: int) -> dict:
        """GET /domestic-groupage-shipment/{id}. Zwraca dane zlecenia."""
        url = f"{self._api_url}/domestic-groupage-shipment/{shipment_id}"
        resp = requests.get(url, headers=self._token_header(), timeout=15)
        if not resp.ok:
            raise JasApiError(resp.status_code, resp.text)
        return resp.json()
