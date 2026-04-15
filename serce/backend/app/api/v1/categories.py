"""Public reference endpoint: list service categories.

Public endpoint — no auth, no rate limit (M2).
Rate limiting will arrive in M3 (slowapi global middleware).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.session import get_db
from app.schemas.category import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    active: bool | None = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> list[Category]:
    stmt = select(Category)
    if active is not None:
        stmt = stmt.where(Category.active == active)
    stmt = stmt.order_by(Category.sort_order, Category.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
