"""KSeF report aggregator — pure logic, reads from ShipmentRepository.

    from core.ksef.usecases.report import build_report
    report = build_report(repo, since=datetime(...))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus, Wysylka


@dataclass(frozen=True)
class ReportData:
    """Aggregated report — reusable for email, CLI, dashboard."""
    since: datetime
    generated_at: datetime
    counts: dict[ShipmentStatus, int]
    total: int
    errors: list[Wysylka]
    rejected: list[Wysylka]
    pending: list[Wysylka]
    all_sent_today: bool

    @property
    def has_problems(self) -> bool:
        return bool(self.errors) or bool(self.rejected) or not self.all_sent_today


def build_report(
    repo: ShipmentRepository,
    *,
    since: datetime,
    clock: datetime | None = None,
) -> ReportData:
    """Build report from repository data since given datetime."""
    now = clock or datetime.now(timezone.utc).replace(tzinfo=None)
    counts = repo.count_by_status(since=since)
    total = sum(counts.values())

    errors = repo.list_by_status(ShipmentStatus.ERROR, limit=50)
    errors = [w for w in errors if w.created_at >= since]

    rejected = repo.list_by_status(ShipmentStatus.REJECTED, limit=50)
    rejected = [w for w in rejected if w.created_at >= since]

    pending = _get_pending(repo, since)

    all_sent = _check_all_sent_today(counts, pending)

    return ReportData(
        since=since,
        generated_at=now,
        counts=counts,
        total=total,
        errors=errors,
        rejected=rejected,
        pending=pending,
        all_sent_today=all_sent,
    )


def _get_pending(repo: ShipmentRepository, since: datetime) -> list[Wysylka]:
    """Get documents still in non-terminal states."""
    pending = []
    for status in (ShipmentStatus.DRAFT, ShipmentStatus.QUEUED,
                   ShipmentStatus.AUTH_PENDING, ShipmentStatus.SENT):
        items = repo.list_by_status(status, limit=100)
        pending.extend(w for w in items if w.created_at >= since)
    return pending


def _check_all_sent_today(
    counts: dict[ShipmentStatus, int],
    pending: list[Wysylka],
) -> bool:
    """True if no errors, no rejected, no pending documents."""
    has_errors = counts.get(ShipmentStatus.ERROR, 0) > 0
    has_rejected = counts.get(ShipmentStatus.REJECTED, 0) > 0
    has_pending = len(pending) > 0
    return not has_errors and not has_rejected and not has_pending
