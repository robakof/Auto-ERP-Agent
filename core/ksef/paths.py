"""KSeF environment-aware path resolver.

All runtime paths (DB, output, logs) live under ksef_api/<env>/.
Env is read from KSEF_ENV (default: demo).
"""
from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_KSEF_API_ROOT = _PROJECT_ROOT / "ksef_api"


def env_root(env: str | None = None) -> Path:
    if env is None:
        env = (os.getenv("KSEF_ENV") or "demo").strip().lower()
    return _KSEF_API_ROOT / env


def db_path(env: str | None = None) -> Path:
    return env_root(env) / "data" / "ksef.db"


def output_dir(env: str | None = None) -> Path:
    return env_root(env) / "output"


def upo_dir(env: str | None = None) -> Path:
    return output_dir(env) / "upo"


def daemon_log(env: str | None = None) -> Path:
    return env_root(env) / "data" / "ksef_daemon.log"


def watchdog_log(env: str | None = None) -> Path:
    return env_root(env) / "data" / "ksef_watchdog.log"


def heartbeat_path(env: str | None = None) -> Path:
    return env_root(env) / "data" / "ksef_heartbeat.json"
