"""Integration test fixtures: live Postgres for schema verification.

Requires `TEST_DATABASE_URL` env var, e.g.:
    postgresql+asyncpg://serce:serce_dev@localhost:5432/serce_test

Run locally (with docker compose up -d db on VPS):
    TEST_DATABASE_URL=postgresql+asyncpg://serce:serce_dev@localhost:5432/serce \
        pytest tests/integration -v

If unset, all integration tests are skipped.

Each test using `clean_db` starts with an empty `public` schema.
Alembic migrations are run via subprocess (avoids nested asyncio.run in env.py).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND_DIR = Path(__file__).resolve().parents[2]
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def _require_db() -> str:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set — integration tests require live Postgres.")
    return TEST_DATABASE_URL


def run_alembic(cmd: str, target: str) -> None:
    """Run `alembic <cmd> <target>` as subprocess with TEST_DATABASE_URL."""
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL or ""
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", cmd, target],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic {cmd} {target} failed (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


async def _reset_schema(url: str) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
            await conn.exec_driver_sql("CREATE SCHEMA public")
            await conn.exec_driver_sql("GRANT ALL ON SCHEMA public TO public")
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def clean_db():
    """Reset `public` schema before & after test. Yields the test DB URL."""
    url = _require_db()
    await _reset_schema(url)
    try:
        yield url
    finally:
        await _reset_schema(url)


@pytest_asyncio.fixture
async def migrated_db(clean_db):
    """clean_db + `alembic upgrade head`. Yields a session factory."""
    run_alembic("upgrade", "head")
    engine = create_async_engine(clean_db)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield session_factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def integration_client(migrated_db):
    """ASGI client against FastAPI app, with get_db overridden to the test DB.

    Combines `migrated_db` (test Postgres with seed data applied) + ASGI transport.
    Use for endpoint-layer integration tests.
    """
    from app.db.session import get_db
    from app.main import app

    async def _override_get_db():
        async with migrated_db() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)
