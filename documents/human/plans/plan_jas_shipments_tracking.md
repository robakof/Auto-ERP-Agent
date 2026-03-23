# Plan implementacji: AILO.jas_shipments — warstwa stanu JAS

Date: 2026-03-23
Owner: Developer
Ref: `documents/human/reports/architecture_review_jas.md` (P1)
Priority: CRITICAL — blokuje bezpieczne użycie produkcyjne

---

## Problem

`jas_export.py --all` nie śledzi co zostało wysłane.
Duplikaty możliwe gdy WZ jest w widoku (brak FV) a shipment już wysłany.

---

## Zakres

3 pliki do modyfikacji + 1 nowy SQL:

```
solutions/jas/create_jas_shipments.sql   ← NOWY (DDL)
tools/jas_export.py                      ← MODYFIKACJA (idempotentność)
tools/jas_client.py                      ← opcjonalna modyfikacja (get_shipment reuse)
tmp/test_jas_idempotency.py              ← NOWY (test ręczny)
```

---

## Krok 1 — DDL: tabela AILO.jas_shipments

Plik: `solutions/jas/create_jas_shipments.sql`

```sql
-- =============================================================================
-- JAS shipments tracking — rejestr wysłanych WZ do JAS FBG
-- Cel: idempotentność (nie wysyłaj WZ drugi raz) + audit trail
-- =============================================================================

CREATE TABLE AILO.jas_shipments (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    wz_id       INT           NOT NULL,
    numer_wz    NVARCHAR(50)  NOT NULL,
    jas_id      INT           NULL,       -- ID zwrócone przez JAS API (NULL gdy błąd)
    sent_at     DATETIME      NOT NULL DEFAULT GETDATE(),
    status      NVARCHAR(20)  NOT NULL DEFAULT 'sent',  -- 'sent' | 'error'
    error_msg   NVARCHAR(MAX) NULL
);

-- Unikalność: jeden rekord 'sent' per wz_id
CREATE UNIQUE INDEX uix_jas_shipments_wz_sent
    ON AILO.jas_shipments(wz_id)
    WHERE status = 'sent';

-- Szybki lookup po wz_id
CREATE INDEX ix_jas_shipments_wz
    ON AILO.jas_shipments(wz_id);
```

**Uwagi do DDL:**
- `WHERE status = 'sent'` w unique index — pozwala na wiele rekordów `error` dla tego samego `wz_id` (retry history), ale blokuje drugi `sent`.
- Schemat `AILO` — zakładam że Developer ma uprawnienia CREATE TABLE w tym schemacie. Jeśli nie — zmienić na `dbo` lub inny dostępny.
- Nie dodawać `ON DELETE CASCADE` — rekordy mają być trwałe (audit).

---

## Krok 2 — Modyfikacja jas_export.py

### 2a. Funkcja sprawdzająca czy WZ była wysłana

Dodać przed `run()`:

```python
_CHECK_SQL = """
SELECT TOP 1 jas_id, sent_at
FROM AILO.jas_shipments
WHERE wz_id = {wz_id} AND status = 'sent'
"""

def _already_sent(wz_id: int) -> bool:
    """Zwraca True jeśli wz_id ma rekord 'sent' w jas_shipments."""
    sql = _CHECK_SQL.replace("{wz_id}", str(int(wz_id)))
    result = SqlClient().execute(sql, inject_top=None)
    return result["ok"] and len(result["rows"]) > 0
```

### 2b. Funkcja zapisująca wynik

```python
_INSERT_SQL = """
INSERT INTO AILO.jas_shipments (wz_id, numer_wz, jas_id, status, error_msg)
VALUES ({wz_id}, '{numer_wz}', {jas_id}, '{status}', {error_msg})
"""

def _record_result(wz_id: int, numer_wz: str, jas_id=None, error_msg=None) -> None:
    """Zapisuje wynik wysłania do AILO.jas_shipments."""
    status = 'sent' if error_msg is None else 'error'
    jas_id_sql = str(jas_id) if jas_id is not None else 'NULL'
    error_sql = f"'{error_msg.replace(chr(39), chr(39)*2)}'" if error_msg else 'NULL'
    numer_safe = numer_wz.replace("'", "''")
    sql = _INSERT_SQL.format(
        wz_id=int(wz_id),
        numer_wz=numer_safe,
        jas_id=jas_id_sql,
        status=status,
        error_msg=error_sql,
    )
    SqlClient().execute(sql, inject_top=None)
```

### 2c. Modyfikacja pętli w run()

Obecny kod (linie 66-86):
```python
for wid, wz_rows in grouped.items():
    payload = rows_to_shipment(wz_rows)
    numer_wz = wz_rows[0].get("numer_wz", str(wid))

    if payload is None:
        skipped += 1
        continue

    if dry_run:
        print(f"\n--- DRY RUN: {numer_wz} ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        sent += 1
        continue

    try:
        response = client.create_shipment(payload)
        print(f"OK: {numer_wz} → id={response.get('id', '?')}")
        sent += 1
    except (JasApiError, JasAuthError) as e:
        errors.append({"numer_wz": numer_wz, "error": str(e)})
```

Po modyfikacji:
```python
for wid, wz_rows in grouped.items():
    payload = rows_to_shipment(wz_rows)
    numer_wz = wz_rows[0].get("numer_wz", str(wid))

    if payload is None:
        skipped += 1
        continue

    if dry_run:
        already = _already_sent(wid)
        print(f"\n--- DRY RUN: {numer_wz} (already_sent={already}) ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        sent += 1
        continue

    if _already_sent(wid):
        print(f"SKIP: {numer_wz} — już wysłana do JAS")
        skipped += 1
        continue

    try:
        response = client.create_shipment(payload)
        jas_id = response.get("id")
        print(f"OK: {numer_wz} → id={jas_id}")
        _record_result(wid, numer_wz, jas_id=jas_id)
        sent += 1
    except (JasApiError, JasAuthError) as e:
        error_str = str(e)
        errors.append({"numer_wz": numer_wz, "error": error_str})
        _record_result(wid, numer_wz, error_msg=error_str)
```

---

## Krok 3 — Test

Plik: `tmp/test_jas_idempotency.py`

```python
"""Test idempotentności: druga próba wysłania tej samej WZ powinna zwrócić SKIP."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.jas_export import run

WZ_ID = <rzeczywiste_wz_id>  # podać ID WZ która już była wysłana

# Pierwsze wywołanie — powinno wysłać (jeśli nie było)
result1 = run(wz_id=WZ_ID, numer=None, dry_run=False)
print("Run 1:", result1)

# Drugie wywołanie — powinno SKIP
result2 = run(wz_id=WZ_ID, numer=None, dry_run=False)
print("Run 2:", result2)

assert result2["sent"] == 0, "Drugie wywołanie powinno skipować!"
assert result2["skipped"] == 1
print("OK: idempotentność działa.")
```

---

## Kolejność wykonania

1. `[ ]` Wykonaj `create_jas_shipments.sql` na bazie ERP (przez SQL Server Management Studio lub SqlClient)
2. `[ ]` Zaimplementuj `_already_sent()` i `_record_result()` w `jas_export.py`
3. `[ ]` Zmodyfikuj pętlę `run()` wg krok 2c
4. `[ ]` Uruchom `--dry-run` na istniejących WZ — sprawdź czy `already_sent` działa poprawnie
5. `[ ]` Uruchom test idempotentności (krok 3)
6. `[ ]` Commit

---

## Co poza zakresem tego planu

- Automatyczny trigger (cron) — osobny plan (P2)
- Parser adresu w Python — osobny plan (P4)
- Pętla zwrotna do ERP (zapis JAS ID w ERP) — decyzja użytkownika
- UI / raport wysłanych WZ — nice to have

---

## Uwaga dla Developera

`_already_sent()` i `_record_result()` używają string interpolacji do SQL
(analogicznie jak obecny kod) — wz_id jest zawsze `int(wz_id)` więc injection risk = 0.
Dla numer_wz używamy `replace("'", "''")` — wystarczające bo format jest `WZ/YYYY/NNNNN`.
