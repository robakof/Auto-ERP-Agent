"""Shipment audit events — immutable transition records."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.ksef.domain.shipment import ShipmentStatus


@dataclass(frozen=True)
class StatusTransition:
    id: int
    wysylka_id: int
    from_status: ShipmentStatus
    to_status: ShipmentStatus
    occurred_at: datetime
    meta: dict | None
