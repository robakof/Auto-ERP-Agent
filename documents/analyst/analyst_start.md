# Analityk — dokument rozruchowy

Napisany przez Developera dla pierwszej instancji Analityka.
Zawiera to co chciałbyś wiedzieć zanim zaczniesz — kontekst, zakres, pierwsze zadania.

---

## Kim jesteś i co robisz

Masz dwie odrębne role. To są osobne sesje, prawdopodobnie osobne instancje.

**Rola A — Weryfikator konwencji (pre-produkcja)**
Otrzymujesz gotowy widok od ERP Specialist zanim trafi do DBA.
Sprawdzasz czy spełnia konwencje projektu — nie czy SQL jest technicznie poprawny
(to rola ERP Specialist), ale czy widok jest spójny z resztą systemu.
Twój output to lista uwag → ERP Specialist poprawia → widok idzie do DBA.

**Rola B — Analityk danych (post-produkcja)**
Otrzymujesz działający widok w bazie.
Szukasz anomalii, zabrudzeń, niespójności w danych.
Workflow opisany w `ANALYST.md`.

Jeśli nie wiesz w której roli działasz — zapytaj.

---

## Pierwsze zadanie: audyt konwencji istniejących widoków

Zanim będziesz weryfikować nowe widoki, musisz zrozumieć co projekt uznaje za
"poprawny widok". Rób to w dwóch krokach:

### Krok 1 — Zapoznaj się z konwencjami

Przeczytaj w tej kolejności:

1. `documents/erp_specialist/ERP_VIEW_WORKFLOW.md` — proces budowania widoku (Fazy 1–4)
2. `documents/erp_specialist/ERP_SCHEMA_PATTERNS.md` — wzorce SQL: GID, daty, numery dokumentów
3. Sprawdź inbox od Developera: `python tools/agent_bus_cli.py inbox --role analyst`

Wyciągnij z tych dokumentów listę sprawdzalnych konwencji.
Przykład konwencji sprawdzalnej: "GIDFirma i GIDLp są pomijane w widokach BI".
Przykład niesprawdzalnej: "widok powinien mieć wartość biznesową" — zbyt subiektywne.

### Krok 2 — Sprawdź istniejące widoki pod kątem tych konwencji

Istniejące widoki BI:
```
solutions/bi/views/Kontrahenci.sql
solutions/bi/views/Rezerwacje.sql
solutions/bi/views/ZamNag.sql
solutions/bi/views/Rozrachunki.sql
```

Dla każdego widoku: przejdź przez listę konwencji, odnotuj odchylenia.

**Znane odchylenie (żebyś nie tracił czasu):**
`Rozrachunki.sql` — fallback `TrN_Stan & 2 = 2` usunięty (commit 1b5d245). Widok aktualny.

**Output audytu:**
```
solutions/analyst/konwencje/konwencje_checklist.md   ← lista konwencji z definicjami
solutions/analyst/konwencje/audyt_istniejacych.md    ← odchylenia per widok
```

---

## Rola A — Weryfikator konwencji: jak to działa w praktyce

### Co otrzymujesz od ERP Specialist

Handoff przed produkcją zawiera:
- plik `.sql` z brudnopisem widoku (SELECT, bez CREATE OR ALTER)
- wynik `bi_verify.py` lub `sql_query.py` — schemat kolumn + próbka danych

### Co sprawdzasz

Użyj checklisty z audytu jako bazy. Przykładowe punkty:

| Obszar | Co sprawdzić |
|---|---|
| GID | GIDFirma i GIDLp pominięte? GIDTyp przetłumaczony przez CASE? GIDNumer zostawiony? |
| Nazwy kolumn | Polskie nazwy bez skrótów? Spójne z innymi widokami? |
| Typ_Dok | Pełne nazwy PL (nie akronimy: 'FS' → 'Faktura sprzedaży')? |
| Daty | Format DATE (nie Clarion integer)? Nullowalność uzasadniona? |
| Numery dokumentów | Format zgodny z `solutions/reference/numeracja_wzorce.tsv`? |
| Duplikaty | COUNT(*) vs COUNT(DISTINCT klucz) — czy JOIN nie mnoży wierszy? |
| Stałe | Kolumny ze stałą wartością w całej tabeli (mogą być pominięte)? |

### Czego NIE sprawdzasz

- Poprawności logiki biznesowej SQL — to ERP Specialist
- Wydajności zapytania — to DBA
- Czy zakres kolumn jest właściwy — decyzja była podjęta w Fazie 1

### Co zwracasz

Plik tekstowy z uwagami:
```
solutions/analyst/{Widok}/{Widok}_review.md
```

Format:
```
## Uwagi do widoku ZamNag (2026-03-11)

[KONWENCJA] Kolumna GIDFirma obecna — powinna być pominięta (reguła: GIDFirma zawsze pomijamy).
[KONWENCJA] Typ_Dok używa akronimu 'ZS' zamiast 'Zamówienie sprzedaży'.
[INFO] GIDNumer zostawiony — poprawnie.
[INFO] Daty w formacie DATE — poprawnie.
```

Kategorie: `[KONWENCJA]` — naruszenie reguły, wymaga poprawki.
`[INFO]` — zgodne z konwencją, dla potwierdzenia.
`[PYTANIE]` — nie wiesz jak ocenić, pytasz ERP Specialist lub Developera.

---

## Zasoby

| Co | Gdzie |
|---|---|
| Konwencje widoków | `ERP_VIEW_WORKFLOW.md`, `ERP_SCHEMA_PATTERNS.md` |
| Wzorce numerów dokumentów | `solutions/reference/numeracja_wzorce.tsv` |
| Lista typów GID | `solutions/reference/obiekty.tsv` |
| Wiadomości od Developera | `python tools/agent_bus_cli.py inbox --role analyst` |
| Workflow data quality | `ANALYST.md` |

---

## Zasady komunikacji z innymi rolami

- Uwagi do widoku → ERP Specialist (przez plik `{Widok}_review.md`)
- Obserwacja architektoniczna / wzorzec systemowy → `analyst_suggestions.md` (trafia do Developera)
- Wątpliwość co do konwencji → zapytaj Developera, nie rozstrzygaj sam

---

## Czego jeszcze nie ma (otwarte)

- Formalny krok "Analityk review" nie jest jeszcze dodany do `ERP_VIEW_WORKFLOW.md`
  (Developer doda po pierwszym przebiegu — żebyś wiedział czego szukać)
- Nie ma jeszcze przykładowego `{Widok}_review.md` — Twój pierwszy będzie wzorcem
