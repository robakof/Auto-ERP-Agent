"""KSeF report aggregator — pure logic, reads from ShipmentRepository.

    from core.ksef.usecases.report import build_report
    report = build_report(repo, since=datetime(...))
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from core.ksef.adapters.erp_counter import EligibleDoc
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus, Wysylka

_RODZAJE = ("FS", "FSK", "FSK_RABAT")


@dataclass(frozen=True)
class CoverageData:
    """Comarch vs KSeF coverage comparison."""
    erp_counts: dict[str, int]       # rodzaj -> count in Comarch
    ksef_counts: dict[str, int]      # rodzaj -> count tracked in ksef_wysylka
    missing: list[EligibleDoc]       # docs in Comarch but not in ksef_wysylka

    @property
    def total_erp(self) -> int:
        return sum(self.erp_counts.values())

    @property
    def total_ksef(self) -> int:
        return sum(self.ksef_counts.values())

    @property
    def total_missing(self) -> int:
        return len(self.missing)

    @property
    def has_gap(self) -> bool:
        return self.total_missing > 0


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
    coverage: CoverageData | None = None

    @property
    def has_problems(self) -> bool:
        has_gap = self.coverage is not None and self.coverage.has_gap
        return bool(self.errors) or bool(self.rejected) or not self.all_sent_today or has_gap


def build_report(
    repo: ShipmentRepository,
    *,
    since: datetime,
    clock: datetime | None = None,
    erp_eligible: list[EligibleDoc] | None = None,
) -> ReportData:
    """Build report from repository data since given datetime.

    If erp_eligible is provided, builds coverage comparison section.
    """
    now = clock or datetime.now(timezone.utc).replace(tzinfo=None)
    counts = repo.count_by_status(since=since)
    total = sum(counts.values())

    errors = repo.list_by_status(ShipmentStatus.ERROR, limit=50)
    errors = [w for w in errors if w.created_at >= since]

    rejected = repo.list_by_status(ShipmentStatus.REJECTED, limit=50)
    rejected = [w for w in rejected if w.created_at >= since]

    pending = _get_pending(repo, since)
    all_sent = _check_all_sent_today(counts, pending)

    coverage = None
    if erp_eligible is not None:
        coverage = _build_coverage(repo, erp_eligible, since)

    return ReportData(
        since=since,
        generated_at=now,
        counts=counts,
        total=total,
        errors=errors,
        rejected=rejected,
        pending=pending,
        all_sent_today=all_sent,
        coverage=coverage,
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


def _build_coverage(
    repo: ShipmentRepository,
    erp_eligible: list[EligibleDoc],
    since: datetime,
) -> CoverageData:
    """Compare ERP eligible docs against tracked shipments."""
    since_date = since.date() if isinstance(since, datetime) else since

    erp_counts: Counter[str] = Counter()
    for doc in erp_eligible:
        erp_counts[doc.rodzaj] += 1

    tracked = repo.tracked_gids(since=since_date)
    # Count tracked docs per rodzaj
    ksef_counts: Counter[str] = Counter()
    for _gid, rodzaj in tracked:
        ksef_counts[rodzaj] += 1

    # Find missing: in ERP but not tracked (by gid, regardless of rodzaj)
    tracked_gids = {gid for gid, _ in tracked}
    missing = [doc for doc in erp_eligible if doc.gid not in tracked_gids]

    return CoverageData(
        erp_counts={r: erp_counts.get(r, 0) for r in _RODZAJE},
        ksef_counts={r: ksef_counts.get(r, 0) for r in _RODZAJE},
        missing=missing,
    )
