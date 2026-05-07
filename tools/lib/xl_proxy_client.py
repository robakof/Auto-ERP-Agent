"""XlProxyClient — zarządza subprocess XlProxy.exe (x86, JSON stdin/stdout)."""

import json
import subprocess
import sys
import threading
from pathlib import Path

def _resolve_proxy_exe(dll_dir: str) -> Path:
    """Wybierz exe proxy na podstawie wersji XL (2023 vs 2025)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    if "2023" in dll_dir:
        return base / "xl_proxy_2023" / "XlProxy.exe"
    return base / "xl_proxy" / "XlProxy.exe"


class XlProxyError(RuntimeError):
    pass


class XlProxyClient:
    def __init__(self, dll_dir: str):
        self._dll_dir = dll_dir
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        proxy_exe = _resolve_proxy_exe(self._dll_dir)
        if not proxy_exe.exists():
            raise XlProxyError(f"XlProxy.exe nie znaleziony: {proxy_exe}")
        self._proc = subprocess.Popen(
            [str(proxy_exe), self._dll_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        ready = self._readline()
        if not ready.get("ok"):
            self.stop()
            raise XlProxyError(f"XlProxy start failed: {ready}")

    def send(self, cmd: dict) -> dict:
        with self._lock:
            if self._proc is None:
                raise XlProxyError("XlProxy nie uruchomiony")
            line = json.dumps(cmd, ensure_ascii=False) + "\n"
            self._proc.stdin.write(line)
            self._proc.stdin.flush()
            return self._readline()

    def stop(self) -> None:
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            self._proc = None

    def _readline(self, timeout: float = 30.0) -> dict:
        bucket: list = []

        def _read():
            try:
                raw = self._proc.stdout.readline()
                bucket.append(("ok", json.loads(raw)) if raw
                              else ("err", "XlProxy zamknął stdout nieoczekiwanie"))
            except Exception as exc:
                bucket.append(("err", str(exc)))

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            self.stop()
            raise XlProxyError(
                f"XlProxy timeout ({timeout}s) — upewnij się że Comarch ERP XL jest zamknięty"
            )
        tag, val = bucket[0]
        if tag == "err":
            raise XlProxyError(val)
        return val
