# ERP — Workflow tworzenia widoków BI

Widoki BI tworzone są w schemacie `BI` przez konto DBA i udostępniane kontu `CEiM_BI`.
Tworzenie widoku to operacja złożona — wymaga fazy discovery, zatwierdzonego planu
i iteracyjnej pracy na pliku roboczym.

---

## Nazewnictwo widoków

**`{NazwaWidoku}` = nazwa tabeli źródłowej bez prefixu CDN.**

Przykłady: `ZamNag` (z CDN.ZamNag), `KntKarty` (z CDN.KntKarty), `Rezerwacje` (z CDN.Rezerwacje).

Dotyczy: katalogu widoku, plików roboczych, pliku SQL w views/, wpisu w catalog.json (`BI.NazwaWidoku`).
Nigdy nie używaj polskich nazw opisowych (`Zamowienia`, `Kontrahenci`).

---

## Inicjalizacja — przed jakimkolwiek zapytaniem

Utwórz dwa pliki robocze (jeśli nie istnieją):

```
solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql          ← brudnopis SELECT (nie CREATE VIEW)
solutions/bi/{NazwaWidoku}/{NazwaWidoku}_progress.md  ← log postępu
```

**Przy wznawianiu pracy** po przerwie lub kompresji kontekstu — zacznij od przeczytania
obu plików zanim wykonasz jakiekolwiek zapytanie.

---

## Faza 0 — Discovery

Wykonaj przed napisaniem jakiegokolwiek kodu. Cel: zrozumieć dane, nie zgadywać.

### a) Poznaj strukturę tabeli

```sql
SELECT TOP 1 * FROM CDN.MainTable
```

Dla każdego klucza obcego w tabeli głównej — zanim napiszesz JOIN — sprawdź etykietę tabeli docelowej w docs.db:

```
python tools/docs_search.py "" --table CDN.PotencjalnaTabela
```

Etykieta tabeli (`table_label`) często jednoznacznie wskazuje przeznaczenie (np. "Grupy_Główne_Kart_Kontrachentów" vs "Grupy_Kart_Kontrachentów"). Nie polegaj wyłącznie na nazwie kolumny klucza.

### b) Ustal baseline row count

```sql
SELECT COUNT(*), COUNT(DISTINCT GIDNumer) FROM CDN.MainTable
WHERE <filtr techniczny>
```

Ten count musi zgadzać się z wynikiem końcowego SELECT.
Jeśli po dodaniu JOINów jest więcej — JOIN mnoży wiersze.

### c) Zbadaj enumeracje — baza i dokumentacja razem

Pobierz WSZYSTKIE unikalne wartości pola:

```sql
SELECT pole, COUNT(*) cnt FROM CDN.MainTable GROUP BY pole ORDER BY cnt DESC
```

Skrzyżuj wszystkie znalezione wartości z CDN.Obiekty jednym zapytaniem:

```sql
SELECT OB_GIDTyp, OB_Nazwa, OB_Skrot
FROM CDN.Obiekty
WHERE OB_GIDTyp IN (<wszystkie DISTINCT wartości>)
```

Następnie sprawdź dokumentację:

```
python tools/docs_search.py "nazwa_pola" --table CDN.MainTable
```

**CASE musi pokrywać wartości z bazy ORAZ wartości wymienione w dokumentacji** — nawet
jeśli w bieżących danych nie występują. Jutro mogą się pojawić.

Jeśli wartość nie ma odpowiednika ani w CDN.Obiekty ani w dokumentacji — eskaluj do usera
z surówką (ile rekordów, jakie charakterystyczne pola) zanim wpiszesz etykietę. Nie zgaduj.

### d) Zidentyfikuj typ pól datowych

```sql
SELECT MIN(col_data), MAX(col_data) FROM CDN.MainTable WHERE col_data > 0
```

- ~70000–100000 → Clarion DATE (`DATEADD(d, col, '18001228')`)
- ~10^9 → Clarion TIMESTAMP (`DATEADD(ss, col, '1990-01-01')`)
- format daty → SQL DATE (bez konwersji)

Patrz `ERP_SCHEMA_PATTERNS.md` — wzorce inline.

### e) Weryfikacja numerów dokumentów — dwuetapowa eskalacja

**Krok 1 — zbierz wszystkie podtypy z tabeli źródłowej:**

```sql
SELECT TypPole, COUNT(*) cnt FROM CDN.MainTable GROUP BY TypPole ORDER BY cnt DESC
```

Nie zakładaj jednorodności — ta sama tabela może zawierać dokumenty różnych typów
z różnymi formatami numerów. Uruchom przez `sql_query.py`, przejrzyj wynik.

**Krok 2 — skompiluj jedno zapytanie obejmujące WSZYSTKIE znalezione podtypy:**

```sql
USE [ERPXL_CEIM];
GO

SELECT NumerERP, TypDok, [pola do ręcznej weryfikacji]
FROM (
    SELECT
        [CDN].[NazwaObiektu](TypPole, NumerPole, 0, 2) AS NumerERP,
        TypPole AS TypDok,
        [pola],
        ROW_NUMBER() OVER (PARTITION BY TypPole ORDER BY NumerPole DESC) AS rn
    FROM [CDN].[MainTable]
) x
WHERE rn = 1
ORDER BY TypDok;
```

Jedno zapytanie — po jednym przykładzie na każdy podtyp. Nie wracaj z częściowymi pytaniami.

**Od razu po odczycie podtypów skompiluj też zapytanie weryfikacyjne** porównujące
NumerSystemowy (z CDN.NazwaObiektu) vs NumerInline (Twoja formuła):

```sql
SELECT TOP 20
    [CDN].[NazwaObiektu](TypPole, NumerPole, 0, 2) AS NumerERP,
    <Twoja formuła inline>                          AS NumerInline,
    CASE WHEN <inline> = [CDN].[NazwaObiektu](...) THEN 'OK' ELSE 'ROZNI SIE' END AS Status
FROM CDN.MainTable
```

Przekaż oba pliki userowi razem — jedna runda zamiast dwóch.

**Zapisz zapytanie do pliku przed przekazaniem userowi:**

```
solutions/bi/{NazwaWidoku}/{NazwaWidoku}_objects.sql
```

Dopiero potem przekaż ścieżkę do pliku userowi z prośbą o uruchomienie w SSMS.
User może plik otworzyć, skopiować i wrócić z wynikiem.
Nie pisz numeracji dokumentów dopóki user nie wróci z wynikiem.

### f) Sprawdź JOINy przez COUNT

Dodawaj JOINy jeden po drugim i sprawdzaj COUNT po każdym:

```sql
SELECT COUNT(*), COUNT(DISTINCT r.GIDNumer) FROM ... LEFT JOIN CDN.XXX ON ...
-- Jeśli COUNT(*) > COUNT(DISTINCT) → JOIN mnoży wiersze → dodaj warunek zawężający
```

### Po zakończeniu Fazy 0 — zapisz postępy

Zaktualizuj `solutions/bi/{NazwaWidoku}/{NazwaWidoku}_progress.md` (patrz sekcja
"Zarządzanie kontekstem" na końcu tego dokumentu).

---

## Faza 1 — Plan mapowania (Excel, zatwierdzenie przez usera)

### Format planu

Plan to plik Excel — nie MD. Agent konstruuje tabelę mapowania jako SQL z hardkodowanymi
wartościami (UNION ALL) i eksportuje przez `excel_export.py` ze stałą ścieżką:

```bash
python tools/excel_export.py "SELECT ..." \
  --output "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx"
```

Plik jest nadpisywany przy każdej aktualizacji planu — stała ścieżka bez timestampu.

### Wymagana zawartość planu

Jedna tabela z kolumnami:

| Kolumna | Źródło | Opis |
|---|---|---|
| `Kolejnosc` | agent | numer kolejny z oryginalnej tabeli (z SELECT TOP 1 *) |
| `CDN_Pole` | agent | oryginalna nazwa kolumny z CDN lub tabeli JOIN |
| `Opis_w_dokumentacji` | docs_search.py | col_label + description z docs.db; puste gdy brak w indeksie |
| `Przykladowe_wartosci` | docs_search.py | sample_values z docs.db; puste gdy brak |
| `Alias_w_widoku` | agent | docelowa nazwa w widoku BI (propozycja) |
| `Transformacja` | agent | co robimy z polem (opis lub formuła) |
| `Uwzglednic` | agent | Tak / Nie (propozycja) |
| `Uzasadnienie` | agent | po co to pole lub dlaczego pominięte |
| `Komentarz_Usera` | **user** | pusta kolumna — user wpisuje uwagi przed zatwierdzeniem |

Kolejność wierszy: wszystkie kolumny CDN.MainTable w kolejności z `SELECT TOP 1 *`,
następnie kolumny sprowadzane przez JOINy (bezpośrednio po kluczu który je sprowadza),
na końcu metryki obliczeniowe.

### Jak agent wypełnia Opis_w_dokumentacji i Przykladowe_wartosci

Dla każdej kolumny CDN.MainTable uruchom:

```
python tools/docs_search.py "{nazwa_kolumny}" --table CDN.MainTable --limit 1
```

Z wyniku pobierz:
- `col_label` → `Opis_w_dokumentacji` (etykieta z dokumentacji, **nie nazwa kolumny CDN**)
- `sample_values` → `Przykladowe_wartosci`

Gdy brak wyniku — zostaw puste. **Nigdy nie wpisuj `col_name` jako opisu** — to jest pole
techniczne, nie czytelny opis. Puste pole jest lepsze niż mylące.

Możesz zebrać wszystkie kolumny jednym wywołaniem bez frazy, z filtrem tabeli:

```
python tools/docs_search.py "" --table CDN.MainTable
```

### Odczyt planu po edycji usera

Po tym jak user edytuje `{NazwaWidoku}_plan.xlsx` (uzupełni `Komentarz_Usera`, zmieni
`Uwzglednic` lub `Transformacja`) — odczytaj zmiany:

```
python tools/excel_read_rows.py \
  --file "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx" \
  --columns CDN_Pole,Uwzglednic,Komentarz_Usera
```

Pełne kolumny (`Transformacja`, `Uzasadnienie`) — tylko dla wierszy które tego wymagają.

**Zanim zaczniesz generować SQL — najpierw przeskanuj plan pod kątem niespójności.**

Wypisz wszystkie wiersze spełniające którykolwiek z warunków:
- `Komentarz_Usera` jest wypełniony
- `Uwzglednic` = "Nie" przy niepustym `Komentarz_Usera` (potencjalna sprzeczność)
- `Transformacja` wygląda na niekompletną lub wymaga interpretacji

Przedstaw je userowi jako listę do rozstrzygnięcia:

```
Zanim zacznę — znalazłem N wierszy wymagających uwagi:
- [CDN_Pole]: Komentarz_Usera = "...", Uwzglednic = "..."
- ...
Czy mam zastosować komentarze dosłownie, czy wolisz najpierw omówić?
```

Dopiero po potwierdzeniu usera przystąp do generowania SQL.

### Metodologia — analiza kolumna po kolumnie

Przejdź przez **każdą** kolumnę CDN.MainTable. Dla każdej zadaj sobie kolejno pytania:

1. **Klucz obcy?** (GIDNumer, Numer, ID, Typ) → sprawdź CDN.Obiekty lub docelową tabelę,
   sprowadź opisowe dane (kod + nazwa). Zachowaj też ID — przydatne do debugowania.
2. **Enumeracja lub flaga?** → sprawdź dokumentację i bazę, zbuduj pełny CASE
   zgodnie z zasadami tłumaczenia wartości poniżej.
3. **Data?** → zidentyfikuj typ Clarion, zastosuj odpowiednią konwersję inline.
4. **Pole opisowe?** (Opis, Nazwa, Kod, Uwagi) → bez zmian, uwzględnij.
5. **Komponenty GID?** → stosuj regułę:
   - `GIDFirma` → **pomijamy**
   - `GIDTyp`   → **tłumaczymy** przez CASE (typ obiektu ERP — niesie sens biznesowy)
   - `GIDNumer` → **zostawiamy** (klucz do ad-hoc zapytań i JOINów)
   - `GIDLp`    → **pomijamy**
6. **Pole Typ_Dok / typ dokumentu?** → domyślnie **pełna nazwa**, nie skrót.
   Widok BI służy też osobom spoza systemu — `'Faktura sprzedaży'` zamiast `'FS'`.
   Zapisz w planie od razu jako pełną nazwę — nie poprawiaj po feedbacku usera.
7. **Inne pole techniczne?** (GUID, TStamp) → domyślnie uwzględnij
   z adnotacją "techniczne". Pomiń tylko gdy wartość jest stałą dla całej tabeli
   i nie niesie żadnej informacji (udowodnij przez COUNT DISTINCT = 1).

**Zasada pominięcia** — pole można pominąć TYLKO gdy spełniony jeden z warunków:
1. SELECT DISTINCT zwraca dokładnie 1 wartość dla całej tabeli (udowodnione przez COUNT)
2. Dokumentacja wprost mówi "pole nie jest obsługiwane" lub "nieużywane"
3. Dane wrażliwe (hasła, PINy)
4. Czyste komponenty GID (GIDTyp/GIDFirma/GIDLp) bez żadnej informacji biznesowej

W każdym innym przypadku — uwzględnij. Rzadko wypełnione, nieznane zastosowanie,
mała wartość analityczna — to NIE są powody do pominięcia. Power BI odfiltruje
co user nie potrzebuje; brak kolumny w widoku blokuje analizę.

### Zatwierdzenie

Pokaż userowi ścieżkę do pliku Excel i czekaj na zatwierdzenie.
**Nie pisz SQL dopóki user nie zatwierdzi planu.**

Po zatwierdzeniu — zaktualizuj progress log.

---

## Faza 2 — SQL na pliku brudnopisu (iteracja)

**Cały SQL powstaje i żyje w pliku `solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql`.**

- Nie wrzucaj długich SELECT-ów do czatu
- Edytuj plik → eksportuj → weryfikuj → powtarzaj
- W czacie podawaj tylko: co zmieniłeś i jaki jest wynik weryfikacji

### Obowiązkowy eksport po każdej zmianie

Każde wywołanie testujące brudnopis musi zawierać `--export`. Jeden krok = test + Excel.

```bash
python tools/sql_query.py --file "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql" \
  --export "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
```

Plik eksportu nadpisywany in-place (stała ścieżka bez timestampu). User zawsze widzi
aktualny wynik bez konieczności osobnego proszenia o eksport.

Plik brudnopisu zawiera `SELECT` (nie `CREATE VIEW`). Widok powstaje dopiero po akceptacji
usera w Fazie 4.

### Zasady nazewnictwa

- Widok: `BI.Rezerwacje`, `BI.Zamowienia` (rzeczownik mnogi, PascalCase)
- Kolumny: `Kod_Towaru`, `Data_Realizacji`, `ID_Rezerwacji` (underscore, opisowe)
- Klucz główny: `ID_[encja]` (np. `ID_Rezerwacji`)
- Dla każdego lookup: kod + nazwa (np. `Kod_Magazynu` + `Nazwa_Magazynu`)

### Brak WHERE z logiką biznesową

Widoki BI zwracają pełne zbiory — filtrowanie wykonuje bot/Power BI:

```sql
-- Poprawnie — tylko wykluczenie rekordów technicznych:
WHERE r.Rez_TwrNumer > 0

-- Błędnie — ogranicza Power BI:
WHERE r.Rez_Aktywna = 1
```

### Kolejność kolumn

Odwzorowuj kolejność z tabeli źródłowej (`SELECT TOP 1 *`). Kolumny z JOINów wstawiaj
bezpośrednio po kluczu który je sprowadza. Metryki obliczeniowe na końcu.

### Ograniczenia CEiM_BI

- Brak EXECUTE na funkcje CDN (error 229)
- Wszystkie konwersje i numery dokumentów muszą być inline
- SELECT tylko na `BI.*` — CDN przez widok

---

## Zasady tłumaczenia wartości

### Flagi 0/1

Zawsze tłumacz w kontekście biznesowym. Nigdy nie zostawiaj surowej liczby w widoku BI.

```sql
-- Nie:
Rez_Aktywna

-- Tak:
CASE Rez_Aktywna WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie' ELSE 'Nieznane' END AS Aktywna
```

Dobieraj etykiety do kontekstu: 'Tak'/'Nie', 'Aktywna'/'Nieaktywna', 'Zatwierdzone'/'Niezatwierdzone' itp.

### Enumeracje i typy dokumentów

```sql
CASE pole
    WHEN 960  THEN 'Zamówienie'
    WHEN 1152 THEN 'ZZ'
    WHEN 1280 THEN 'ZS'
    -- wartości z dokumentacji, nawet jeśli nie ma ich w bazie:
    WHEN 2592 THEN 'Rezerwacja u dostawcy'
    ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')'  -- ZAWSZE fallback z surową wartością
END
```

**ELSE z surową wartością jest obowiązkowy.** Nigdy nie zostawiaj ELSE bez gałęzi —
milczące NULL ukrywa nieznane typy zamiast je ujawniać.

### Klucze obce

Nie zostawiaj samego ID gdy możliwa jest dekodifikacja. Dla każdego klucza obcego:
- Dodaj JOIN do docelowej tabeli
- Sprowadź przynajmniej kod + nazwę
- Zachowaj ID (dla debugowania)

### Pola numeryczne = brak

```sql
CASE WHEN Rez_DstNumer = 0 THEN NULL ELSE Rez_DstNumer END AS ID_Dostawy
```

---

## Faza 3 — Export i weryfikacja (po każdej iteracji SQL)

### bi_verify vs sql_query

- `bi_verify`: tylko na końcu etapu lub gdy zmiana dotyka wielu kolumn/JOINów
- `sql_query`: przy drobnej poprawce (1 kolumna, literówka) — bez pełnych statystyk

```bash
python tools/excel_export_bi.py \
  --sql "$(cat solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql)" \
  --view-name "{NazwaWidoku}" \
  --source-table "CDN.MainTable" \
  --plan "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx"
```

Następnie statystyki:

```bash
python tools/excel_read_stats.py \
  --file "exports/{NazwaWidoku}_TIMESTAMP.xlsx" \
  --sheet "Wynik" \
  --max-unique 15
```

### Weryfikacja wyników

- **Row count**: musi równać się `COUNT(*)` z bazy z tego samego SQL.
  Różnica → zbadaj JOINy (nie zakładaj "dane się zmieniły").
- Daty: czy wyglądają jak daty (nie surowe liczby Clarion)
- Enumeracje: czy `distinct` ≤ oczekiwana liczba typów, czy etykiety sensowne
- Metryki: czy wartości w rozsądnym zakresie

**Artefakt wyścigu czasowego:** kilka NULLi w kolumnie Nr_Dok przy eksporcie z bazy produkcyjnej
to normalne — nowe rekordy dodane między zapytaniem a eksportem, nie błąd SQL.
Weryfikacja: `SELECT ... WHERE COALESCE(Nr_Dok, '') = ''` zwróci 0 gdy SQL jest poprawny.

**sql_query blokuje CREATE OR ALTER VIEW:** `sql_query.py` odrzuca słowo `CREATE` —
walidacja widoku możliwa tylko na brudnopisie (sam SELECT). Nigdy nie porzucaj brudnopisu
przed Fazą 4 — jest jedynym plikiem który można przetestować bez DBA.

---

## Faza 4 — Zapis i commit (po akceptacji usera)

```sql
CREATE OR ALTER VIEW BI.NazwaWidoku AS
<SELECT z brudnopisu>
```

Zapisz do `solutions/bi/views/NazwaWidoku.sql`, zaktualizuj `solutions/bi/catalog.json`:

```json
{
  "name": "BI.NazwaWidoku",
  "file": "views/NazwaWidoku.sql",
  "description": "...",
  "primary_table": "CDN.XXX",
  "joins": ["CDN.YYY"],
  "columns": ["ID_Encji", "Kolumna1"],
  "notes": "Wskazówki: wartości kodowane, warunki filtrowania dla bota"
}
```

```bash
git add solutions/bi/
git commit -m "feat: widok BI.[NazwaWidoku] — opis"
git push
```

---

## Zarządzanie kontekstem — progress log widoku

Plik `solutions/bi/{NazwaWidoku}/{NazwaWidoku}_progress.md` jest kołem ratunkowym przy kompresji
kontekstu. Aktualizuj go obligatoryjnie na końcu każdej fazy.

Minimalny zakres po każdej fazie:

```markdown
## Status: [Faza X — nazwa]

**Tabela główna:** CDN.XXX, N rekordów, filtr: `warunek`

**Baseline:** COUNT(*) = N, COUNT(DISTINCT) = N ✓

**JOINy ustalone:**
- CDN.YYY — LEFT JOIN na kluczu ZZZ — uzasadnienie

**Enumeracje rozkodowane:**
- Pole_A: 1='Etykieta1', 0='Etykieta2' (źródło: dokumentacja/CDN.Obiekty)
- Pole_B: 960='Zamówienie', 14346='ZPZ' (zweryfikowane)

**Numery dokumentów:**
- [CZEKA NA ODPOWIEDŹ USERA: SELECT z CDN.NazwaObiektu przekazany]
  LUB
- [ZWERYFIKOWANE: ZS format ZS-N/MM/RRRR/Seria]

**Pliki:**
- Brudnopis: solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql
- Plan: solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx
- Ostatni export: solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx

**Następny krok:** [konkretna czynność]
```

---

## Ochrona dokumentacji agenta

Pliki `documents/erp_specialist/*.md` opisują zweryfikowane wzorce.

**Nie modyfikuj tych plików w trakcie pracy nad widokiem** bez:
1. Twardego dowodu: wynik SELECT z bazy lub jawne potwierdzenie usera
2. Eskalacji do usera z propozycją zmiany

Jeśli zauważysz potencjalną nieścisłość w dokumentacji — zanotuj w progress logu widoku
i zgłoś userowi po zakończeniu bieżącego zadania. Nie poprawiaj w trakcie.

---

## Kiedy eskalować do usera

- Wartość enumeracji nieznana (brak w CDN.Obiekty i dokumentacji) — podaj surówkę
- Numery dokumentów — zawsze jednorazowe zapytanie zbiorcze przed pisaniem SQL
- Row count z exportu ≠ COUNT z bazy — zbadaj i wyjaśnij różnicę zanim pokażesz wyniki
- Wynik pusty lub dane wyglądają na błędne
- Potencjalna nieścisłość w dokumentacji agenta — zgłoś, nie poprawiaj samodzielnie
