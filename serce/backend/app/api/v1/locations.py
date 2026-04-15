"""Public reference endpoint: list Polish voivodeships + cities.

Public endpoint — no auth, no rate limit (M2).
Rate limiting will arrive in M3 (slowapi global middleware).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.location import Location, LocationType
from app.db.session import get_db
from app.schemas.location import LocationRead

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationRead])
async def list_locations(
    type: LocationType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[Location]:
    stmt = select(Location)
    if type is not None:
        stmt = stmt.where(Location.type == type)
    stmt = stmt.order_by(Location.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
