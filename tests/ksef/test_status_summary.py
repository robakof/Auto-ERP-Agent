"""Dashboard + count_by_status tests."""
from __future__ import annotations

import io
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus


_NOW = datetime(2026, 4, 16, 12, 0, 0)


@pytest.fixture
def repo(tmp_path: Path) -> ShipmentRepository:
    ticker = iter(_NOW + timedelta(seconds=i) for i in range(1000))
    r = ShipmentRepository(tmp_path / "ksef.db", clock=lambda: next(ticker))
    r.init_schema()
    return r


def _create(
    repo: ShipmentRepository, *, gid: int, rodzaj: str = "FS", attempt: int = 1,
):
    return repo.create(
        gid_erp=gid, rodzaj=rodzaj, nr_faktury=f"{rodzaj}-{gid}",
        data_wystawienia=date(2026, 4, 16),
        xml_path=f"output/ksef/{gid}.xml", xml_hash="a" * 64, attempt=attempt,
    )


# ---- count_by_status --------------------------------------------------------

def test_count_by_status_returns_dict_with_all_statuses(repo: ShipmentRepository) -> None:
    _create(repo, gid=1)
    counts = repo.count_by_status()
    assert set(counts.keys()) == set(ShipmentStatus)
    assert counts[ShipmentStatus.DRAFT] == 1


def test_count_by_status_groups_correctly(repo: ShipmentRepository) -> None:
    w1 = _create(repo, gid=1)
    w2 = _create(repo, gid=2)
    w3 = _create(repo, gid=3)
    repo.transition(w1.id, ShipmentStatus.QUEUED)
    repo.transition(w1.id, ShipmentStatus.AUTH_PENDING)
    repo.transition(w1.id, ShipmentStatus.SENT)
    repo.transition(w1.id, ShipmentStatus.ACCEPTED, ksef_number="K-1")
    repo.transition(w2.id, ShipmentStatus.ERROR, error_code="E")
    # w3 stays DRAFT

    counts = repo.count_by_status()
    assert counts[ShipmentStatus.ACCEPTED] == 1
    assert counts[ShipmentStatus.ERROR] == 1
    assert counts[ShipmentStatus.DRAFT] == 1
    assert counts[ShipmentStatus.SENT] == 0


def test_count_by_status_since_filter(repo: ShipmentRepository) -> None:
    _create(repo, gid=1)
    _create(repo, gid=2)
    _create(repo, gid=3)
    # `since` clock advances with ticker — cutoff in the middle
    since = _NOW + timedelta(seconds=1)  # skip first row (t=0)
    counts = repo.count_by_status(since=since)
    # Rows 2 (t=1s) and 3 (t=2s) included
    assert counts[ShipmentStatus.DRAFT] == 2


def test_count_by_status_empty_db(repo: ShipmentRepository) -> None:
    counts = repo.count_by_status()
    assert all(n == 0 for n in counts.values())


# ---- ksef_status.py --summary ---------------------------------------------

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "ksef_status.py"


def _run_status(args: list[str], db_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--db", str(db_path), *args],
        capture_output=True, text=True, check=False,
    )


def test_summary_runs_on_empty_db(tmp_path: Path) -> None:
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    result = _run_status(["--summary"], db)
    assert result.returncode == 0
    assert "podsumowanie" in result.stdout
    assert "Dzis" in result.stdout
    assert "Ostatnie 7 dni" in result.stdout
    assert "Lacznie w DB:  0" in result.stdout


def test_summary_shows_counts(tmp_path: Path) -> None:
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    w1 = repo.create(
        gid_erp=1, rodzaj="FS", nr_faktury="FS-1",
        data_wystawienia=date(2026, 4, 16),
        xml_path="x.xml", xml_hash="a" * 64,
    )
    repo.transition(w1.id, ShipmentStatus.QUEUED)
    repo.transition(w1.id, ShipmentStatus.AUTH_PENDING)
    repo.transition(w1.id, ShipmentStatus.SENT)
    repo.transition(w1.id, ShipmentStatus.ACCEPTED, ksef_number="K-1")

    result = _run_status(["--summary"], db)
    assert result.returncode == 0
    assert "ACCEPTED" in result.stdout
    assert "Lacznie w DB:  1" in result.stdout


def test_summary_alerts_error_status(tmp_path: Path) -> None:
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    w1 = repo.create(
        gid_erp=1, rodzaj="FS", nr_faktury="FS-1",
        data_wystawienia=date(2026, 4, 16),
        xml_path="x.xml", xml_hash="a" * 64,
    )
    repo.transition(w1.id, ShipmentStatus.ERROR, error_code="E")
    result = _run_status(["--summary"], db)
    assert result.returncode == 0
    assert "UWAGA" in result.stdout


def test_default_behavior_is_summary(tmp_path: Path) -> None:
    """Running with no args → summary mode."""
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    result = _run_status([], db)
    assert result.returncode == 0
    assert "podsumowanie" in result.stdout


def test_rodzaj_without_gid_is_rejected(tmp_path: Path) -> None:
    """W1 fix: --rodzaj wymaga --gid."""
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    result = _run_status(["--rodzaj", "FS"], db)
    assert result.returncode == 2
    assert "--rodzaj wymaga --gid" in result.stderr


def test_gid_zero_opens_table_not_summary(tmp_path: Path) -> None:
    """W2 fix: --gid 0 must use `is not None` check, not truthy."""
    db = tmp_path / "ksef.db"
    repo = ShipmentRepository(db)
    repo.init_schema()
    result = _run_status(["--gid", "0"], db)
    assert result.returncode == 0
    # GID=0 has no rows → "Brak wysylek." message from table branch,
    # NOT "podsumowanie" header from summary branch.
    assert "Brak wysylek" in result.stdout
    assert "podsumowanie" not in result.stdout
