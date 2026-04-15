"""KSeF runtime configuration — loaded from .env at process start."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ALLOWED_ENVS = {"demo", "test", "prod"}


@dataclass(frozen=True)
class KSefConfig:
    env: str
    base_url: str
    nip: str
    ksef_token: str | None

    @property
    def is_demo(self) -> bool:
        return self.env == "demo"


def load_config(dotenv_path: Path | None = None) -> KSefConfig:
    """Load KSeF config from .env (or environment already set).

    Required keys: KSEF_ENV, KSEF_BASE_URL, KSEF_NIP. Optional: KSEF_TOKEN.
    """
    if dotenv_path is not None:
        load_dotenv(dotenv_path, override=False)
    else:
        load_dotenv(override=False)

    env = (os.getenv("KSEF_ENV") or "").strip().lower()
    if env not in ALLOWED_ENVS:
        raise ValueError(
            f"KSEF_ENV must be one of {sorted(ALLOWED_ENVS)}, got: {env!r}"
        )

    base_url = (os.getenv("KSEF_BASE_URL") or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("KSEF_BASE_URL is required")

    nip = (os.getenv("KSEF_NIP") or "").strip()
    if not nip:
        raise ValueError("KSEF_NIP is required (NIP kontekstu uwierzytelnienia)")

    return KSefConfig(
        env=env,
        base_url=base_url,
        nip=nip,
        ksef_token=(os.getenv("KSEF_TOKEN") or None),
    )
