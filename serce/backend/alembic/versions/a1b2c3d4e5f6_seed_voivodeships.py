"""seed_voivodeships

Seeds 16 Polish voivodeships with stable IDs (1-16, alphabetical).
IDs are referenced by seed_cities (literal parent_id, not name lookup).

Revision ID: a1b2c3d4e5f6
Revises: f8e3d1a9b7c2
Create Date: 2026-04-15

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f8e3d1a9b7c2"
branch_labels = None
depends_on = None


# Stable IDs 1-16, alphabetical order. Do not reorder — referenced by seed_cities.
VOIVODESHIPS = [
    (1, "Dolnośląskie"),
    (2, "Kujawsko-pomorskie"),
    (3, "Lubelskie"),
    (4, "Lubuskie"),
    (5, "Łódzkie"),
    (6, "Małopolskie"),
    (7, "Mazowieckie"),
    (8, "Opolskie"),
    (9, "Podkarpackie"),
    (10, "Podlaskie"),
    (11, "Pomorskie"),
    (12, "Śląskie"),
    (13, "Świętokrzyskie"),
    (14, "Warmińsko-mazurskie"),
    (15, "Wielkopolskie"),
    (16, "Zachodniopomorskie"),
]


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
    op.bulk_insert(
        locations,
        [
            {"id": vid, "name": name, "type": "VOIVODESHIP", "parent_id": None}
            for vid, name in VOIVODESHIPS
        ],
    )
    # Reset autoincrement sequence past stable IDs so future inserts (cities)
    # don't collide with reserved 1-16.
    op.execute(
        "SELECT setval(pg_get_serial_sequence('locations', 'id'), "
        "(SELECT MAX(id) FROM locations))"
    )


def downgrade() -> None:
    # Precise delete: only rows we inserted. Stable IDs 1-16 guarantee no collision
    # with user-added voivodeships (if any appear in the future).
    op.execute("DELETE FROM locations WHERE id BETWEEN 1 AND 16 AND type = 'VOIVODESHIP'")
