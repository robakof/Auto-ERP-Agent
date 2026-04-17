"""CLI: promote user to ADMIN role by email.

Usage:
    py -m app.cli.promote_admin --email admin@example.com
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.models.user import User, UserRole


async def _promote(email: str) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            row = (await conn.execute(
                select(User.id, User.role).where(User.email == email)
            )).first()
            if not row:
                print(f"User with email '{email}' not found.")
                sys.exit(1)
            if row.role == UserRole.ADMIN:
                print(f"User '{email}' is already ADMIN.")
                return
            await conn.execute(
                update(User).where(User.id == row.id).values(role=UserRole.ADMIN)
            )
        print(f"User '{email}' promoted to ADMIN.")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote user to ADMIN role")
    parser.add_argument("--email", required=True, help="User email to promote")
    args = parser.parse_args()
    asyncio.run(_promote(args.email))


if __name__ == "__main__":
    main()
