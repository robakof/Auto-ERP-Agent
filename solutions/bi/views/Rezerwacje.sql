-- ============================================================
-- BI.Rezerwacje
-- Rezerwacje towarów z pełnymi danymi towaru, kontrahenta,
-- magazynu, dokumentu źródłowego i statusu rezerwacji.
--
-- Kolumny (kolejność zgodna z CDN.Rezerwacje):
--   Typ_Rezerwacji
--   ID_Rezerwacji
--   Kod_Towaru, Nazwa_Towaru, Jm_Towaru
--   Akronim_Kontrahenta, Nazwa_Kontrahenta
--   Typ_Dokumentu_Zrodlowego, Opis_Dokumentu_Zrodlowego, Numer_Dokumentu_Zrodlowego, Pozycja_Na_Dok_Zrodlowym
--   ID_Magazynu, Magazyn
--   ID_Dostawy
--   Ilosc_Zarezerwowana, Ilosc_Zrealizowana, Ilosc_Na_Dok_Magazynowych
--   Data_Wprowadzenia, Data_Realizacji, Data_Waznosci, Data_Aktywacji
--   Aktywna
--   Zrodlo_Rezerwacji, Opis_Zrodla
--   Data_Planowanej_Dostawy
--   ID_Centrum_Praw
--   Typ_Rez
--   Priorytet
--   Data_Rezerwacji
--   ID_Zasobu_Technologii
--   ID_Klasy_Cechy
--   Ilosc_Do_Pokrycia  [metryka]
--
-- Typy dokumentów źródłowych (Rez_ZrdTyp):
--   960   = Zamówienie (ZS/ZZ — wg ZaN_ZamTyp: 960=ZS, 1152=ZZ)
--   14345 = Operacja procesu produkcyjnego (ZPC)
--   14346 = Zasób procesu produkcyjnego (ZPZ) → numer ZP z CDN.ProdZlecenia
--   2592  = Rezerwacja u dostawcy (BkRez)
--
-- Źródła rezerwacji (Rez_Zrodlo):
--   5=Zamówienie wewnętrzne, 6=Ręczna wewnętrzna,
--   9=Zamówienie zewnętrzne, 10=Ręczna zewnętrzna, 16=Dokument magazynowy
--
-- Przykładowe pytania:
--   "jakie są rezerwacje towaru X"
--   "ile sztuk towaru X jest zarezerwowane"
--   "rezerwacje dla kontrahenta Y"
--   "przeterminowane rezerwacje"
--   "rezerwacje z zamówienia ZS-9/09/2025/ZTHK"
--   "rezerwacje ze zlecenia produkcji ZP-1/08/23/OTO"
--   "rezerwacje powiązane z dostawą"
-- ============================================================

CREATE OR ALTER VIEW BI.Rezerwacje AS
SELECT

    -- Typ rezerwacji (GIDTyp dekodowany z CDN.Obiekty)
    CASE r.Rez_GIDTyp
        WHEN 2576 THEN 'Rezerwacja'
        WHEN 2592 THEN 'Rezerwacja u dostawcy'
        ELSE            'Inne (' + CAST(r.Rez_GIDTyp AS VARCHAR) + ')'
    END                                                                     AS Typ_Rezerwacji,

    r.Rez_GIDNumer                                                          AS ID_Rezerwacji,

    -- Towar
    t.Twr_Kod                                                               AS Kod_Towaru,
    t.Twr_Nazwa                                                             AS Nazwa_Towaru,
    t.Twr_Jm                                                                AS Jm_Towaru,

    -- Kontrahent (NULL = rezerwacja wewnętrzna / produkcyjna bez kontrahenta)
    k.Knt_Akronim                                                           AS Akronim_Kontrahenta,
    k.Knt_Nazwa1                                                            AS Nazwa_Kontrahenta,

    -- Dokument źródłowy — typ
    r.Rez_ZrdTyp                                                            AS Typ_Dokumentu_Zrodlowego,
    CASE r.Rez_ZrdTyp
        WHEN 960   THEN 'Zamówienie'
        WHEN 14345 THEN 'Operacja procesu produkcyjnego'
        WHEN 14346 THEN 'Zasób procesu produkcyjnego'
        WHEN 2592  THEN 'Rezerwacja u dostawcy'
        ELSE            'Inne (' + CAST(r.Rez_ZrdTyp AS VARCHAR) + ')'
    END                                                                     AS Opis_Dokumentu_Zrodlowego,

    -- Dokument źródłowy — numer (inline, bez CDN functions)
    -- 960   → ZS/ZZ: Prefix-Numer/MM/RRRR/Seria (format zweryfikowany CDN.NazwaObiektu)
    -- 14346 → ZP: ZP-Numer/MM/RR/Seria (format zweryfikowany CDN.NazwaObiektu)
    -- 14345 → ZPC: brak numeru tekstowego (operacja, nie zlecenie)
    -- 2592  → BkRez: brak numeru tekstowego — ID rezerwacji
    CASE
        WHEN r.Rez_ZrdTyp = 960 AND z.ZaN_GIDNumer IS NOT NULL THEN
            CASE z.ZaN_ZamTyp WHEN 1280 THEN 'ZS' WHEN 1152 THEN 'ZZ' ELSE 'ZAM' END
            + '-' + CAST(z.ZaN_ZamNumer AS VARCHAR(10))
            + '/' + RIGHT('0' + CAST(z.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
            + '/' + CAST(z.ZaN_ZamRok AS VARCHAR(4))
            + '/' + RTRIM(z.ZaN_ZamSeria)
        WHEN r.Rez_ZrdTyp = 14346 AND pzl.PZL_Id IS NOT NULL THEN
            'ZP-' + CAST(pzl.PZL_Numer AS VARCHAR(10))
            + '/' + RIGHT('0' + CAST(pzl.PZL_Miesiac AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(pzl.PZL_Rok AS VARCHAR(4)), 2)
            + '/' + RTRIM(pzl.PZL_Seria)
        WHEN r.Rez_ZrdTyp = 2592 THEN
            'BkRez#' + CAST(r.Rez_ZrdNumer AS VARCHAR(10))
        ELSE NULL
    END                                                                     AS Numer_Dokumentu_Zrodlowego,

    -- Pozycja na dokumencie źródłowym (0 = nagłówek)
    r.Rez_ZrdLp                                                             AS Pozycja_Na_Dok_Zrodlowym,

    -- Magazyn (0 = globalna — dotyczy wszystkich magazynów)
    r.Rez_MagNumer                                                          AS ID_Magazynu,
    CASE WHEN r.Rez_MagNumer = 0 THEN 'Globalnie'
         ELSE m.Mag_Nazwa
    END                                                                     AS Magazyn,

    -- Dostawa (wypełniana tylko po stronie sprzedaży; 0 = brak)
    CASE WHEN r.Rez_DstNumer = 0 THEN NULL
         ELSE r.Rez_DstNumer
    END                                                                     AS ID_Dostawy,

    -- Ilości
    r.Rez_Ilosc                                                             AS Ilosc_Zarezerwowana,
    r.Rez_Zrealizowano                                                      AS Ilosc_Zrealizowana,
    r.Rez_IloscMag                                                          AS Ilosc_Na_Dok_Magazynowych,

    -- Daty (konwersja Clarion; 0 = brak daty → NULL)
    CASE WHEN r.Rez_TStamp = 0 THEN NULL
         ELSE CAST(DATEADD(ss, r.Rez_TStamp, '1990-01-01') AS DATETIME)
    END                                                                     AS Data_Wprowadzenia,

    CASE WHEN r.Rez_DataRealizacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataRealizacji, '18001228') AS DATE)
    END                                                                     AS Data_Realizacji,

    CASE WHEN r.Rez_DataWaznosci = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataWaznosci, '18001228') AS DATE)
    END                                                                     AS Data_Waznosci,

    -- Początkowa data ważności; przed nią i po DataWaznosci rezerwacja jest ignorowana
    CASE WHEN r.Rez_DataAktywacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataAktywacji, '18001228') AS DATE)
    END                                                                     AS Data_Aktywacji,

    -- Status
    CASE r.Rez_Aktywna
        WHEN 1 THEN 'Tak'
        WHEN 0 THEN 'Nie'
        ELSE        'Inne (' + CAST(r.Rez_Aktywna AS VARCHAR) + ')'
    END                                                                     AS Aktywna,

    r.Rez_Zrodlo                                                            AS Zrodlo_Rezerwacji,
    CASE r.Rez_Zrodlo
        WHEN 5  THEN 'Zamówienie wewnętrzne'
        WHEN 6  THEN 'Ręczna wewnętrzna'
        WHEN 9  THEN 'Zamówienie zewnętrzne'
        WHEN 10 THEN 'Ręczna zewnętrzna'
        WHEN 16 THEN 'Dokument magazynowy'
        ELSE         'Inne (' + CAST(r.Rez_Zrodlo AS VARCHAR) + ')'
    END                                                                     AS Opis_Zrodla,

    -- Planowana data dostawy
    CASE WHEN r.Rez_DataPotwDst = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataPotwDst, '18001228') AS DATE)
    END                                                                     AS Data_Planowanej_Dostawy,

    -- Centrum praw (miejsce w strukturze firmy; FK do CDN.FrmStruktura)
    r.Rez_FrsID                                                             AS ID_Centrum_Praw,

    CASE r.Rez_Typ
        WHEN 1 THEN 'Rezerwacja'
        WHEN 0 THEN 'Nierezerwacja'
        ELSE        'Inne (' + CAST(r.Rez_Typ AS VARCHAR) + ')'
    END                                                                     AS Typ_Rez,

    r.Rez_Priorytet                                                         AS Priorytet,

    CASE WHEN r.Rez_DataRezerwacji = 0 THEN NULL
         ELSE CAST(DATEADD(ss, r.Rez_DataRezerwacji, '1990-01-01') AS DATETIME)
    END                                                                     AS Data_Rezerwacji,

    -- Zasób z technologii z czynności lub realizacji (produkcja)
    r.Rez_PTZID                                                             AS ID_Zasobu_Technologii,

    -- Klasa cechy towaru (0 = brak cechy)
    r.Rez_CCHNumer                                                          AS ID_Klasy_Cechy,

    -- Metryka obliczeniowa
    r.Rez_Ilosc - r.Rez_Zrealizowano - r.Rez_IloscMag                      AS Ilosc_Do_Pokrycia

FROM CDN.Rezerwacje r
JOIN      CDN.TwrKarty    t   ON  t.Twr_GIDNumer  = r.Rez_TwrNumer
LEFT JOIN CDN.KntKarty    k   ON  k.Knt_GIDNumer  = r.Rez_KntNumer
                              AND k.Knt_GIDTyp     = r.Rez_KntTyp
LEFT JOIN CDN.Magazyny    m   ON  m.Mag_GIDNumer   = r.Rez_MagNumer
LEFT JOIN CDN.ZamNag      z   ON  z.ZaN_GIDNumer   = r.Rez_ZrdNumer
                              AND r.Rez_ZrdTyp     = 960
LEFT JOIN CDN.ProdZasoby  pza ON  pza.PZA_Id       = r.Rez_ZrdNumer
                              AND r.Rez_ZrdTyp     = 14346
LEFT JOIN CDN.ProdZlecenia pzl ON  pzl.PZL_Id      = pza.PZA_PZLId
LEFT JOIN CDN.Dostawy     d   ON  d.Dst_GIDNumer   = r.Rez_DstNumer
                              AND r.Rez_DstTyp     = 160

WHERE r.Rez_TwrNumer > 0;
GO
