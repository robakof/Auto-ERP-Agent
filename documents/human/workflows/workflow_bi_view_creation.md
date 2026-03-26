---
workflow_id: bi_view_creation
version: "3.0"
owner_role: erp_specialist
trigger: "Użytkownik prosi o utworzenie widoku BI"
participants:
  - erp_specialist (implementacja)
  - analyst (recenzja planu, weryfikacja eksportu)
  - human (DBA deployment)
related_docs:
  - documents/erp_specialist/ERP_SQL_SYNTAX.md
  - documents/erp_specialist/ERP_SCHEMA_PATTERNS.md
  - solutions/reference/obiekty.tsv
  - solutions/reference/numeracja_wzorce.tsv
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "solutions/bi/views/{NazwaWidoku}.sql"
  - type: file
    path: "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
  - type: commit
---

# Workflow: Tworzenie widoku BI

Proces tworzenia widoku BI dla systemu ERP Comarch XL.

**Statusy faz:** `PASS` | `BLOCKED` | `ESCALATE`

## Outline

0. **Inicjalizacja** — utworzenie plików roboczych
1. **Discovery** — analiza struktury, enumeracje, typy danych
2. **Plan mapowania** — plan kolumn + recenzja Analityka
3. **SQL na brudnopisie** — iteracyjne budowanie SELECT
4. **Weryfikacja eksportu** — bi_verify + approval Analityka
5. **Zapis i wdrożenie** — CREATE VIEW, DBA, katalog, commit

---

## Inicjalizacja

**Owner:** ERP Specialist

### Steps

1. Ustal `{NazwaWidoku}` = nazwa tabeli źródłowej bez prefixu `CDN.*`
   (np. `ZamNag`, `KntKarty`). Nie używaj polskich nazw opisowych.

2. Utwórz plik roboczy:
   ```
   solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql
   ```

3. Przy wznawianiu — przeczytaj pliki zanim wykonasz zapytanie.

### Forbidden

- Nie zaczynaj SQL przed zakończeniem Inicjalizacji.
- Nie używaj `CREATE VIEW` w brudnopisie — tylko `SELECT`.

### Exit gate

PASS jeśli plik roboczy istnieje.

---

## Faza 0 — Discovery

**Owner:** ERP Specialist

### Purpose

Zrozumieć dane przed napisaniem kodu. Nie zgadywać.

### Steps

1. Poznaj strukturę tabeli (`SELECT TOP 1 *`).
   Dla każdego klucza obcego — sprawdź etykietę przez `docs_search.py`.

2. Ustal baseline row count (`COUNT(*), COUNT(DISTINCT GIDNumer)`).

3. Zbadaj enumeracje:
   - `GROUP BY pole` w bazie
   - `solutions/reference/obiekty.tsv` (280+ typów GID)
   - `docs_search.py` w dokumentacji
   - CASE musi pokrywać wartości z bazy ORAZ dokumentacji.

4. Zidentyfikuj typy pól datowych.
   → Zobacz `ERP_SCHEMA_PATTERNS.md` sekcja "Konwersja dat Clarion".

5. Weryfikacja numerów dokumentów:
   - Sprawdź `solutions/reference/numeracja_wzorce.tsv`
   - Nieznany format → eskaluj do usera
   → Zobacz `ERP_SCHEMA_PATTERNS.md` sekcja "Numeracja dokumentów".

6. Zbadaj klucze obce bez oczywistej tabeli:
   - `INFORMATION_SCHEMA.COLUMNS`
   - Zakres wartości w `CDN.Obiekty`
   - JOIN testowy (100% dopasowań = silny dowód)

7. Sprawdź JOINy przez COUNT (czy mnożą wiersze).

### Forbidden

- Nie zakładaj typów bez weryfikacji MIN/MAX.
- Nie wpisuj enumeracji bez potwierdzenia.
- Nie pisz numeracji bez formatu od usera.

### Exit gate

PASS jeśli: baseline ustalony, typy dat zidentyfikowane, enumeracje zbadane.

### Po fazie

```
py tools/agent_bus_cli.py log --role erp_specialist --content-file tmp/log_faza0.md
```

---

## Faza 1 — Plan mapowania

**Owner:** ERP Specialist (tworzy) → Analityk (recenzuje)

### Purpose

Zatwierdzony plan kolumn przed napisaniem SQL.

### Faza 1a — Tworzenie planu (ERP Specialist)

1. Dla każdej kolumny pobierz opis z dokumentacji (`docs_search.py`).

2. Dla każdej kolumny zadaj pytania:
   - Klucz obcy? → sprowadź kod + nazwa
   - Enumeracja/flaga? → CASE z dokumentacji i bazy
   - Data? → konwersja Clarion (patrz `ERP_SCHEMA_PATTERNS.md`)
   - GIDFirma/GIDLp? → pomijamy
   - GIDNumer? → zachowaj jako `ID_[encja]`

3. Zasada pominięcia — TYLKO:
   - `COUNT(DISTINCT) = 1`
   - Dokumentacja: "nieużywane"
   - Dane wrażliwe (PESEL, rachunek bankowy)
   - GIDFirma, GIDLp

4. Generuj plan Excel (`excel_export.py`).
   Kolumny: `CDN_Pole`, `Opis`, `Alias_w_widoku`, `Transformacja`, `Uwzglednic`, `Komentarz_Analityka`.

5. Wyślij plan do Analityka (`agent_bus send`).

### Faza 1b — Recenzja planu (Analityk)

1. Odczytaj plan (`excel_read_rows.py`).

2. Weryfikacja konwencji:
   - Dane wrażliwe wykluczene
   - GID: Firma pominięta, Numer zachowany
   - Flagi/enumeracje: CASE z ELSE
   - Klucze obce: ID + nazwa/kod
   - Pominięcia uzasadnione

3. Feedback do ERP Specialist. Iteruj aż zatwierdzenie.

### Exit gate

PASS jeśli: plan istnieje, Analityk zatwierdził.

---

## Faza 2 — SQL na brudnopisie

**Owner:** ERP Specialist

### Purpose

Iteracyjne budowanie SELECT w pliku roboczym.

### Steps

1. Przeskanuj plan pod kątem niespójności PRZED SQL.

2. Generuj SQL w brudnopisie:
   - Nie wrzucaj długich SELECT do czatu
   - Edytuj plik → eksportuj → weryfikuj

3. Po każdej zmianie — eksport:
   ```
   py tools/sql_query.py --file "...draft.sql" --export "...export.xlsx"
   ```

4. Zasady SQL:
   - Kolumny: PascalCase, polskie (`Data_Wystawienia`)
   - Klucz główny: `ID_[encja]`
   - WHERE: tylko warunki techniczne
   → Zobacz `ERP_SCHEMA_PATTERNS.md` dla wzorców konwersji.

5. Ograniczenia konta CEiM_BI:
   → Zobacz `ERP_SQL_SYNTAX.md` sekcja "Wbudowane funkcje".

### Self-check

- [ ] Dane wrażliwe wykluczone
- [ ] GID: Firma pominięta, Numer zachowany
- [ ] Flagi/enumeracje: CASE z ELSE
- [ ] Daty: konwersja Clarion, 0 → NULL
- [ ] JOINy: nie mnożą wierszy
- [ ] Eksport istnieje

### Exit gate

PASS jeśli: brudnopis bez błędów, eksport aktualny, self-check zaliczony.

---

## Faza 3 — Weryfikacja eksportu

**Owner:** ERP Specialist

### Steps

1. Uruchom `bi_verify.py` (na końcu etapu lub przy dużych zmianach).

2. Sprawdź: row count, daty, enumeracje, metryki.

3. Wyślij eksport + bi_verify output do Analityka.

### Exit gate

PASS jeśli: eksport aktualny, row count zgadza się, Analityk potwierdził.

---

## Faza 4 — Zapis i wdrożenie

**Owner:** ERP Specialist → DBA → ERP Specialist

### Steps

1. Zapisz widok (`solutions_save_view.py`).

2. Zgłoś do DBA (`agent_bus flag`).

3. Po wdrożeniu — zaktualizuj katalog (`bi_catalog_add.py`).

4. Uzupełnij ręcznie: `description`, `example_questions`.

5. Commit + push (`git_commit.py`).

6. Zamknij backlog, oznacz flagę DBA, log sesji.

### Forbidden

- Nie uruchamiaj `bi_catalog_add.py` przed wdrożeniem DBA.
- Nie commituj bez wdrożenia.

### Exit gate

PASS jeśli: widok wdrożony, katalog zaktualizowany, commit wykonany.

---

## Progress log

Na końcu każdej fazy:
```
py tools/agent_bus_cli.py log --role erp_specialist --content-file tmp/log_faza_X.md
```

Zakres: tabela główna, baseline, JOINy, enumeracje, następny krok.

---

## Kiedy eskalować

- Enumeracja nieznana (brak w CDN.Obiekty i dokumentacji)
- Numery dokumentów — format nieznany
- Row count nie zgadza się
- 5 wymian z Analitykiem bez porozumienia

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 3.0 | 2026-03-24 | Refaktor: wyciągnięcie domeny do related_docs, usunięcie duplikacji snippetów SQL, nowy styl (proces-focused) |
| 2.0 | 2026-03-24 | Dodanie YAML header, Outline |
| 1.0 | legacy | Oryginalna wersja |
