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


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    use_ssl: bool
    report_from: str
    report_to: str
    subject_prefix: str


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

    if env == "prod":
        confirmed = (os.getenv("KSEF_PROD_CONFIRMED") or "").strip().lower()
        if confirmed != "yes":
            raise ValueError(
                "KSEF_ENV=prod requires KSEF_PROD_CONFIRMED=yes in .env. "
                "This is a safety measure to prevent accidental production sends."
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


def load_smtp_config(dotenv_path: Path | None = None) -> SmtpConfig:
    """Load SMTP config from .env. All KSEF_SMTP_* keys required."""
    if dotenv_path is not None:
        load_dotenv(dotenv_path, override=False)
    else:
        load_dotenv(override=False)

    host = (os.getenv("KSEF_SMTP_HOST") or "").strip()
    if not host:
        raise ValueError("KSEF_SMTP_HOST is required")

    port = int(os.getenv("KSEF_SMTP_PORT") or "465")

    user = (os.getenv("KSEF_SMTP_USER") or "").strip()
    if not user:
        raise ValueError("KSEF_SMTP_USER is required")

    password = os.getenv("KSEF_SMTP_PASS") or ""
    if not password:
        raise ValueError("KSEF_SMTP_PASS is required")

    use_ssl = (os.getenv("KSEF_SMTP_SSL") or "true").strip().lower() == "true"

    report_from = (os.getenv("KSEF_REPORT_FROM") or user).strip()
    report_to = (os.getenv("KSEF_REPORT_TO") or "").strip()
    if not report_to:
        raise ValueError("KSEF_REPORT_TO is required")

    subject_prefix = (os.getenv("KSEF_REPORT_SUBJECT_PREFIX") or "[KSeF]").strip()

    return SmtpConfig(
        host=host, port=port, user=user, password=password,
        use_ssl=use_ssl, report_from=report_from, report_to=report_to,
        subject_prefix=subject_prefix,
    )
