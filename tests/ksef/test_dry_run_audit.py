"""Dry-run audit — verify --dry-run makes zero HTTP calls."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.usecases.scan_erp import PendingDocument
from tools.ksef_daemon import KSeFDaemon, _build_send_factory


_DOC = PendingDocument(
    gid=59, rodzaj="FS", nr_faktury="FS-59/04/26/SPKR",
    data_wystawienia=date(2026, 4, 14),
)


def test_dry_run_factory_makes_no_http_calls(tmp_path: Path) -> None:
    """--dry-run path must not instantiate KSefHttp or call httpx."""
    db_path = tmp_path / "ksef.db"
    repo = ShipmentRepository(db_path)
    repo.init_schema()

    def run_query(_sql: str) -> list[dict]:
        return []

    # If dry_run=True invoked any real adapters, these patches would be touched.
    with patch("core.ksef.adapters.http.httpx.Client") as http_mock, \
         patch("tools.ksef_daemon.KSefHttp") as http_cls_mock, \
         patch("tools.ksef_daemon.KSeFApiClient") as api_mock, \
         patch("tools.ksef_daemon.load_config") as cfg_mock:
        factory = _build_send_factory(run_query, repo, dry_run=True)
        result = factory(_DOC)

        http_mock.assert_not_called()
        http_cls_mock.assert_not_called()
        api_mock.assert_not_called()
        cfg_mock.assert_not_called()

    assert result.wysylka_id == 0
    assert result.ksef_number is None


def test_dry_run_daemon_run_once_makes_no_http_calls(tmp_path: Path) -> None:
    """Full daemon.run_once() with dry-run factory and fake scan — zero HTTP."""
    db_path = tmp_path / "ksef.db"
    repo = ShipmentRepository(db_path)
    repo.init_schema()

    def run_query(_sql: str) -> list[dict]:
        return []

    with patch("core.ksef.adapters.http.httpx.Client") as http_mock, \
         patch("tools.ksef_daemon.load_config") as cfg_mock:
        factory = _build_send_factory(run_query, repo, dry_run=True)

        from unittest.mock import MagicMock
        scan = MagicMock()
        scan.scan.return_value = [_DOC]
        mock_repo = MagicMock()
        mock_repo.list_stuck.return_value = []
        daemon = KSeFDaemon(scan=scan, send_factory=factory, repo=mock_repo, sleep=lambda _: None)
        results = daemon.run_once()

        http_mock.assert_not_called()
        cfg_mock.assert_not_called()

    assert len(results) == 1
