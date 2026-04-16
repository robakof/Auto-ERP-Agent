"""Integration tests — Prod safety guard in load_config."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.ksef.config import load_config


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate: clear KSEF_* env vars and return path to a writable .env."""
    for key in list(os.environ):
        if key.startswith("KSEF_"):
            monkeypatch.delenv(key, raising=False)
    return tmp_path / ".env"


def _write_env(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_prod_without_confirmed_raises(env_file: Path) -> None:
    _write_env(env_file, [
        "KSEF_ENV=prod",
        "KSEF_BASE_URL=https://api.ksef.mf.gov.pl",
        "KSEF_NIP=7871003063",
    ])
    with pytest.raises(ValueError, match="KSEF_PROD_CONFIRMED=yes"):
        load_config(dotenv_path=env_file)


def test_prod_with_confirmed_no_raises_base_url(env_file: Path) -> None:
    _write_env(env_file, [
        "KSEF_ENV=prod",
        "KSEF_PROD_CONFIRMED=yes",
        "KSEF_BASE_URL=https://api.ksef.mf.gov.pl",
        "KSEF_NIP=7871003063",
    ])
    cfg = load_config(dotenv_path=env_file)
    assert cfg.env == "prod"
    assert cfg.base_url == "https://api.ksef.mf.gov.pl"


def test_prod_with_confirmed_wrong_value_raises(env_file: Path) -> None:
    _write_env(env_file, [
        "KSEF_ENV=prod",
        "KSEF_PROD_CONFIRMED=true",  # not "yes"
        "KSEF_BASE_URL=https://api.ksef.mf.gov.pl",
        "KSEF_NIP=7871003063",
    ])
    with pytest.raises(ValueError, match="KSEF_PROD_CONFIRMED=yes"):
        load_config(dotenv_path=env_file)


def test_demo_no_confirmation_needed(env_file: Path) -> None:
    _write_env(env_file, [
        "KSEF_ENV=demo",
        "KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl",
        "KSEF_NIP=7871003063",
    ])
    cfg = load_config(dotenv_path=env_file)
    assert cfg.env == "demo"
    assert cfg.is_demo is True


def test_test_env_no_confirmation_needed(env_file: Path) -> None:
    _write_env(env_file, [
        "KSEF_ENV=test",
        "KSEF_BASE_URL=https://api-test.ksef.mf.gov.pl",
        "KSEF_NIP=7871003063",
    ])
    cfg = load_config(dotenv_path=env_file)
    assert cfg.env == "test"
