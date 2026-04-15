---
convention_id: migrations
version: "1.0"
status: active
created: 2026-04-15
updated: 2026-04-15
author: architect
owner: architect
approver: dawid
audience: [developer, architect]
scope: "Cykl życia migracji bazy danych — immutability po release"
---

# CONVENTION_MIGRATIONS — Cykl życia migracji

## TL;DR

- Raz wydana migracja jest immutable — nie edytuj jej w miejscu.
- Każda zmiana schema po pierwszym release = nowa migracja (`alembic revision -m "..."`).
- Wyjątek M1: fundament projektu, 0 użytkowników — dopuszczalny jednorazowy in-place edit.
- Wyjątek pre-release: migracja zcommitowana ale nigdy niezaaplikowana na prod — edit dopuszczalny, preferowana nowa migracja.
- Dotyczy każdego repo z Alembic w projekcie (obecnie `serce/backend/alembic/`).

---

## Zakres

**Pokrywa:**
- Cykl życia migracji Alembic (schema + data migrations).
- Warunki dopuszczalnej edycji zaaplikowanej migracji.
- Relację między git history migracji a stanem `alembic_version` na prod.

**NIE pokrywa:**
- Nazewnictwo tabel/kolumn (patrz `CONVENTION_DB_SCHEMA.md` dla mrowisko.db).
- Struktura schematu domenowego Serce (patrz `documents/human/plans/serce_architecture.md`).
- Proces review migracji (patrz `workflows/workflow_code_review.md`).

---

## Kontekst

### Problem

Bez zasady immutability:
- Prod schema rozjeżdża się po cichu z historią migracji.
- `alembic upgrade head` na świeżej bazie daje inny wynik niż na istniejącej (tech debt loop).
- Review zaaplikowanej migracji staje się bezwartościowy — kod mógł się zmienić po deploy.
- Downgrade nie działa deterministycznie (każda środowisko ma swoją wersję migracji).

### Rozwiązanie

Migracja po pierwszym deploy = append-only log. Każda zmiana schema → nowa migracja z własnym revision ID. Alembic head tworzy się przez sekwencję migracji, nie przez edycję poprzednich.

---

## Reguły

### 01R: Immutability po release

Migracja zaaplikowana na produkcji (wpis w `alembic_version` jakiegokolwiek środowiska prod) MUSI pozostać niezmieniona.

Każda zmiana schema po tym momencie = **nowa migracja Alembic**:

```bash
alembic revision -m "short description"
# edytuj nową migrację w alembic/versions/{revision_id}_short_description.py
```

### 02R: Zakres immutability

Dotyczy:
- Schema migrations (CREATE/ALTER/DROP TABLE, INDEX, CONSTRAINT).
- Data migrations (seed, backfill, enum value changes).
- Enum changes (rename, add/remove values).

Dotyczy każdego repo z Alembic w projekcie. Obecnie aktywne: `serce/backend/alembic/`.

### 03R: Wyjątek — pre-release

Migracja może być edytowana w miejscu jeśli spełnia OBIE zasady:
- Nie została zcommitowana do main, LUB zcommitowana ale nigdy niezaaplikowana na żadnym środowisku prod.
- Developer zweryfikował `git log` + `docker compose exec db psql -c "SELECT version_num FROM alembic_version"` na prod — revision nie występuje.

Nawet wtedy preferowana jest nowa migracja (czystsza historia). Edit pre-release jest dopuszczalny, nie zalecany.

### 04R: Wyjątek — M1 fundament

Projekt Serce M1 (initial schema, revision `f8e3d1a9b7c2`) otrzymał jednorazowe pozwolenie na in-place edit podczas revision (review v2, 2026-04-15) z uzasadnieniem: 0 użytkowników, fundament, fix schemy przed pierwszym prawdziwym release.

**To był ostatni raz.** Od M2 każda zmiana schema = nowa migracja bez wyjątków.

### 05R: Nowa migracja — minimum metadanych

Każda nowa migracja MUSI zawierać w komentarzu na górze pliku:

```python
"""Opis zmiany - krótki, imperatywny.

Revision ID: <auto>
Revises: <parent revision>
Create Date: <auto>

Scope: <opis co migracja robi biznesowo>
Milestone: <M2, M3, itd.>
"""
```

### 06R: Enforcement

Convention jest tekstową zasadą. Propozycja check w narzędziach (nie wymagane do aktywacji):
- `arch_check.py` może czytać git log migracji i ostrzec (warning) gdy plik migracji został zmieniony po pierwszym commicie.
- Warning nie blokuje — decyzję o edit pre-release podejmuje developer po zweryfikowaniu 03R.

---

## Przykłady

### Przykład 1: Dodanie kolumny po release (poprawnie)

```bash
# M2 właśnie się skończył, M3 wymaga nowej kolumny
cd serce/backend
alembic revision -m "add user avatar_url column"
# → alembic/versions/a1b2c3d4e5f6_add_user_avatar_url_column.py
# Edycja NOWEJ migracji, stare nietknięte.
alembic upgrade head
```

### Przykład 2: Pre-release fix (dopuszczalne)

```bash
# Migracja commitowana 10 minut temu, jeszcze nie wdrożona na VPS
git log --oneline -5  # potwierdza lokalny commit
ssh vps "docker compose exec db psql -c 'SELECT version_num FROM alembic_version'"
# → pusta lub starsza revision → OK, edit dopuszczalny

# Preferowana ścieżka mimo wszystko:
alembic revision -m "fix column default"
```

---

## Antywzorce

### 01AP: In-place edit zaaplikowanej migracji

**Źle:**
```python
# alembic/versions/f8e3d1a9b7c2_initial_schema.py (revision już na prod)
def upgrade():
    op.create_table("users", ...)
    op.create_table("new_table_added_silently", ...)  # ← po deploy
```

**Dlaczego:** Prod miał stary upgrade(); `alembic upgrade head` na prod = noop. Schema na prod rozjeżdża się z intent. Nowy developer klonuje repo i `alembic upgrade head` daje inny schema niż prod.

**Dobrze:**
```bash
alembic revision -m "add new_table"
# nowa migracja, parent = f8e3d1a9b7c2
```

### 02AP: Rename istniejącej migracji

**Źle:** Zmiana nazwy pliku `f8e3d1a9b7c2_initial_schema.py` → `f8e3d1a9b7c2_initial_schema_v2.py` po deploy.

**Dlaczego:** Revision ID jest w `alembic_version` na prod. Rename pliku nie zmienia ID, ale maskuje faktyczny stan. Przy downgrade Alembic nie znajduje oryginalnej ścieżki.

**Dobrze:** Nazwa pliku jest immutable razem z migracją.

### 03AP: Edit dla "drobnej poprawki" bez nowej migracji

**Źle:**
```python
# "Tylko zmienię default z 0 na 1 w zaaplikowanej migracji"
op.add_column("users", sa.Column("points", sa.Integer, server_default="1"))  # było "0"
```

**Dlaczego:** Prod ma już kolumnę z default=0. Edit migracji nie zmieni danych ani default-a na prod. Nowy developer dostanie default=1 lokalnie, prod pozostanie 0. Silent drift.

**Dobrze:**
```bash
alembic revision -m "change users.points default from 0 to 1"
# W nowej migracji: op.alter_column("users", "points", server_default="1")
```

---

## References

- Precedens: `documents/human/reports/serce_m1_code_review_v2.md` (linie 53-57, 185-187) — uzasadnienie S6.
- Alembic best practices: https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration (append-only history)
- Konwencja pokrewna: `CONVENTION_DB_SCHEMA.md` (schemat mrowisko.db, inne DB).

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-04-15 | Początkowa wersja. Wywodzi się z review v2 M1 (S6). Uzasadnienie: wprowadzenie przed startem M2 Serce. |
