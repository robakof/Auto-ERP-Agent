USE [ERPXL_CEIM];
GO

CREATE OR ALTER VIEW AIBI.TraElem AS

-- BRUDNOPIS -- wylacznie SELECT, bez CREATE VIEW
-- AIBI.TraElem -- pozycje dokumentow handlowych
-- Status: Faza 2 -- draft v1

WITH CenBase AS (
    SELECT t.TCN_RodzajCeny, RTRIM(t.TCN_Nazwa) AS TCN_Nazwa
    FROM CDN.TwrCenyNag t
    WHERE t.TCN_Id = (
        SELECT MIN(t2.TCN_Id) FROM CDN.TwrCenyNag t2
        WHERE t2.TCN_RodzajCeny = t.TCN_RodzajCeny
    )
)
SELECT
    -- === TYP I IDENTYFIKACJA ===
    CASE e.TrE_GIDTyp
        WHEN 2034 THEN 'Paragon'
        WHEN 2033 THEN 'Faktura sprzedazy'
        WHEN 1617 THEN 'Przychod wewnetrzny'
        WHEN 2001 THEN 'Wydanie zewnetrzne'
        WHEN 1521 THEN 'Faktura zakupu'
        WHEN 2009 THEN 'Korekta wydania zewnetrznego'
        WHEN 1603 THEN 'Przesuniecie MM wydanie'
        WHEN 1604 THEN 'Przesuniecie MM przyjecie'
        WHEN 1616 THEN 'Rozchod wewnetrzny'
        WHEN 2041 THEN 'Korekta faktury sprzedazy'
        WHEN 2003 THEN 'Korekta kosztu'
        WHEN 1489 THEN 'Przyjecie zewnetrzne'
        WHEN 1497 THEN 'Korekta przyjecia zewnetrznego'
        WHEN 1625 THEN 'Korekta przychodu wewnetrznego'
        WHEN 1529 THEN 'Korekta faktury zakupu'
        WHEN 2042 THEN 'Korekta paragonu'
        WHEN 2037 THEN 'Faktura eksportowa'
        WHEN 2013 THEN 'Korekta wydania eksportowego'
        WHEN 2005 THEN 'Wydanie zewnetrzne eksportowe'
        WHEN 1624 THEN 'Korekta rozchodu wewnetrznego'
        WHEN 2039 THEN 'Raport sprzedazy'
        WHEN 2045 THEN 'Korekta faktury eksportowej'
        WHEN 2035 THEN 'Faktura do paragonu'
        WHEN 2004 THEN 'Deprecjacja'
        WHEN 1232 THEN 'Koszt dodatkowy zakupu'
        ELSE 'Nieznane (' + CAST(e.TrE_GIDTyp AS VARCHAR(10)) + ')'
    END                                                                 AS Typ_Dokumentu,
    e.TrE_GIDNumer                                                      AS ID_Dokumentu,
    e.TrE_GIDLp                                                         AS Nr_Pozycji,
    e.TrE_Pozycja                                                       AS Pozycja_Na_Dokumencie,

    -- === NUMER I DATA DOKUMENTU (z JOIN CDN.TraNag) ===
    CASE
        WHEN n.TrN_GIDTyp IN (2041, 2045, 1529)
             AND EXISTS (
                 SELECT 1 FROM CDN.TraNag s
                 WHERE s.TrN_SpiTyp   = n.TrN_GIDTyp
                   AND s.TrN_SpiNumer = n.TrN_GIDNumer
                   AND (   (n.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009)
                        OR (n.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013)
                        OR (n.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497))
             )                                                          THEN '(Z)'
        WHEN n.TrN_Stan & 2 = 2
             AND n.TrN_GIDTyp IN (2041, 2045, 1529)                    THEN '(Z)'
        WHEN n.TrN_GenDokMag = -1
             AND n.TrN_GIDTyp IN (1521, 1529, 1489)                    THEN '(A)'
        WHEN n.TrN_GenDokMag = -1                                      THEN '(s)'
        ELSE ''
    END
    + CASE n.TrN_GIDTyp
        WHEN 2034 THEN 'PA'   WHEN 2033 THEN 'FS'   WHEN 1617 THEN 'PW'
        WHEN 2001 THEN 'WZ'   WHEN 1521 THEN 'FZ'   WHEN 2009 THEN 'WZK'
        WHEN 1603 THEN 'MMW'  WHEN 1604 THEN 'MMP'  WHEN 1616 THEN 'RW'
        WHEN 2041 THEN 'FSK'  WHEN 2003 THEN 'KK'   WHEN 1489 THEN 'PZ'
        WHEN 1497 THEN 'PZK'  WHEN 1625 THEN 'PWK'  WHEN 1529 THEN 'FZK'
        WHEN 2042 THEN 'PAK'  WHEN 2037 THEN 'FSE'  WHEN 2013 THEN 'WKE'
        WHEN 2005 THEN 'WZE'  WHEN 1624 THEN 'RWK'  WHEN 2039 THEN 'RS'
        WHEN 2045 THEN 'FKE'  WHEN 2035 THEN 'RA'   WHEN 2004 THEN 'DP'
        WHEN 1232 THEN 'KDZ'
        ELSE CAST(n.TrN_GIDTyp AS VARCHAR(10))
      END
    + '-' + CAST(n.TrN_TrNNumer AS VARCHAR(10))
    + '/' + RIGHT('0' + CAST(n.TrN_TrNMiesiac AS VARCHAR(2)), 2)
    + '/' + RIGHT(CAST(n.TrN_TrNRok AS VARCHAR(4)), 2)
    + CASE WHEN RTRIM(n.TrN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(n.TrN_TrNSeria) END
                                                                        AS Numer_Dokumentu,
    CASE WHEN n.TrN_Data2 BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_Data2 - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                                  AS Data_Wystawienia,

    -- === TOWAR ===
    CASE WHEN e.TrE_TwrNumer = 0 THEN NULL ELSE e.TrE_TwrNumer END     AS ID_Towaru,
    RTRIM(e.TrE_TwrNazwa)                                               AS Nazwa_Towaru,
    RTRIM(e.TrE_TwrKod)                                                 AS Kod_Towaru,
    CASE e.TrE_TypTwr
        WHEN 1 THEN 'Towar'
        WHEN 2 THEN 'Produkt'
        WHEN 3 THEN 'Koszt'
        WHEN 4 THEN 'Usluga'
        WHEN 6 THEN 'A-Vista'
        ELSE 'Nieznane (' + CAST(e.TrE_TypTwr AS VARCHAR(5)) + ')'
    END                                                                 AS Typ_Towaru,

    -- === KONTRAHENT POZYCJI ===
    CASE WHEN e.TrE_KntNumer = 0 THEN NULL ELSE e.TrE_KntNumer END     AS ID_Kontrahenta_Pozycji,
    knt_pos.Knt_Akronim                                                 AS Akronim_Kontrahenta_Pozycji,
    knt_pos.Knt_Nazwa1                                                  AS Nazwa_Kontrahenta_Pozycji,

    -- === AKWIZYTOR ===
    CASE WHEN e.TrE_AkwNumer = 0 THEN NULL ELSE e.TrE_AkwNumer END     AS ID_Akwizytora,
    COALESCE(akw_knt.Knt_Akronim, akw_prc.Prc_Akronim)                 AS Akwizytor_Akronim,

    -- === CZAS UTWORZENIA (Clarion TIMESTAMP) ===
    CASE WHEN e.TrE_TrnTStamp = 0 THEN NULL
         ELSE CAST(DATEADD(ss, e.TrE_TrnTStamp, '1990-01-01') AS DATETIME)
    END                                                                 AS DataCzas_Utworzenia,

    -- === ILOSC I JEDNOSTKA MIARY ===
    e.TrE_Ilosc                                                         AS Ilosc,
    RTRIM(e.TrE_JmZ)                                                    AS Jednostka_Miary,
    e.TrE_PrzeliczL                                                     AS Przelicznik_JM,

    -- === VAT ===
    e.TrE_GrupaPod                                                      AS Grupa_VAT,
    e.TrE_StawkaPod                                                     AS Stawka_VAT,
    CASE e.TrE_FlagaVat
        WHEN 0 THEN 'Zwolniony'
        WHEN 1 THEN 'Opodatkowany'
        WHEN 2 THEN 'Nie podlega'
        ELSE 'Nieznane (' + CAST(e.TrE_FlagaVat AS VARCHAR(5)) + ')'
    END                                                                 AS Flaga_VAT,

    -- === WALUTA ===
    e.TrE_Waluta                                                        AS Waluta,
    e.TrE_KursM                                                         AS Kurs_Mianownik,
    e.TrE_KursL                                                         AS Kurs_Licznik,

    -- === CENY I WARTOSCI ===
    e.TrE_Poczatkowa                                                    AS Cena_Poczatkowa_Waluta,
    CASE e.TrE_FlagaNB
        WHEN 'N' THEN 'Od netto'
        WHEN 'B' THEN 'Od brutto'
        ELSE 'Nieznane (' + e.TrE_FlagaNB + ')'
    END                                                                 AS Kalkulacja_VAT,
    e.TrE_Rabat                                                         AS Rabat_Procent,
    e.TrE_WartoscPoRabacie                                              AS Wartosc_Po_Rabacie_Waluta,
    e.TrE_KsiegowaNetto                                                 AS Wartosc_Netto_PLN,
    e.TrE_KsiegowaBrutto                                                AS Wartosc_Brutto_PLN,
    e.TrE_RzeczywistaNetto                                              AS Wartosc_Rzeczywista_Netto_PLN,
    e.TrE_KosztKsiegowy                                                 AS Koszt_Ksiegowy_PLN,
    e.TrE_KosztRzeczywisty                                              AS Koszt_Rzeczywisty_PLN,
    e.TrE_Cena                                                          AS Cena_Jednostkowa,
    CASE e.TrE_Rownanie
        WHEN 0 THEN 'Nieaktywne'
        WHEN 1 THEN 'Aktywne'
        ELSE 'Nieznane (' + CAST(e.TrE_Rownanie AS VARCHAR(5)) + ')'
    END                                                                 AS Rowna_IloscxCena,
    CASE e.TrE_OdKsiegowych
        WHEN 0 THEN 'Nie'
        WHEN 1 THEN 'Tak'
        ELSE 'Nieznane (' + CAST(e.TrE_OdKsiegowych AS VARCHAR(5)) + ')'
    END                                                                 AS Wartosci_Od_Ksiegowych,

    -- === KRAJ POCHODZENIA ===
    NULLIF(RTRIM(e.TrE_KrajPoch), '')                                   AS Kraj_Pochodzenia,

    -- === RABATY PROMOCYJNE ===
    e.TrE_RabatPromocyjny                                               AS Rabat_Promocyjny,
    e.TrE_RabatKorekta                                                  AS Rabat_Korekta,

    -- === CENNIK ===
    CASE WHEN e.TrE_CenaSpr IN (0, -32000) THEN NULL ELSE e.TrE_CenaSpr END AS ID_Cennika,
    cen.TCN_Nazwa                                                       AS Nazwa_Cennika,
    e.TrE_CenaPoRabacie                                                 AS Cena_Po_Rabacie,
    NULLIF(RTRIM(e.TrE_Cecha), '')                                      AS Cecha_Towaru,

    -- === KOREKTY ===
    e.TrE_IloscPrzedKorekta                                             AS Ilosc_Przed_Korekta,
    e.TrE_CenaPrzedKorekta                                              AS Cena_Przed_Korekta,
    e.TrE_WartoscPrzedKorekta                                           AS Wartosc_Przed_Korekta_PLN,
    NULLIF(RTRIM(e.TrE_GrupaPodPrzedKorekta), '')                       AS Grupa_VAT_Przed_Korekta,
    e.TrE_StawkaPodPrzedKorekta                                         AS Stawka_VAT_Przed_Korekta,
    CASE e.TrE_FlagaVatPrzedKorekta
        WHEN 0 THEN 'Zwolniony'
        WHEN 1 THEN 'Opodatkowany'
        WHEN 2 THEN 'Nie podlega'
        ELSE 'Nieznane (' + CAST(e.TrE_FlagaVatPrzedKorekta AS VARCHAR(5)) + ')'
    END                                                                 AS Flaga_VAT_Przed_Korekta,
    NULLIF(RTRIM(e.TrE_PrzyczynaKorekty), '')                          AS Przyczyna_Korekty,

    -- === RABAT OPERATORA ===
    e.TrE_RabatOpeGen                                                   AS Rabat_Operator

FROM CDN.TraElem e
JOIN CDN.TraNag n
     ON n.TrN_GIDNumer = e.TrE_GIDNumer
    AND n.TrN_GIDTyp   = e.TrE_GIDTyp
LEFT JOIN CDN.KntKarty knt_pos
       ON knt_pos.Knt_GIDNumer = e.TrE_KntNumer
      AND knt_pos.Knt_GIDTyp   = e.TrE_KntTyp
      AND e.TrE_KntNumer       > 0
LEFT JOIN CDN.KntKarty akw_knt
       ON akw_knt.Knt_GIDNumer = e.TrE_AkwNumer
      AND e.TrE_AkwTyp          = 32
      AND e.TrE_AkwNumer        > 0
LEFT JOIN CDN.PrcKarty akw_prc
       ON akw_prc.Prc_GIDNumer = e.TrE_AkwNumer
      AND e.TrE_AkwTyp          = 944
      AND e.TrE_AkwNumer        > 0
LEFT JOIN CenBase cen
       ON cen.TCN_RodzajCeny = e.TrE_CenaSpr
      AND e.TrE_CenaSpr       > 0
