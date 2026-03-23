# Code Review: JAS API — integracja WZ → zlecenie spedycyjne

Date: 2026-03-23
Scope: `tools/jas_client.py`, `tools/jas_mapper.py`, `tools/jas_export.py`,
       `solutions/jas/wz_jas_export.sql`, `solutions/jas/wz_jas_pending.sql`

---

## Summary

**Overall assessment:** NEEDS REVISION
**Code maturity level:** Mid — uzasadnienie: `jas_client.py` i `jas_mapper.py` są na poziomie senior
(czyste klasy, separacja odpowiedzialności, walrus operator, token caching). `jas_export.py`
i SQL obniżają ocenę do Mid przez SQL injection risk i brak idempotentności.

---

## Findings

### Critical Issues (must fix)

**[jas_export.py:35-36] SQL injection przez konkatenację stringa**

```python
# present
safe = numer.replace("'", "''")
where = f"WHERE numer_wz = '{safe}'"
```

`replace("'", "''")` to podstawowe escaping — nie obroni przed sekwencjami `--`, `; DROP`, `CHAR()`.
Wartość trafia do `SqlClient().execute(sql, inject_top=None)` jako raw SQL.
W kontekście wewnętrznego CLI ryzyko jest niskie, ale zasada jest zła — nie otwiera się luki
którą można przypadkowo poszerzyć (np. CLI wystawione przez wrapper webowy).

Fix: SqlClient powinien przyjmować parametry (`@numer_wz`) — eskalacja do Developera
żeby sprawdzić czy `sql_client.py` obsługuje parametrized queries.
Fallback: strict validation (regex dopasowanie do wzorca `WZ/\d{4}/\d+`) przed interpolacją.

---

**[jas_export.py:56-87] Brak idempotentności — duplikaty zleceń JAS**

`--all` zwraca wszystkie WZ bez FV. Między wysłaniem do JAS a wystawieniem FV (mogą minąć dni)
każde kolejne `--all` wyśle te same WZ ponownie. JAS prawdopodobnie nie deduplikuje po `customerRefNo`.
Skutek biznesowy: jeden transport zamówiony kilka razy.

Obecny plan ("śledzenie wysłanych WZ poza zakresem MVP") naraża produkcję na realne błędy.
To nie jest "nice to have" — to warunek bezpiecznego działania.

Fix architektoniczny (patrz sekcja Architectural Notes):
Tabela `jas_shipments(wz_id, jas_shipment_id, sent_at, status)` — przed wysłaniem
sprawdź czy `wz_id` już istnieje. Alternatywa minimalna: flaga `jas_sent` w widoku/tabeli ERP.

---

### Warnings (should fix)

**[wz_jas_export.sql:167-170] `WITH (NOLOCK)` na tabelach WMS**

```sql
LEFT JOIN wms.documents d   WITH (NOLOCK) ON ...
LEFT JOIN wms.items i       WITH (NOLOCK) ON ...
LEFT JOIN wms.LogisticUnitObjects lo WITH (NOLOCK) ON ...
LEFT JOIN wms.LogisticUnitTypes lt   WITH (NOLOCK) ON ...
```

`NOLOCK` = dirty read — możliwe odczytanie danych niecommitowanych lub w trakcie update.
Dla danych palet (typ, ilość, wymiary) wysyłanych do spedytora dirty read może skutkować
błędnym payloadem (np. `ilosc=0` bo transakcja jeszcze nie zacommitowała).

Fix: usunąć `NOLOCK` jeśli nie ma udokumentowanego powodu wydajnościowego.
Jeśli WMS ma blokady — zbadać i naprawić źródło, nie obejść `NOLOCK`.

---

**[wz_jas_pending.sql:7-9] Stale komentarze — rozbieżność z kodem**

Komentarz w SQL opisuje dwa placeholdery `{filter_wz_id}` i `{filter_numer}`,
ale faktyczny placeholder w SQL to jeden `{where_clause}`. Komentarz pozostałość po wcześniejszej wersji.

Fix: zaktualizować komentarz do aktualnego stanu.

---

**[jas_export.py:43] `RuntimeError` z `_load_rows` nie jest łapany w `run()`**

```python
# _load_rows rzuca RuntimeError gdy SQL failed
result = SqlClient().execute(sql, inject_top=None)
if not result["ok"]:
    raise RuntimeError(result["error"]["message"])
```

W `run()` catch obejmuje tylko `JasApiError, JasAuthError`. Błąd SQL propaguje do `main()`
bez ustrukturyzowanego outputu — `print_json` nie zostaje wywołany.

Fix: owinąć `_load_rows` w `try/except RuntimeError` w `run()`, zwrócić `{"ok": False, "errors": [...]}`

---

**[wz_jas_export.sql] Wymiary palet hardcoded w widoku SQL**

```sql
CASE lt.Name WHEN 'Pół paleta jednorazowa' THEN 60 WHEN NULL THEN NULL ELSE 120 END AS dlugosc_cm,
```

Jeśli JAS zmieni wymagane wymiary lub firma zacznie używać niestandardowych palet — zmiana wymaga
ALTER VIEW. Logika biznesowa powinna być konfigurywalna, nie zabetonowana w widoku.

Fix (opcja 1): tabela konfiguracyjna `AILO.jas_pallet_types(name, dlugosc, szerokosc, wysokosc, waga_max)`,
JOIN zamiast CASE.
Fix (opcja 2): przenieść mapowanie do `jas_mapper.py` (Python dict — łatwiejsze zmiany).

---

**[tmp/test_jas.py] Test w katalogu tymczasowym**

`tmp/` jest katalogiem scratch — może być czyszczony. Test zostanie utracony.

Fix: przenieść do `tests/test_jas.py` lub `tests/jas/`.

---

### Suggestions (nice to have)

**[jas_mapper.py] Brak walidacji pól wymaganych przez JAS**

`rows_to_shipment` milcząco przepuszcza puste stringi w polach adresowych
(`"" ` zamiast `None`). JAS może odrzucić zlecenie jeśli np. `city` jest pusty.

Sugestia: walidacja przed zwróceniem payloadu — lista pól wymaganych, rzucenie wyjątku
z nazwą WZ i listą brakujących pól.

---

**[jas_client.py] Token cache na poziomie instancji**

Jeśli `JasClient()` będzie tworzony wielokrotnie (np. w pętli, przez CLI wielokrotne wywołania),
token nie jest współdzielony. Obecny kod w `jas_export.py` tworzy jeden client na run — OK.
Ale rosnący system może to złamać.

Sugestia: moduł-level singleton lub plik tymczasowy tokenu (`.jas_token_cache`) jeśli system
wywoła CLI kilka razy szybko po sobie.

---

**[wz_jas_export.sql:126-131] Parser adresu — brak edge case'ów**

Parser ulicy (CTE `addr`) obsługuje popularne wzorce. Nieobsłużone:
- "ul. 3 Maja 15" (cyfry w nazwie ulicy, nie numerze)
- "Jana Pawła II 12/4" (numer z lokalem)
- Brak numeru w ogóle (adres tylko z nazwą ulicy)

Sugestia: test na realnych danych z `CDN.KntAdresy` — sprawdzić procent wierszy gdzie
`odbiorca_nr_domu IS NULL` mimo że ulica zawiera numer.

---

## Architectural Notes

### Brakująca warstwa: tracking wysłanych WZ

Najważniejsza luka architektoniczna projektu. System wysyła, ale nie pamięta co wysłał.

Minimalne rozwiązanie:
```sql
CREATE TABLE AILO.jas_shipments (
    id           INT IDENTITY PRIMARY KEY,
    wz_id        INT NOT NULL,
    numer_wz     NVARCHAR(50),
    jas_id       INT,           -- ID zwrócone przez JAS API
    sent_at      DATETIME DEFAULT GETDATE(),
    status       NVARCHAR(20) DEFAULT 'sent',
    error_msg    NVARCHAR(MAX)
);
CREATE UNIQUE INDEX uix_jas_shipments_wz ON AILO.jas_shipments(wz_id) WHERE status = 'sent';
```

`jas_export.py` przed wysłaniem: `SELECT 1 FROM AILO.jas_shipments WHERE wz_id = ? AND status = 'sent'`
Po wysłaniu: `INSERT INTO AILO.jas_shipments`.

Alternatywa bez tabeli: kolumna `TrN_Uwagi` w ERP (mniej czyste, ale bez DDL).

---

## Recommended Actions

- [ ] **[Critical]** Dodać walidację `--numer` (regex) lub parameterized query w SqlClient
- [ ] **[Critical]** Zaprojektować `AILO.jas_shipments` tracking table + integracja z `jas_export.py`
- [ ] **[Warning]** Usunąć `WITH (NOLOCK)` z SQL widoku — zbadać czy są blokady WMS
- [ ] **[Warning]** Naprawić obsługę `RuntimeError` w `run()`
- [ ] **[Warning]** Zaktualizować komentarz w `wz_jas_pending.sql`
- [ ] **[Suggestion]** Przenieść `tmp/test_jas.py` → `tests/test_jas.py`
- [ ] **[Suggestion]** Walidacja pól adresowych w `jas_mapper.py` przed zwróceniem payloadu
