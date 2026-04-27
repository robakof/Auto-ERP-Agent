"""XlProxyClient — zarządza subprocess XlProxy.exe (x86, JSON stdin/stdout)."""

import json
import subprocess
import threading
from pathlib import Path

_PROXY_EXE = Path(__file__).parent.parent / "xl_proxy" / "XlProxy.exe"


class XlProxyError(RuntimeError):
    pass


class XlProxyClient:
    def __init__(self, dll_dir: str):
        self._dll_dir = dll_dir
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if not _PROXY_EXE.exists():
            raise XlProxyError(f"XlProxy.exe nie znaleziony: {_PROXY_EXE}")
        self._proc = subprocess.Popen(
            [str(_PROXY_EXE), self._dll_dir],
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

    def _readline(self) -> dict:
        raw = self._proc.stdout.readline()
        if not raw:
            raise XlProxyError("XlProxy zamknął stdout nieoczekiwanie")
        return json.loads(raw)
