"""xl_session — singleton sesji XL API (login/logout, lazy init z .env)."""

import os
import threading
from pathlib import Path

from dotenv import load_dotenv

from tools.lib.xl_proxy_client import XlProxyClient, XlProxyError

load_dotenv()

_lock = threading.Lock()
_client: XlProxyClient | None = None
_sesja_id: int = 0

_DEFAULTS = {
    "XL_DLL_DIR":       r"C:\Comarch ERP\Comarch ERP XL 2025.1",
    "XL_BAZA":          "",
    "XL_LOGIN":         "",
    "XL_PASSWORD":      "",
    "XL_SERWER":        "",
    "XL_TRYB_WSADOWY":  "0",
}


def _env(key: str) -> str:
    return os.environ.get(key, _DEFAULTS.get(key, ""))


def get() -> tuple[XlProxyClient, int]:
    """Zwraca (client, sesja_id) — lazy init przy pierwszym wywołaniu."""
    global _client, _sesja_id
    with _lock:
        if _client is None:
            _client, _sesja_id = _login()
        return _client, _sesja_id


def logout() -> None:
    """Wylogowanie i zatrzymanie proxy."""
    global _client, _sesja_id
    with _lock:
        if _client:
            try:
                _client.send({"cmd": "logout", "sesja_id": _sesja_id})
            finally:
                _client.stop()
                _client = None
                _sesja_id = 0


def _login() -> tuple[XlProxyClient, int]:
    client = XlProxyClient(_env("XL_DLL_DIR"))
    client.start()
    result = client.send({
        "cmd":           "login",
        "baza":          _env("XL_BAZA"),
        "oper":          _env("XL_LOGIN"),
        "haslo":         _env("XL_PASSWORD"),
        "serwer":        _env("XL_SERWER"),
        "tryb_wsadowy":  _env("XL_TRYB_WSADOWY"),
    })
    if not result.get("ok"):
        client.stop()
        raise XlProxyError(f"XL login failed: {result}")
    return client, result["sesja_id"]
