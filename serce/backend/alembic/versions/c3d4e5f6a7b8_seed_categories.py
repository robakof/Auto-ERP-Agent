"""seed_categories

Seeds 9 top-level category groups (stable IDs 1-9) + subcategories per decyzja #106.
Leaf category required at Request/Offer create (decyzja #110).

NOTE (for code review): decyzja #106 says "26 podkategorii" but the literal list in
serce_architecture.md gives 27. Implemented 27 (list-authoritative). Architect to
confirm or scope-reduce at review.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-15

"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


# Stable IDs 1-9 for top-level groups. Order from decyzja #106.
# Do not reorder — FK references from Request/Offer are by id.
GROUPS = [
    (1, "Dom i otoczenie"),
    (2, "Opieka"),
    (3, "Nauka i rozwój"),
    (4, "Zdrowie i wsparcie"),
    (5, "Transport i mobilność"),
    (6, "IT i technika"),
    (7, "Sprawy urzędowe"),
    (8, "Pożyczanie rzeczy"),
    (9, "Inne"),
]

# Subcategories: (name, parent_id). sort_order assigned by list position within group.
SUBCATEGORIES = [
    # Group 1: Dom i otoczenie
    ("Prace domowe", 1),
    ("Gotowanie", 1),
    ("Naprawy i majsterkowanie", 1),
    ("Ogród i rośliny", 1),
    ("Zakupy i sprawunki", 1),
    # Group 2: Opieka
    ("Opieka nad dziećmi", 2),
    ("Opieka nad seniorami", 2),
    ("Opieka nad zwierzętami", 2),
    # Group 3: Nauka i rozwój
    ("Korepetycje szkolne", 3),
    ("Języki obce", 3),
    ("Programowanie i IT (nauka)", 3),
    ("Rękodzieło i hobby (nauka)", 3),
    # Group 4: Zdrowie i wsparcie
    ("Wsparcie emocjonalne", 4),
    ("Trening i sport", 4),
    ("Zdrowie codzienne", 4),
    # Group 5: Transport i mobilność
    ("Przewóz osoby", 5),
    ("Przeprowadzka i transport mebli", 5),
    ("Pomoc przy zakupach ciężkich", 5),
    # Group 6: IT i technika
    ("Naprawa komputera / telefonu", 6),
    ("Instalacja oprogramowania", 6),
    ("Sieć, WiFi, smart home", 6),
    # Group 7: Sprawy urzędowe
    ("Wypełnianie pism i dokumentów", 7),
    ("Tłumaczenia", 7),
    ("Pomoc w e-urzędach / ePUAP", 7),
    # Group 8: Pożyczanie rzeczy
    ("Narzędzia", 8),
    ("Sprzęt sportowy i turystyczny", 8),
    ("Książki, filmy, gry", 8),
    # Group 9: Inne — no subcategories
]


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("parent_id", sa.Integer),
        sa.column("icon", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("active", sa.Boolean),
    )

    # Groups with stable IDs + sort_order from position.
    group_rows = [
        {
            "id": gid,
            "name": name,
            "parent_id": None,
            "icon": None,
            "sort_order": idx,
            "active": True,
        }
        for idx, (gid, name) in enumerate(GROUPS)
    ]

    # Subcategories: autoincrement ID, sort_order within group by position.
    sub_rows = []
    group_counter: dict[int, int] = {}
    for name, parent_id in SUBCATEGORIES:
        group_counter[parent_id] = group_counter.get(parent_id, -1) + 1
        sub_rows.append(
            {
                "name": name,
                "parent_id": parent_id,
                "icon": None,
                "sort_order": group_counter[parent_id],
                "active": True,
            }
        )

    op.bulk_insert(categories, group_rows)
    # Reset sequence past stable IDs 1-9 before inserting autoincrement subcategories.
    op.execute(
        "SELECT setval(pg_get_serial_sequence('categories', 'id'), "
        "(SELECT MAX(id) FROM categories))"
    )
    op.bulk_insert(categories, sub_rows)


def downgrade() -> None:
    # Subcategories first (FK). Match by (parent_id BETWEEN 1 AND 9, name IN ...).
    sub_names = tuple(name for name, _ in SUBCATEGORIES)
    op.execute(
        sa.text(
            "DELETE FROM categories WHERE parent_id BETWEEN 1 AND 9 AND name IN :names"
        ).bindparams(sa.bindparam("names", expanding=True, value=list(sub_names)))
    )
    # Then groups (stable IDs 1-9).
    op.execute("DELETE FROM categories WHERE id BETWEEN 1 AND 9 AND parent_id IS NULL")
