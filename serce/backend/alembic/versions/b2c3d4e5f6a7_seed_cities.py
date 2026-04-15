"""seed_cities

Seeds top-100 Polish cities from GUS data (Wikipedia cross-check, 2024-06-30).
CSV source: alembic/data/cities_pl.csv. IMMUTABLE per CONVENTION_MIGRATIONS.md —
future updates require a new migration + new CSV, not edit-in-place.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15

"""
import csv
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


# CSV lives next to versions/ under data/. Resolved at runtime, immutable.
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "cities_pl.csv"


def _load_cities() -> list[dict]:
    rows: list[dict] = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "name": row["name"],
                    "type": "CITY",
                    "parent_id": int(row["voivodeship_id"]),
                }
            )
    return rows


def upgrade() -> None:
    # locationtype enum already exists (created by M1); reference without recreating.
    location_type = sa.Enum("VOIVODESHIP", "CITY", name="locationtype", create_type=False)
    locations = sa.table(
        "locations",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("type", location_type),
        sa.column("parent_id", sa.Integer),
    )
    op.bulk_insert(locations, _load_cities())


def downgrade() -> None:
    # Precise delete: only cities we inserted (by name), scoped to CITY + valid voivodeship parents.
    # Avoids wiping user-added cities with the same scope.
    names = tuple(row["name"] for row in _load_cities())
    if not names:
        return
    op.execute(
        sa.text(
            "DELETE FROM locations WHERE type = 'CITY' "
            "AND parent_id BETWEEN 1 AND 16 AND name IN :names"
        ).bindparams(sa.bindparam("names", expanding=True, value=list(names)))
    )
