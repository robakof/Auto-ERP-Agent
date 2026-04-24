"""Shipment domain — immutable Wysylka + forward-only state machine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class ShipmentStatus(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    AUTH_PENDING = "AUTH_PENDING"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


_ALLOWED: dict[ShipmentStatus, frozenset[ShipmentStatus]] = {
    ShipmentStatus.DRAFT: frozenset({ShipmentStatus.QUEUED, ShipmentStatus.ERROR}),
    ShipmentStatus.QUEUED: frozenset({ShipmentStatus.AUTH_PENDING, ShipmentStatus.ERROR, ShipmentStatus.DRAFT}),
    ShipmentStatus.AUTH_PENDING: frozenset({ShipmentStatus.SENT, ShipmentStatus.ERROR, ShipmentStatus.DRAFT}),
    ShipmentStatus.SENT: frozenset({
        ShipmentStatus.ACCEPTED,
        ShipmentStatus.REJECTED,
        ShipmentStatus.ERROR,
        ShipmentStatus.DRAFT,
    }),
    ShipmentStatus.ACCEPTED: frozenset(),
    ShipmentStatus.REJECTED: frozenset(),
    ShipmentStatus.ERROR: frozenset(),
}

_ACTIVE_STATES: frozenset[ShipmentStatus] = frozenset({
    ShipmentStatus.QUEUED,
    ShipmentStatus.AUTH_PENDING,
    ShipmentStatus.SENT,
    ShipmentStatus.ACCEPTED,
})


def is_valid_transition(old: ShipmentStatus, new: ShipmentStatus) -> bool:
    return new in _ALLOWED[old]


def is_active(status: ShipmentStatus) -> bool:
    """Stany blokujące nową próbę wysyłki tego samego (gid, rodzaj)."""
    return status in _ACTIVE_STATES


@dataclass(frozen=True)
class Wysylka:
    id: int
    gid_erp: int
    rodzaj: str  # 'FS' | 'FSK'
    nr_faktury: str
    data_wystawienia: date
    xml_path: str
    xml_hash: str
    status: ShipmentStatus
    ksef_session_ref: str | None
    ksef_invoice_ref: str | None
    ksef_number: str | None
    upo_path: str | None
    error_code: str | None
    error_msg: str | None
    attempt: int
    created_at: datetime
    queued_at: datetime | None
    sent_at: datetime | None
    accepted_at: datetime | None
    rejected_at: datetime | None
    errored_at: datetime | None
