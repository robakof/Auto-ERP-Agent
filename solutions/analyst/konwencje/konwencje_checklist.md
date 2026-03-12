# Checklist konwencji widoków BI

Wyciągnięta z: ERP_VIEW_WORKFLOW.md, ERP_SCHEMA_PATTERNS.md, developer_notes.md
Data: 2026-03-12

---

## K01 — GIDFirma pominięte
GIDFirma nie pojawia się w kolumnach SELECT widoku.
Uzasadnienie: nie niesie informacji biznesowej (stała dla całej bazy).

## K02 — GIDTyp tłumaczony przez CASE (gdy niesie sens biznesowy)
GIDTyp tabeli głównej tłumaczony przez CASE gdy pole rozróżnia typy dokumentów/obiektów.
Wyjątek: GIDTyp stały dla całej tabeli (np. ZaN_GIDTyp = 960 zawsze) — pomijamy.

## K03 — GIDNumer zachowany jako ID
GIDNumer tabeli głównej obecny w SELECT jako klucz (np. ID_Rezerwacji, ID_Zamowienia).

## K04 — GIDLp pominięte
GIDLp nie pojawia się w kolumnach SELECT widoku.
Wyjątek: CDN.Rozrachunki — GIDLp używany wyłącznie w WHERE (= 1), nie w SELECT.

## K05 — Flagi 0/1 tłumaczone przez CASE
Nigdy surowa liczba 0/1 w widoku BI.
Format: CASE x WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie' ELSE 'Nieznane (' + CAST(x AS VARCHAR) + ')' END

## K06 — ELSE fallback w każdym CASE
Każde CASE (flagi, enumeracje, typy) musi mieć ELSE z surową wartością.
Nigdy ELSE NULL bez ujawnienia — milczący NULL ukrywa nieznane wartości.
Format fallbacku: 'Nieznane (' + CAST(pole AS VARCHAR) + ')'

## K07 — Typ_Dok pełna nazwa PL (nie akronim)
Kolumny opisujące typ dokumentu zawierają pełne nazwy: 'Faktura sprzedaży', nie 'FS'.
Wyjątek: akronimy jako część składowa numeru dokumentu (Nr_Dok) — dopuszczalne.

## K08 — Klucze obce: JOIN + kod + nazwa + zachowany ID
Dla każdego klucza obcego: dodaj JOIN do docelowej tabeli, sprowadź przynajmniej kod + nazwę.
ID zachowany (dla debugowania i ad-hoc JOINów).

## K09 — Clarion DATE konwersja
Format: CASE WHEN col = 0 THEN NULL ELSE CAST(DATEADD(d, col, '18001228') AS DATE) END
Pola z potencjalnymi sentinelami (>109211): CASE WHEN col BETWEEN 1 AND 109211 THEN ... ELSE NULL END

## K10 — Clarion TIMESTAMP konwersja
Format: CASE WHEN col = 0 THEN NULL ELSE CAST(DATEADD(ss, col, '1990-01-01') AS DATETIME) END

## K11 — Sentinel Clarion DATE
Wartości >109211 (np. 117976 = "bezterminowo") → NULL, nie przeliczane do daty.
Wzorzec defensywny: BETWEEN 1 AND 109211.

## K12 — Numery dokumentów inline
Numery budowane bez CDN.NazwaObiektu i CDN.NumerDokumentu (CEiM_BI nie ma EXECUTE).
Wszystkie konwersje inline w SELECT.

## K13 — Format numeru dokumentu zweryfikowany
Format numeru (YY vs YYYY, układ składników) zweryfikowany przez NazwaObiektu przed wdrożeniem.
Nie przyjmowany z góry.

## K14 — WHERE tylko warunki techniczne
WHERE nie zawiera logiki biznesowej ograniczającej zbiór (np. tylko aktywne, tylko z bieżącego roku).
Dopuszczalne: filtr techniczny wykluczający rekordy nieposiadające klucza (np. Rez_TwrNumer > 0,
ROZ_GIDLp = 1).

## K15 — Nazewnictwo kolumn: underscore + opisowe + polskie
Kolumny: PascalCase_z_underscore, polskie nazwy opisowe (Data_Wystawienia, nie DataWyst).
Klucz główny: ID_[encja] (ID_Rezerwacji, ID_Zamowienia).
Para lookup: Kod_X + Nazwa_X.

## K16 — Widok w schemacie AIBI
CREATE OR ALTER VIEW AIBI.NazwaWidoku (nie BI, nie CDN).

## K17 — Plik views/ zawiera CREATE OR ALTER VIEW
Plik w solutions/bi/views/ zawiera CREATE OR ALTER VIEW — nie sam SELECT.

## K18 — Pola numeryczne "brak" = NULL
Pola ID, gdzie 0 oznacza brak: CASE WHEN col = 0 THEN NULL ELSE col END.
Alternatywnie: warunek > 0 w JOIN z NULL propagowanym przez LEFT JOIN.

## K19 — JOIN kontrahenta: dwuczęściowy klucz
LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = x.Knt_Numer AND k.Knt_GIDTyp = x.Knt_Typ
Dotyczy gdy tabela źródłowa ma osobne pole GIDTyp dla kontrahenta (np. Rez_KntTyp).

## K20 — JOIN nie mnoży wierszy
COUNT(*) = COUNT(DISTINCT klucz_główny) po każdym dodanym JOINie.
Jeśli JOIN mnoży — dodaj zawężający warunek.

## K21 — CDN.Rozrachunki: WHERE ROZ_GIDLp = 1
Każdy JOIN/SELECT na CDN.Rozrachunki filtruje GIDLp = 1 (eliminuje lustrzane wiersze).

## K22 — TraNag prefiks (Z)/(s)/(A): prawidłowa kolejność CASE
Prawidłowa kolejność (z developer_notes.md, 2026-03-11):
  1. EXISTS (spinacz WZK/WKE/PZK) → '(Z)'
  2. Stan & 2 = 2 AND GIDTyp IN (...) → '(Z)' (fallback heurystyczny)
  3. GenDokMag = -1 AND GIDTyp IN (1521,1529,1489) → '(A)'
  4. GenDokMag = -1 → '(s)'
  5. ELSE ''
Widok używający starej heurystyki (tylko Stan & 2) jest niezgodny.

## K23 — TrN_TypNumeracji nie istnieje
Nie używaj TrN_TypNumeracji — kolumna nie istnieje w CDN.TraNag (Msg 207).
Zamiast: TrN_GIDTyp IN (lista numeryczna). Mapowanie: solutions/reference/numeracja_wzorce.tsv.

## K24 — Pominięcie pola: tylko 4 uzasadnione powody
Pole można pominąć WYŁĄCZNIE gdy:
  1. COUNT DISTINCT = 1 dla całej tabeli (stała wartość — udowodnione)
  2. Dokumentacja wprost: "nieobsługiwane" / "nieużywane"
  3. Dane wrażliwe (hasła, PINy)
  4. Czyste komponenty GID (GIDFirma, GIDLp) bez sensu biznesowego
W każdym innym przypadku — uwzględnij.
