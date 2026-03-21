-- MagElem plan_src.sql
-- Generuje plan mapowania dla bi_plan_generate.py
-- Tabela główna: CDN.MagElem (pozycje dokumentów magazynowych)
-- Baseline: ~752 570 wierszy

SELECT * FROM (

-- === KLUCZ GŁÓWNY / IDENTYFIKACJA ===
SELECT  1           AS Kolejnosc,
        'MaE_GIDTyp'            AS CDN_Pole,
        'Typ identyfikatora dokumentu' AS Opis_w_dokumentacji,
        '1605, 1093, 1601, 1089' AS Przykladowe_wartosci,
        'Typ_Dokumentu'         AS Alias_w_widoku,
        'CASE: 1089=Przyjecie magazynowe, 1093=Awizo dostawy, 1601=Wydanie magazynowe, 1605=Zlecenie wydania z magazynu + ELSE' AS Transformacja,
        'Tak'                   AS Uwzglednic,
        ''                      AS Uzasadnienie,
        'GIDTyp nagłówka MagNag — 4 typy z CDN.Obiekty: PM/AWD/WM/ZWM' AS Komentarz_Analityka
UNION ALL
SELECT  2, 'MaE_GIDNumer', 'Identyfikator dokumentu', '10, 51056, 50948',
        'ID_Dokumentu', 'FK do CDN.MagNag — zachować jako ID, Nr_Dokumentu z JOINu nagłówka',
        'Tak', '', 'Klucz obcy do CDN.MagNag; Nr_Dokumentu pobieramy przez JOIN'
UNION ALL
SELECT  3, 'MaE_GIDLp', 'Numer kolejny pozycji dokumentu', '1, 2, 3',
        'Nr_Pozycji', 'Bezpośrednio — composite PK (GIDNumer+GIDLp)',
        'Tak', '', 'Część PK — zawsze uwzględniamy dla tabel pozycji'
UNION ALL
SELECT  4, 'MaE_Pozycja', 'Pozycja elementu na dokumencie', '1, 2, 3',
        'Pozycja_Na_Dokumencie', 'Bezpośrednio',
        'Tak', '', 'Analog TrE_Pozycja — renumerowalny numer wyświetlany na dok.'

-- === NR DOKUMENTU (z JOINu MagNag) ===
UNION ALL
SELECT  5, '(JOIN CDN.MagNag)', 'Numer dokumentu z nagłówka', 'AWD-1/05/23, ZWM-5/03/24',
        'Nr_Dokumentu', 'CASE MaN_GIDTyp → SKRÓT + Nr/MM/YY[/Seria] — wzorzec identyczny z AIBI.MagNag',
        'Tak', '', 'Nie ma pola numeru bezpośrednio w MagElem — z JOINu MagNag'

-- === TOWAR ===
UNION ALL
SELECT  6, 'MaE_TwrTyp', 'Typ identyfikatora towaru', '16',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (always 16)', 'Stała techniczna'
UNION ALL
SELECT  7, 'MaE_TwrNumer', 'Identyfikator towaru', '3290, 3282, 5478',
        'ID_Towaru', 'Bezpośrednio (CASE WHEN 0 THEN NULL ELSE val END)',
        'Tak', '', 'FK do CDN.TwrKarty'
UNION ALL
SELECT  8, '(JOIN CDN.TwrKarty)', 'Kod towaru (aktualny)', 'CWKZ0033, NIEO0263',
        'Kod_Towaru', 'Twr_Kod z JOINu TwrKarty',
        'Nie', 'Duplikat aliasu — Kod_Towaru pochodzi z MaE_TwrKod (row 9); JOIN TwrKarty tylko dla Nazwa_Towaru', 'Poprawka iteracja 2 — usunięcie duplikatu (Analityk msg 141)'
UNION ALL
SELECT  9, 'MaE_TwrKod', 'Kod towaru (denormalizowany)', 'CWKZ0033, NIEO0263',
        'Kod_Towaru', 'Bezpośrednio — MaE_TwrKod (historyczny w momencie transakcji)',
        'Tak', '', 'Dostępny bezpośrednio; JOIN TwrKarty potrzebny dla Nazwa_Towaru. Decyzja: MaE_TwrKod as Kod_Towaru, JOIN dla Twr_Nazwa1'
UNION ALL
SELECT  10, '(JOIN CDN.TwrKarty)', 'Nazwa towaru', 'Znicz okrągły mały',
        'Nazwa_Towaru', 'Twr_Nazwa1 z JOINu CDN.TwrKarty',
        'Tak', '', 'Każde ID_Towaru wymaga kolumny opisowej'

-- === CECHY ===
UNION ALL
SELECT  11, 'MaE_CCKTyp', 'Typ identyfikatora klasy cechy', '0, 192',
        '', '',
        'Nie', 'Techniczny komponent GID klasy cechy — para z CCKNumer', 'GIDTyp techniczny'
UNION ALL
SELECT  12, 'MaE_CCKNumer', 'Identyfikator klasy cechy', '0, 1',
        '', '',
        'Nie', 'Wartość 1=Partia (CDN.CechyKlasy); 0=brak. Cecha bezpośrednio w MaE_Cecha — CCKNumer nie wnosi wartości BI', 'Techniczne — zduplikowane przez MaE_Cecha'
UNION ALL
SELECT  13, 'MaE_Cecha', 'Cecha towaru', '346.P30.2.5J, 115.1J',
        'Cecha', 'Bezpośrednio',
        'Tak', '', 'Czytelny string cechy (seria produkcyjna / lot)'
UNION ALL
SELECT  14, 'MaE_CCK2Typ', 'Typ identyfikatora klasy cechy 2', '0, 192',
        '', '',
        'Nie', 'Techniczny komponent GID — para z CCK2Numer', 'GIDTyp techniczny'
UNION ALL
SELECT  15, 'MaE_CCK2Numer', 'Identyfikator klasy cechy 2', '0, 1',
        '', '',
        'Nie', 'Wartość 1=Partia (CDN.CechyKlasy); 0=brak. Cecha2 bezpośrednio w MaE_Cecha2 — CCK2Numer nie wnosi wartości BI', 'Techniczne — zduplikowane przez MaE_Cecha2'
UNION ALL
SELECT  16, 'MaE_Cecha2', 'Cecha towaru 2', '115.1J, 346.P30.2.5J',
        'Cecha2', 'Bezpośrednio',
        'Tak', '', 'Drugi string cechy'

-- === EAN ===
UNION ALL
SELECT  17, 'MaE_Ean', 'Kod kreskowy', '5907702509853',
        'EAN', 'Bezpośrednio',
        'Tak', '', 'Kod EAN pozycji'

-- === DATA ===
UNION ALL
SELECT  18, 'MaE_DataW', 'Data ważności', '0',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all 0 — brak dat ważności w danych)', 'Stała techniczna'

-- === ILOŚĆ I JEDNOSTKI ===
UNION ALL
SELECT  19, 'MaE_Ilosc', 'Ilość w jednostce podstawowej', '1.0000, 2.0000',
        'Ilosc', 'Bezpośrednio (DECIMAL)',
        'Tak', '', 'Ilość ruchu magazynowego'
UNION ALL
SELECT  20, 'MaE_JmFormat', 'Miejsca po przecinku (JM podstawowa)', '0, 1, 4',
        '', '',
        'Nie', 'Techniczny format wyświetlania — nie analityczny', 'Techniczne pole formatowania'
UNION ALL
SELECT  21, 'MaE_JmZ', 'Jednostka pomocnicza', 'szt., opak., paleta',
        'Jednostka_Pomocnicza', 'Bezpośrednio (RTRIM)',
        'Tak', '', 'JM pomocnicza na pozycji'
UNION ALL
SELECT  22, 'MaE_JmFormatZ', 'Miejsca po przecinku (JM pomocnicza)', '0, 1',
        '', '',
        'Nie', 'Techniczny format wyświetlania — nie analityczny', 'Techniczne pole formatowania'
UNION ALL
SELECT  23, 'MaE_TypJm', 'Przelicznik ciągły/dyskretny', '1, 2',
        'Typ_Przelicznika_JM', 'CASE: 1=Ciagly, 2=Dyskretny + ELSE',
        'Tak', '', '2 distinct: 1=ciągły (445776), 2=dyskretny (306794)'
UNION ALL
SELECT  24, 'MaE_PrzeliczM', 'Mianownik przelicznika', '1',
        'Przelicznik_Mianownik', 'Bezpośrednio (DECIMAL)',
        'Tak', '', 'Przelicznik JM — mianownik'
UNION ALL
SELECT  25, 'MaE_PrzeliczL', 'Licznik przelicznika', '1, 6, 12, 25',
        'Przelicznik_Licznik', 'Bezpośrednio (DECIMAL)',
        'Tak', '', 'Przelicznik JM — licznik'
UNION ALL
SELECT  26, 'MaE_JednostkaLog', 'Jednostka logistyczna WMS', '0, 344',
        'ID_Jednostki_Logistycznej', 'CASE WHEN 0 THEN NULL ELSE val END',
        'Tak', '', '2 distinct (0=752527 brak, 344=43 z JL); ID bez tabeli opisowej — zachować jako ID'

-- === PARTIA ===
UNION ALL
SELECT  27, 'MaE_TPaId', 'Identyfikator partii towaru', '4405, 3832',
        'ID_Partii', 'Bezpośrednio — MaE_TPaId; CDN.TwrPartie nie wnosi pól opisowych (Cecha=MaE_Cecha, DataW=all 0)',
        'Tak', '', 'FK do CDN.TwrPartie; 6752 distinct — każda pozycja ma partię'

-- === OPERATOR ===
UNION ALL
SELECT  28, 'MaE_OpeTyp', 'Typ operatora', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'
UNION ALL
SELECT  29, 'MaE_OpeFirma', 'Firma operatora', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'
UNION ALL
SELECT  30, 'MaE_OpeNumer', 'Numer operatora', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'
UNION ALL
SELECT  31, 'MaE_OpeLp', 'Lp operatora', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'

-- === OPIS ===
UNION ALL
SELECT  32, 'MaE_Opis', 'Opis pozycji', 'po 5 z zapachu, mix po 6',
        'Opis', 'Bezpośrednio (NULLIF(RTRIM, ''''))',
        'Tak', '', 'Opis wolnotekstowy pozycji'

-- === STATUS ===
UNION ALL
SELECT  33, 'MaE_Status', 'Stan zlecenia', '0, 1, 4, 5',
        'Status_Pozycji', 'CASE: 0=Niezatwierdzony, 1=Zatwierdzony, 2=W realizacji, 4=Zamkniety, 5=Zamkniety bez realizacji, 6=Zamkniety do edycji + ELSE',
        'Tak', '', '4 wartości w danych; 2 i 6 z dokumentacji MaN_Status (MagNag) — dodać do CASE'

-- === ILOŚCI SKRAJNE ===
UNION ALL
SELECT  34, 'MaE_IloscMin', 'Minimalna ilość', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'
UNION ALL
SELECT  35, 'MaE_IloscMax', 'Maksymalna ilość', 'null',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all null)', 'Puste w całej tabeli'

-- === WMS ===
UNION ALL
SELECT  36, 'MaE_JLogWMS', 'Kaucja jednostki logistycznej WMS', '0',
        '', '',
        'Nie', 'COUNT DISTINCT=1 (all 0)', 'Stała techniczna — brak kaucji WMS w danych'

) AS plan
ORDER BY Kolejnosc
