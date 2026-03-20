# Workflow: Tworzenie widoku BI

Kanoniczny dokument procesowy. Obowiązuje wszystkie role uczestniczące w tworzeniu widoku BI.

W runtime agent dostaje tylko sekcję swojej bieżącej fazy + `handoffs/bi_view_handoff_schema.md`.
Nie wczytuj całego dokumentu do promptu sesji.

**Statusy faz:** `PASS` | `BLOCKED` | `ESCALATE`
Faza kończy się wyłącznie jednym z tych statusów — nigdy "luźnym podsumowaniem".

---

## Inicjalizacja

**Owner:** ERP Specialist

### Steps

1. Ustal `{NazwaWidoku}` = nazwa tabeli źródłowej bez prefixu `CDN.*`
   (np. `ZamNag` z CDN.ZamNag, `KntKarty` z CDN.KntKarty)
   Nigdy nie używaj polskich nazw opisowych (`Zamowienia`, `Kontrahenci`).
2. Utwórz plik roboczy jeśli nie istnieje:
   ```
   solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql    ← brudnopis SELECT (nie CREATE VIEW)
   ```
3. Przy wznawianiu po przerwie — przeczytaj oba pliki zanim wykonasz jakiekolwiek zapytanie.

### Forbidden

- Nie zaczynaj pisać SQL przed zakończeniem Inicjalizacji.
- Nie twórz `CREATE VIEW` w brudnopisie — wyłącznie `SELECT`.

### Exit gate

PASS jeśli oba pliki robocze istnieją.

---

## Faza 0 — Discovery

**Owner:** ERP Specialist

### Purpose

Zrozumieć dane przed napisaniem kodu. Nie zgadywać.

### Steps

1. Poznaj strukturę tabeli:
   ```sql
   SELECT TOP 1 * FROM CDN.MainTable
   ```
   Dla każdego klucza obcego — sprawdź etykietę tabeli docelowej przez `docs_search.py "" --table CDN.PotencjalnaTabela` zanim napiszesz JOIN.

2. Ustal baseline row count:
   ```sql
   SELECT COUNT(*), COUNT(DISTINCT GIDNumer) FROM CDN.MainTable WHERE <filtr techniczny>
   ```
   Ten count musi zgadzać się z wynikiem końcowego SELECT. Więcej po JOINach = JOIN mnoży wiersze.

3. Zbadaj enumeracje — baza i dokumentacja razem:
   - Pobierz wszystkie unikalne wartości: `SELECT pole, COUNT(*) FROM CDN.MainTable GROUP BY pole`
   - Sprawdź `solutions/reference/obiekty.tsv` — pełna lista 280+ typów GID (symbol, nazwa, opis). Szybsze niż zapytanie do CDN.Obiekty.
   - Jeśli brak w obiekty.tsv: `SELECT OB_GIDTyp, OB_Nazwa FROM CDN.Obiekty WHERE OB_GIDTyp IN (...)`
   - Sprawdź dokumentację: `python tools/docs_search.py "nazwa_pola" --table CDN.MainTable`
   - CASE musi pokrywać wartości z bazy ORAZ z dokumentacji (mogą pojawić się jutro).
   - Nieznana wartość bez odpowiednika → ESCALATE do usera z surówką (ile rekordów, jakie pola).

4. Zidentyfikuj typ pól datowych:
   ```sql
   SELECT MIN(col), MAX(col) FROM CDN.MainTable WHERE col > 0
   ```
   - ~70 000–109 211 → Clarion DATE → `DATEADD(d, col, '18001228')` → alias `Data_XXX`
   - ~10^9 → Clarion TIMESTAMP → `DATEADD(ss, col, '1990-01-01')` → alias `DataCzas_XXX`
   - Format daty → SQL DATE (bez konwersji) → alias `Data_XXX`

5. Weryfikacja numerów dokumentów:
   - Krok 1: zbierz wszystkie podtypy z tabeli źródłowej (`GROUP BY TypPole`)
   - Krok 2: sprawdź `solutions/reference/numeracja_wzorce.tsv` — wzorce formatów dla TraNag (25 typów), ZamNag, ZP, NM, NO, UP, KB, RK. Jeśli wszystkie podtypy są tam — nie eskaluj do usera.
   - Krok 2b (jeśli podtyp brak w TSV): sprawdź `solutions/reference/obiekty.tsv` (kolumna `Ob_Skrot` dla danego GIDTypu) — jeśli skrót znany, użyj formatu `SKRÓT-Nr/MM/YY[/Seria]` przez analogię do istniejących wzorców. Nie eskaluj jeśli skrót wystarczy.
   - Krok 3 (tylko gdy skrót nieznany lub format niestandardowy): zapytanie z `CDN.NazwaObiektu(TypPole, NumerPole, 0, 2)` — po jednym przykładzie na każdy nieznany podtyp. Zapisz do `solutions/bi/{NazwaWidoku}/{NazwaWidoku}_objects.sql`, przekaż ścieżkę userowi.
   - Nie pisz numeracji dokumentów dopóki nie masz zweryfikowanego formatu (z TSV lub od usera)

6. Zbadaj klucze obce bez oczywistej tabeli docelowej:
   - `INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE 'POK_%'`
   - Zakres wartości w `CDN.Obiekty`
   - JOIN testowy — 100% dopasowań = silny dowód
   - Nie deklaruj "brak tabeli" bez przejścia przez wszystkie trzy kroki.

7. Sprawdź JOINy przez COUNT:
   ```sql
   SELECT COUNT(*), COUNT(DISTINCT GIDNumer) FROM ... LEFT JOIN CDN.XXX ON ...
   ```
   COUNT(*) > COUNT(DISTINCT) → JOIN mnoży wiersze → dodaj warunek zawężający.

### Forbidden

- Nie zakładaj typów kolumn bez weryfikacji MIN/MAX.
- Nie wpisuj wartości enumeracji bez potwierdzenia w CDN.Obiekty lub dokumentacji.
- Nie deklaruj braku tabeli referencyjnej bez przejścia przez 3 kroki.
- Nie pisz numeracji dokumentów bez wyniku od usera.

### Exit gate

PASS jeśli:
- Baseline row count ustalony.
- Typy wszystkich pól datowych zidentyfikowane.
- Enumeracje zbadane (baza + dokumentacja).
- Numery dokumentów: wynik od usera otrzymany LUB zapytanie przekazane i sesja czeka.
- Progress log zapisany do bazy.

BLOCKED jeśli którykolwiek warunek niespełniony — opisz brak w `missing_items`.

### Po fazie

```
python tools/agent_bus_cli.py log --role erp_specialist --content-file tmp/log_faza0.md
```

---

## Faza 1 — Plan mapowania

**Owner:** ERP Specialist (tworzy) → Analityk (recenzuje)

### Purpose

Zatwierdzony plan kolumn przed napisaniem SQL.

---

### Faza 1a — Tworzenie planu (ERP Specialist)

#### Steps

1. Dla każdej kolumny CDN.MainTable pobierz opis z dokumentacji:
   ```
   python tools/docs_search.py "" --table CDN.MainTable
   ```
   Z wyniku: `col_label` → `Opis_w_dokumentacji`, `sample_values` → `Przykladowe_wartosci`.
   Gdy brak → zostaw puste. Nigdy nie wpisuj `col_name` jako opisu.

2. Dla każdej kolumny zadaj kolejno:
   - **Klucz obcy?** → sprawdź CDN.Obiekty lub tabelę docelową, sprowadź kod + nazwa. Zachowaj ID.
   - **Enumeracja/flaga?** → pełny CASE z dokumentacji i bazy.
   - **Data?** → zidentyfikuj typ Clarion, zastosuj konwersję, użyj właściwego aliasu.
   - **Pole opisowe?** → bez zmian, uwzględnij.
   - **GIDFirma / GIDLp?** → pomijamy zawsze.
   - **GIDTyp?** → tłumaczymy CASE gdy rozróżnia typy. Pomijamy gdy stały dla całej tabeli.
   - **GIDNumer?** → zachowujemy jako `ID_[encja]`.
   - **Typ_Dok?** → zawsze pełna nazwa PL. `'Faktura sprzedaży'` nie `'FS'`.
   - **Inne techniczne?** → domyślnie uwzględniaj. Pomiń tylko przy COUNT DISTINCT = 1.

3. Zasada pominięcia — TYLKO jeden z warunków:
   1. `COUNT(DISTINCT col) = 1` — udowodnione zapytaniem
   2. Dokumentacja wprost: "pole nie jest obsługiwane" / "nieużywane"
   3. Dane wrażliwe (PESEL, rachunek bankowy, dokument tożsamości)
   4. Czyste komponenty GID: GIDFirma, GIDLp

4. Generuj plan Excel jako SQL z hardkodowanymi wartościami (UNION ALL):
   ```bash
   python tools/excel_export.py "SELECT ..." --output "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx"
   ```
   Kolumny planu: `Kolejnosc`, `CDN_Pole`, `Opis_w_dokumentacji`, `Przykladowe_wartosci`,
   `Alias_w_widoku`, `Transformacja`, `Uwzglednic`, `Uzasadnienie`, `Komentarz_Analityka`.

5. Wyślij plan do Analityka:
   ```bash
   python tools/agent_bus_cli.py send --from erp_specialist --to analyst --content-file tmp/tmp.md
   ```
   Wiadomość: ścieżka do planu Excel, baseline row count, krótki opis zakresu i kluczowych decyzji.

   **Wyjątek — widok według ugruntowanego wzorca:**
   Jeśli widok jest mechanicznym zastosowaniem istniejącego wzorca (np. kolejny GrupyDom),
   możesz dostarczyć plan + draft + export jednocześnie. Wskaż jawnie: "widok według wzorca X".
   Analityk i tak recenzuje plan niezależnie od draftu.

#### Forbidden

- Nie pisz SQL przed wysłaniem planu do Analityka (z wyjątkiem wzorca powyżej).
- Nie wpisuj `col_name` jako `Opis_w_dokumentacji`.
- Nie pomijaj pola bez jednego z 4 uzasadnień.

---

### Faza 1b — Recenzja planu (Analityk)

#### Steps

1. Odczytaj plan:
   ```bash
   python tools/excel_read_rows.py \
     --file "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx" \
     --columns CDN_Pole,Uwzglednic,Transformacja,Alias_w_widoku,Komentarz_Analityka
   ```

2. Weryfikacja konwencji — sprawdź każdy punkt:
   - Dane wrażliwe: żadna kolumna z listy (PESEL, rachunek bankowy, dokument tożsamości) nie jest w planie z `Uwzglednic=Tak`
   - GID: Firma pominięta, Lp pominięty, Numer zachowany jako `ID_[encja]`
   - Flagi 0/1: plan przewiduje CASE z etykietami kontekstowymi
   - Enumeracje: plan przewiduje CASE z ELSE zawierającym surową wartość
   - Daty: konwersja Clarion zaplanowana, alias `Data_XXX` vs `DataCzas_XXX` poprawny
   - Klucze obce: dla każdego pola ID_XXX zadaj pytanie: "czy ta encja ma czytelną nazwę lub kod?"
     Jeśli tak — plan MUSI zawierać te kolumny. Dotyczy bez wyjątku:
     adresów kontrahenta, numerów dokumentów powiązanych (korekta, zamówienie),
     cenników, słowników, operatorów, pracowników, magazynów i wszystkich innych encji.
     Samo ID w widoku BI jest dopuszczalne tylko gdy encja nie ma żadnego pola opisowego
     (udowodnione przez INFORMATION_SCHEMA).
   - Pominięcia: każde uzasadnione jednym z 4 powodów
   - Typy dokumentów: pełne nazwy PL, nie skróty

3. Weryfikacja danych — jeśli workdb istnieje:
   Skrzyżuj decyzje planu z faktycznymi danymi. Szukaj rozbieżności.

4. Odeślij feedback do ERP Specialist:
   ```bash
   python tools/agent_bus_cli.py send --from analyst --to erp_specialist --content-file tmp/tmp.md
   ```
   Feedback konkretny: co zmienić i dlaczego. Jeśli OK → "zatwierdzam plan".

#### Pętla feedback

ERP Specialist nanosi poprawki i wraca. Iteruj aż Analityk zatwierdzi.

Eskalacja do usera po 5 rundach bez porozumienia:
```bash
python tools/agent_bus_cli.py flag --from analyst --reason-file tmp/tmp.md
```

#### Forbidden

- Nie zatwierdzaj planu bez przejścia przez checklistę konwencji.
- Nie zatwierdzaj bez weryfikacji każdego pominięcia.

---

### Exit gate Fazy 1

PASS jeśli:
- Plan Excel istnieje w `solutions/bi/{NazwaWidoku}/`
- Analityk odesłał wiadomość "zatwierdzam plan"
- Progress log zapisany do bazy

BLOCKED jeśli plan nie zatwierdzony lub Analityk odesłał uwagi do poprawki.

---

## Faza 2 — SQL na brudnopisie

**Owner:** ERP Specialist

### Purpose

Iteracyjne budowanie SELECT w pliku roboczym. SQL powstaje i żyje wyłącznie w brudnopisie.

### Steps

1. Po odczycie zatwierdzonego planu — przeskanuj pod kątem niespójności PRZED generowaniem SQL:
   - `Komentarz_Analityka` wypełniony
   - `Uwzglednic=Nie` przy niepustym `Komentarz_Analityka`
   - `Transformacja` wygląda na niekompletną
   Niespójności zamknij z Analitykiem — nie angażuj usera.

2. Generuj SQL w brudnopisie `{NazwaWidoku}_draft.sql`:
   - Nie wrzucaj długich SELECT do czatu
   - Edytuj plik → eksportuj → weryfikuj → powtarzaj

3. Po każdej zmianie — obowiązkowy eksport:
   ```bash
   python tools/sql_query.py --file "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql" \
     --export "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
   ```
   Plik eksportu nadpisywany in-place (stała ścieżka bez timestampu).

   **Eksport próbkowy dla dużych widoków (>100k wierszy):** dodaj `TOP 100000` do SELECT.
   Weryfikacja statystyk przez `excel_read_stats.py` jest wystarczająca — pełny eksport niepotrzebny.

4. Zasady SQL:
   - Kolumny: PascalCase z underscore, polskie, opisowe (`Data_Wystawienia`, `Kod_Towaru`)
   - Klucz główny widoku: `ID_[encja]`
   - Para lookup: zawsze `Kod_X` + `Nazwa_X`
   - WHERE: tylko wykluczenie rekordów technicznych (np. `Rez_TwrNumer > 0`). Nigdy logika biznesowa.
   - Kolejność kolumn: odwzorowuj kolejność z `SELECT TOP 1 *`. JOINy bezpośrednio po kluczu.

5. Tłumaczenia wartości:
   ```sql
   -- Flagi 0/1:
   CASE pole WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
   ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')' END

   -- Enumeracje — ELSE obowiązkowy:
   CASE pole
       WHEN 960 THEN 'Zamówienie'
       ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')'
   END

   -- Data Clarion DATE:
   CASE WHEN col = 0 THEN NULL
        ELSE CAST(DATEADD(d, col, '18001228') AS DATE) END AS Data_XXX

   -- Data Clarion TIMESTAMP:
   CASE WHEN col = 0 THEN NULL
        ELSE CAST(DATEADD(ss, col, '1990-01-01') AS DATETIME) END AS DataCzas_XXX

   -- Pole numeryczne = brak:
   CASE WHEN col = 0 THEN NULL ELSE col END AS ID_X

   -- JOIN kontrahenta (dwuczęściowy klucz):
   LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = r.Rez_KntNumer
                            AND k.Knt_GIDTyp   = r.Rez_KntTyp
                            AND r.Rez_KntNumer > 0

   -- TraNag prefiks (obowiązkowa kolejność CASE):
   CASE
       WHEN n.TrN_GIDTyp IN (2041, 2045, 1529)
            AND EXISTS (SELECT 1 FROM CDN.TraNag s
                        WHERE s.TrN_SpiTyp = n.TrN_GIDTyp AND s.TrN_SpiNumer = n.TrN_GIDNumer
                          AND ((n.TrN_GIDTyp=2041 AND s.TrN_GIDTyp=2009) OR
                               (n.TrN_GIDTyp=2045 AND s.TrN_GIDTyp=2013) OR
                               (n.TrN_GIDTyp=1529 AND s.TrN_GIDTyp=1497)))  THEN '(Z)'
       WHEN n.TrN_Stan & 2 = 2 AND n.TrN_GIDTyp IN (2041, 2045, 1529)      THEN '(Z)'
       WHEN n.TrN_GenDokMag = -1 AND n.TrN_GIDTyp IN (1521, 1529, 1489)    THEN '(A)'
       WHEN n.TrN_GenDokMag = -1                                            THEN '(s)'
       ELSE ''
   END + RTRIM(n.TrN_Seria) + '/' + CAST(n.TrN_NumerTrN AS VARCHAR(10))
       + '/' + RIGHT(CAST(n.TrN_Rok AS VARCHAR(4)), 2)
   ```

6. Ograniczenia konta CEiM_BI:
   - Brak EXECUTE na funkcje CDN (error 229) — wszystkie konwersje i numery dokumentów inline
   - SELECT tylko na `AIBI.*` — CDN przez widok
   - `sql_query.py` blokuje `CREATE` — brudnopis to wyłącznie SELECT

7. Grupy hierarchiczne — buduj pełną ścieżkę CTE gdy FK wskazuje na tabelę z hierarchią:
   ```sql
   WITH Sciezka_Grup AS (
       SELECT GIDNumer, GrONumer, CAST(Kod AS NVARCHAR(500)) AS Sciezka
       FROM CDN.TwrGrupyDom WHERE GIDTyp = -16 AND GrONumer = 0
       UNION ALL
       SELECT d.GIDNumer, d.GrONumer, CAST(sg.Sciezka + '\' + d.Kod AS NVARCHAR(500))
       FROM CDN.TwrGrupyDom d JOIN Sciezka_Grup sg ON sg.GIDNumer = d.GrONumer
       WHERE d.GIDTyp = -16
   )
   ```
   Format ścieżki: `Poziom1\Poziom2\Poziom3`. Kolumny: `ID_Grupy` + `Sciezka_Grupy`.

### Forbidden

- Nie wrzucaj długich SELECT do czatu — tylko do pliku brudnopisu.
- Nie używaj `CREATE VIEW` w brudnopisie.
- Nie zostawiaj ELSE bez gałęzi w CASE.
- Nie używaj aliasu `Data_XXX` gdy kolumna zawiera godzinę — to błąd semantyczny.
- Nie używaj `TrN_TypNumeracji` — kolumna nie istnieje. Używaj `TrN_GIDTyp IN (...)`.

### Self-check przed zamknięciem fazy

- [ ] Dane wrażliwe: żadna kolumna PESEL / rachunek bankowy / dokument tożsamości w SELECT
- [ ] GID: Firma pominięta, Lp pominięty, Numer zachowany, Typ przetłumaczony lub pominięty
- [ ] Flagi: wszystkie 0/1 mają CASE z etykietami
- [ ] Enumeracje: wszystkie CASE mają ELSE z surową wartością
- [ ] Daty: konwersja Clarion zastosowana, 0 → NULL, sentinel → NULL, alias `Data_` vs `DataCzas_` poprawny
- [ ] Numery dokumentów: prefiks TraNag w prawidłowej kolejności (EXISTS → Stan&2 → GenDokMag)
- [ ] JOINy: COUNT(*) = COUNT(DISTINCT klucz) po każdym JOIN
- [ ] WHERE: tylko warunki techniczne
- [ ] Pominięcia: każde uzasadnione jednym z 4 powodów
- [ ] Eksport istnieje w `solutions/bi/{NazwaWidoku}/`

### Exit gate

PASS jeśli:
- Brudnopis SELECT istnieje i przeszedł przez `sql_query.py` bez błędu
- Eksport `{NazwaWidoku}_export.xlsx` istnieje i jest aktualny
- Self-check zaliczony (wszystkie pozycje odhaczone)
- Row count z eksportu = COUNT(*) z bazy (lub eksport próbkowy TOP 100000 dla widoków >100k wierszy)

BLOCKED jeśli którykolwiek warunek niespełniony.

---

## Faza 3 — Weryfikacja eksportu

**Owner:** ERP Specialist

### Purpose

Potwierdzić poprawność danych przed przekazaniem do zatwierdzenia.

### Steps

1. Uruchom weryfikację:
   - `bi_verify`: na końcu etapu lub gdy zmiana dotyka wielu kolumn/JOINów
   - `sql_query --export`: przy drobnej poprawce (1 kolumna, literówka)

   ```bash
   python tools/bi_verify.py --draft "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql" \
     --view-name "{NazwaWidoku}" \
     --plan "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx" \
     --export "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
   ```

2. Sprawdź wyniki:
   - Row count: musi równać się COUNT(*) z bazy. Różnica → zbadaj JOINy.
   - Daty: wyglądają jak daty (nie surowe liczby Clarion)
   - Enumeracje: distinct ≤ oczekiwana liczba typów, etykiety sensowne
   - Metryki: wartości w rozsądnym zakresie

3. Artefakt wyścigu czasowego: kilka NULLi w Nr_Dok przy eksporcie to normalne (nowe rekordy). Weryfikacja: `WHERE COALESCE(Nr_Dok, '') = ''` → 0 gdy SQL poprawny.

4. Wyślij eksport do Analityka przez agent_bus (ścieżka do pliku Excel + opis co zweryfikowano).

### Forbidden

- Nie przekazuj do Fazy 4 bez eksportu.
- Nie zakładaj "dane się zmieniły" gdy row count nie zgadza — zbadaj JOINy.

### Exit gate

PASS jeśli:
- Eksport istnieje i jest aktualny
- Row count zgadza się z COUNT(*) z bazy
- Analityk potwierdził eksport (wiadomość "OK" / "zatwierdzam eksport")

BLOCKED jeśli eksport brakuje lub Analityk zgłosił uwagi.

---

## Faza 4 — Zapis i wdrożenie

**Owner:** ERP Specialist (zapis) → DBA (wdrożenie w bazie) → ERP Specialist (katalog)

### Purpose

Zapisać zatwierdzony widok, wdrożyć przez DBA, zaktualizować katalog.

### Steps

1. Zapisz widok (CREATE OR ALTER):
   ```bash
   python tools/solutions_save_view.py --draft "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql"
   ```
   Weryfikuje że eksport istnieje przed zapisem. Zapisuje do `solutions/bi/views/{NazwaWidoku}.sql`.

2. Zgłoś do DBA przez agent_bus:
   ```
   # Zapisz treść do pliku tymczasowego, np. tmp/flag_dba_{NazwaWidoku}.md
   python tools/agent_bus_cli.py flag --from erp_specialist --reason-file tmp/flag_dba_{NazwaWidoku}.md
   ```
   Plik do wdrożenia: `solutions/bi/views/{NazwaWidoku}.sql`.

3. Po potwierdzeniu wdrożenia przez DBA — zaktualizuj katalog:
   ```bash
   python tools/bi_catalog_add.py --view AIBI.{NazwaWidoku} --add
   ```
   **Narzędzie odpytuje bazę — widok musi być wdrożony zanim je uruchomisz.**
   Nie wpisuj kolumn ręcznie do catalog.json.

4. Uzupełnij ręcznie w `catalog.json`: `description`, `example_questions`, `notes`.

5. Commit i push:
   ```bash
   python tools/git_commit.py --message "feat: widok BI.{NazwaWidoku} — opis" --all --push
   ```

### Forbidden

- Nie uruchamiaj `bi_catalog_add.py` przed potwierdzeniem wdrożenia przez DBA.
- Nie wpisuj kolumn ręcznie do catalog.json — narzędzie odpytuje bazę.
- Nie commituj bez uprzedniego wdrożenia przez DBA.

### Exit gate

PASS jeśli:
- `solutions/bi/views/{NazwaWidoku}.sql` istnieje
- DBA potwierdził wdrożenie
- `bi_catalog_add.py` uruchomiony po wdrożeniu
- Commit wykonany

BLOCKED jeśli DBA nie wdrożył lub katalog nie zaktualizowany.

---

## Zarządzanie kontekstem — progress log

Progress log jest kołem ratunkowym przy kompresji kontekstu.
Zapisuj obligatoryjnie na końcu każdej fazy do bazy:

```
python tools/agent_bus_cli.py log --role erp_specialist --content-file tmp/log_faza_X.md
```

Minimalny zakres pliku `tmp/log_faza_X.md`:

```markdown
## Status: [Faza X — nazwa] — {NazwaWidoku}

**Tabela główna:** CDN.XXX, N rekordów, filtr: `warunek`
**Baseline:** COUNT(*) = N, COUNT(DISTINCT) = N

**JOINy ustalone:**
- CDN.YYY — LEFT JOIN na kluczu ZZZ — uzasadnienie

**Enumeracje rozkodowane:**
- Pole_A: 1='Etykieta1', 0='Etykieta2' (źródło: dokumentacja/CDN.Obiekty)

**Numery dokumentów:** [CZEKA NA USERA] | [ZWERYFIKOWANE: format]

**Pliki:**
- Brudnopis: solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql
- Plan: solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx

**Następny krok:** [konkretna czynność]
```

---

## Kiedy eskalować do użytkownika

- Wartość enumeracji nieznana (brak w CDN.Obiekty i dokumentacji) — podaj surówkę
- Numery dokumentów — zawsze jednorazowe zapytanie zbiorcze przed pisaniem SQL
- Row count z eksportu ≠ COUNT z bazy — zbadaj i wyjaśnij przed pokazaniem wyników
- Wynik pusty lub dane wyglądają na błędne
- 5 wymian z Analitykiem bez porozumienia
- Potencjalna nieścisłość w dokumentacji — zgłoś, nie poprawiaj samodzielnie
