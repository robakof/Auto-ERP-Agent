-- ============================================================
-- BI.Rezerwacje
-- Aktywne rezerwacje towarów — z danymi towaru, kontrahenta,
-- magazynu i dokumentu źródłowego (zamówienie ZS)
--
-- Kolumny:
--   ID, KodTowaru, NazwaTowaru, JednostkaRezerwacji
--   AkronimKontrahenta, NazwaKontrahenta
--   IloscZarezerwowana, IloscZrealizowana, IloscNaDokMagazynowych, IloscDoPokrycia
--   DataRealizacji, DataWaznosci
--   Magazyn, IDMagazynu
--   NumerZamowieniaZS (format: Seria/Numer/Rok, tylko gdy źródło = ZS)
--   ZrodloRezerwacji (5=ZamWew, 6=RęcznaWew, 9=ZamZew, 10=RęcznaZew, 16=DokMag)
--   OpisZrodla
--
-- Przykładowe pytania:
--   "jakie są aktywne rezerwacje towaru X"
--   "rezerwacje dla kontrahenta Y"
--   "ile sztuk towaru X jest zarezerwowane"
--   "przeterminowane rezerwacje"
--   "rezerwacje na dziś"
-- ============================================================

CREATE OR ALTER VIEW BI.Rezerwacje AS
SELECT
    r.Rez_GIDNumer                                                AS ID,

    -- Towar
    t.Twr_Kod                                                     AS KodTowaru,
    t.Twr_Nazwa                                                   AS NazwaTowaru,
    t.Twr_Jm                                                      AS JednostkaRezerwacji,

    -- Kontrahent (NULL = rezerwacja wewnętrzna / bez kontrahenta)
    k.Knt_Akronim                                                 AS AkronimKontrahenta,
    k.Knt_Nazwa1                                                  AS NazwaKontrahenta,

    -- Ilości
    r.Rez_Ilosc                                                   AS IloscZarezerwowana,
    r.Rez_Zrealizowano                                            AS IloscZrealizowana,
    r.Rez_IloscMag                                                AS IloscNaDokMagazynowych,
    r.Rez_Ilosc - r.Rez_Zrealizowano - r.Rez_IloscMag            AS IloscDoPokrycia,

    -- Daty (konwersja Clarion int → DATE; 0 = brak daty → NULL)
    CASE WHEN r.Rez_DataRealizacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataRealizacji, '18001228') AS DATE)
    END                                                           AS DataRealizacji,

    CASE WHEN r.Rez_DataWaznosci = 0 THEN NULL
         ELSE CAST(DATEADD(d, r.Rez_DataWaznosci, '18001228') AS DATE)
    END                                                           AS DataWaznosci,

    -- Magazyn (0 = globalna, dotyczy wszystkich magazynów)
    CASE WHEN r.Rez_MagNumer = 0 THEN 'Globalnie'
         ELSE m.Mag_Nazwa
    END                                                           AS Magazyn,
    r.Rez_MagNumer                                                AS IDMagazynu,

    -- Dokument źródłowy
    r.Rez_ZrdTyp                                                  AS TypDokumentuZrodlowego,
    r.Rez_ZrdNumer                                                AS IDDokumentuZrodlowego,

    -- Numer ZS (tylko gdy źródłem jest zamówienie sprzedaży, ZrdTyp=960)
    CASE WHEN r.Rez_ZrdTyp = 960 AND z.ZaN_GIDNumer IS NOT NULL
         THEN RTRIM(z.ZaN_ZamSeria) + '/' + CAST(z.ZaN_ZamNumer AS VARCHAR(10))
              + '/' + CAST(z.ZaN_ZamRok AS VARCHAR(4))
         ELSE NULL
    END                                                           AS NumerZamowieniaZS,

    -- Pochodzenie
    r.Rez_Zrodlo                                                  AS ZrodloRezerwacji,
    CASE r.Rez_Zrodlo
        WHEN 5  THEN 'Zamówienie wewnętrzne'
        WHEN 6  THEN 'Ręczna wewnętrzna'
        WHEN 9  THEN 'Zamówienie zewnętrzne'
        WHEN 10 THEN 'Ręczna zewnętrzna'
        WHEN 16 THEN 'Dokument magazynowy'
        ELSE        'Inne (' + CAST(r.Rez_Zrodlo AS VARCHAR) + ')'
    END                                                           AS OpisZrodla,

    r.Rez_Aktywna                                                 AS Aktywna,
    r.Rez_Typ                                                     AS Typ

FROM CDN.Rezerwacje r
JOIN  CDN.TwrKarty  t  ON  t.Twr_GIDNumer = r.Rez_TwrNumer
LEFT JOIN CDN.KntKarty  k  ON  k.Knt_GIDNumer = r.Rez_KntNumer
                           AND k.Knt_GIDTyp   = r.Rez_KntTyp
LEFT JOIN CDN.Magazyny  m  ON  m.Mag_GIDNumer = r.Rez_MagNumer
LEFT JOIN CDN.ZamNag    z  ON  z.ZaN_GIDNumer = r.Rez_ZrdNumer
                           AND r.Rez_ZrdTyp   = 960

WHERE r.Rez_TwrNumer > 0;  -- wyklucza rekordy techniczne bez towaru
GO
