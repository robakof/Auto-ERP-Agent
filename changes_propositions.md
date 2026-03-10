# Plan widoków BI — faza testowa

Cel: zbudować minimalny zestaw widoków BI do przetestowania pipeline bota (NLP → SQL → odpowiedź).
Istniejący widok: `BI.Rezerwacje` (wzorzec jakości).

---

## Kolejność implementacji

### 1. BI.Kontrahenci

**Priorytet:** pierwszy — referencyjny, przez niego przechodzą wszystkie kolejne widoki.

Zakres:
- Kartoteka kontrahentów (KntKarty) — dane podstawowe, adresowe, NIP, akronim
- Opcjonalnie: typ kontrahenta (klient / dostawca / oba), grupa kontrahentów

Przykładowe pytania bota:
- "Podaj dane kontrahenta Bolsius"
- "Jaki NIP ma firma X?"
- "Którzy kontrahenci są jednocześnie klientami i dostawcami?"

---

### 2. BI.Zamowienia

**Priorytet:** drugi — kluczowy operacyjnie, pokrywa najczęstsze pytania.

Zakres:
- Nagłówki zamówień (ZamNag): ZS (sprzedaż) + ZZ (zakup)
- Elementy zamówień (ZamElem): pozycje, ilości, ceny
- JOIN: KntKarty (kontrahent), TwrKarty (towar)
- Daty: złożenia, planowanej realizacji, planowanej dostawy (Clarion → SQL)
- Status zamówienia: czy otwarte, w realizacji, zamknięte
- Link do dokumentów handlowych: czy wystawiona FZ/FS (JOIN TraNag lub podzapytanie)
- Status WMS (kolektory, pakowanie): zbadać w discovery jakie tabele — może być kolumna lub pominięte jeśli brak danych

Przykładowe pytania bota:
- "Kiedy przyjedzie zamówienie od Bolsiusa?"
- "Jakie ZS są otwarte dla kontrahenta X?"
- "Czy do zamówienia ZS-5/03/26 jest już wystawiona faktura?"
- "Ile zamówień zakupu jest niezrealizowanych?"

---

### 3. BI.Rozrachunki

**Priorytet:** trzeci — wysokowartościowe operacyjnie, wymaga rozkodowania schematu CDN.

Zakres:
- Należności i zobowiązania (CDN.TraPlat lub CDN.ZobNag/ZobElem — ustalić w discovery)
- Stan rozliczenia: kwota, zapłacono, pozostało
- Przeterminowanie: data wymagalności vs dziś
- JOIN: KntKarty (kontrahent), TraNag (dokument źródłowy)

Przykładowe pytania bota:
- "Ile zalega nam kontrahent X?"
- "Które płatności są przeterminowane?"
- "W jakim stopniu zapłacił X za fakturę FS-12?"
- "Jakie mamy zobowiązania wobec dostawcy Y?"

Uwaga: schemat rozrachunków ERP XL może być nietrywialny — discovery krytyczne przed SQL.

---

### 4. BI.DokumentyHandlowe (Tier 2 — po teście bota)

**Priorytet:** czwarty — po weryfikacji że pipeline bota działa na widokach 1-3.

Zakres:
- Nagłówki dokumentów (TraNag): FS, FZ, WZ, PZ i inne
- Elementy (TraElem): pozycje, ilości, ceny
- JOIN: KntKarty, TwrKarty
- Typy dokumentów: rozkodowane etykiety (nie surowe GIDTyp)

Przykładowe pytania bota:
- "Jakie faktury wystawiliśmy dla X w tym miesiącu?"
- "Historia sprzedaży towaru Y"
- "Kiedy ostatnio kupiliśmy od dostawcy Z?"

---

---

## Zadania developerskie (przed lub równolegle z widokami)

Obserwacje z sesji BI.Kontrahenci — priorytetyzowane według zwrotu z kontekstu:

| # | Zadanie | Plik | Zmiana |
|---|---------|------|--------|
| P1 | `--file SCIEZKA.sql` w `excel_export_bi.py` | `tools/excel_export_bi.py` + testy | Eliminuje `$(cat ...)` w bashu — duży SQL nie przechodzi przez kontekst |
| P2 | `--count-only` w `sql_query.py` | `tools/sql_query.py` + testy | Zamiast 5.8 MB JSON zwraca `{ok, row_count, columns[]}` |
| P2 | `--quiet` w `sql_query.py` | jw. | Stdout: `OK 4530` lub `ERROR: ...` — eliminuje ręczny parsing JSON w bashu |
| P3 | `bi_verify.py` — test + eksport + statystyki | `tools/bi_verify.py` + testy | 3 kroki → 1; baseline COUNT check z discovery |
| P4 | `solutions_save_view.py --draft PLIK --schema BI` | `tools/solutions_save_view.py` + testy | Zapis `CREATE OR ALTER VIEW BI.X AS <draft>` bez czytania treści |

Każde zadanie: TDD (testy → implementacja), dodać do CLAUDE.md po zaimplementowaniu.

### [Prompt] Przebudowa CLAUDE.md — 3 poziomy wywołania

CLAUDE.md wymaga przebudowy. Aktualnie miesza tryb agenta ERP z wzmianką o dev i metodologu.
Powinien:
- Jasno definiować 3 poziomy wywołania: Agent ERP / Developer / Metodolog
- Na wejściu rozpoznawać poziom i odsyłać do właściwej dokumentacji
- Na poziomie Agenta ERP: zawierać zakaz edycji plików dokumentacji bez jawnej zgody użytkownika
  (obserwacja błędu NIE jest wystarczającym uzasadnieniem do edycji)

Do zrobienia jako osobna sesja — wymaga przeprojektowania struktury, nie drobnej poprawki.

---

## Wzorzec jakości

Każdy widok budowany według `ERP_VIEW_WORKFLOW.md`:
- Discovery → plan Excel → zatwierdzenie → SQL → export → `CREATE OR ALTER VIEW BI.Nazwa`
- Katalog: wpis w `solutions/bi/catalog.json` z opisem, kolumnami, przykładowymi pytaniami
- Plik widoku: `solutions/bi/views/Nazwa.sql`
- Pliki robocze: `solutions/bi/Nazwa/` (draft, plan, export, progress)
