USE [ERPXL_CEIM];
GO

CREATE OR ALTER VIEW AIBI.ZamElem AS

-- BRUDNOPIS -- wylacznie SELECT, bez CREATE VIEW
-- AIBI.ZamElem -- pozycje zamowien (ZS/ZZ/OFS/OFZ)
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
    -- === IDENTYFIKACJA ===
    e.ZaE_GIDNumer                                                      AS ID_Zamowienia,
    e.ZaE_GIDLp                                                         AS Nr_Pozycji,
    e.ZaE_Pozycja                                                        AS Pozycja_Na_Dokumencie,

    -- === NUMER I TYP DOKUMENTU (z JOIN CDN.ZamNag) ===
    CASE n.ZaN_ZamTyp
        WHEN 640  THEN 'OFZ'
        WHEN 768  THEN 'OFS'
        WHEN 1152 THEN 'ZZ'
        WHEN 1280 THEN 'ZS'
        ELSE 'ZAM'
    END
    + '-' + CAST(n.ZaN_ZamNumer AS VARCHAR(10))
    + '/' + RIGHT('0' + CAST(n.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
    + '/' + RIGHT(CAST(n.ZaN_ZamRok AS VARCHAR(4)), 2)
    + '/' + RTRIM(n.ZaN_ZamSeria)                                       AS Numer_Dokumentu,

    CASE n.ZaN_ZamTyp
        WHEN 640  THEN 'Oferta zakupu'
        WHEN 768  THEN 'Oferta sprzedazy'
        WHEN 1152 THEN 'Zamowienie zakupu'
        WHEN 1280 THEN 'Zamowienie sprzedazy'
        WHEN 2688 THEN 'Zapytanie ofertowe zakupu'
        WHEN 2816 THEN 'Zapytanie ofertowe sprzedazy'
        ELSE 'Nieznane (' + CAST(n.ZaN_ZamTyp AS VARCHAR(10)) + ')'
    END                                                                  AS Typ_Zamowienia,

    CASE n.ZaN_Stan
        WHEN 1  THEN 'Oferta'
        WHEN 2  THEN 'Zamowienie'
        WHEN 3  THEN 'Potwierdzone'
        WHEN 4  THEN 'Zaakceptowane'
        WHEN 5  THEN 'W realizacji'
        WHEN 19 THEN 'Odrzucone'
        WHEN 21 THEN 'Zrealizowane'
        WHEN 35 THEN 'Anulowane (potwierdzone)'
        WHEN 51 THEN 'Anulowane (zarchiwizowane)'
        WHEN 53 THEN 'Zamkniete w realizacji'
        ELSE 'Nieznane (' + CAST(n.ZaN_Stan AS VARCHAR(10)) + ')'
    END                                                                  AS Stan_Zamowienia,

    CASE WHEN n.ZaN_DataWystawienia > 0
         THEN CAST(DATEADD(d, n.ZaN_DataWystawienia, '18001228') AS DATE)
         ELSE NULL
    END                                                                  AS Data_Wystawienia,

    -- === TOWAR ===
    CASE WHEN e.ZaE_TwrNumer = 0 THEN NULL ELSE e.ZaE_TwrNumer END     AS ID_Towaru,
    RTRIM(e.ZaE_TwrNazwa)                                               AS Nazwa_Towaru,
    RTRIM(e.ZaE_TwrKod)                                                 AS Kod_Towaru,

    -- === KONTRAHENT POZYCJI ===
    CASE WHEN e.ZaE_KntNumer = 0 THEN NULL ELSE e.ZaE_KntNumer END     AS ID_Kontrahenta_Pozycji,
    knt_pos.Knt_Akronim                                                 AS Akronim_Kontrahenta_Pozycji,
    knt_pos.Knt_Nazwa1                                                  AS Nazwa_Kontrahenta_Pozycji,

    -- === AKWIZYTOR ===
    CASE WHEN e.ZaE_AkwNumer = 0 OR e.ZaE_AkwTyp != 32 THEN NULL
         ELSE e.ZaE_AkwNumer END                                        AS ID_Akwizytora,
    akw_knt.Knt_Akronim                                                 AS Akwizytor_Akronim,

    -- === MAGAZYN ===
    e.ZaE_MagNumer                                                      AS ID_Magazynu,
    RTRIM(mag.MAG_Kod)                                                  AS Kod_Magazynu,
    RTRIM(mag.MAG_Nazwa)                                                AS Nazwa_Magazynu,

    -- === CZAS UTWORZENIA (Clarion TIMESTAMP) ===
    CASE WHEN e.ZaE_TStamp = 0 THEN NULL
         ELSE CAST(DATEADD(ss, e.ZaE_TStamp, '1990-01-01') AS DATETIME)
    END                                                                  AS DataCzas_Utworzenia,

    -- === ILOSC I JEDNOSTKA MIARY ===
    e.ZaE_Ilosc                                                         AS Ilosc,
    RTRIM(e.ZaE_JmZ)                                                    AS Jednostka_Miary,
    e.ZaE_PrzeliczL                                                     AS Przelicznik_JM,

    -- === VAT ===
    e.ZaE_GrupaPod                                                      AS Grupa_VAT,
    e.ZaE_StawkaPod                                                     AS Stawka_VAT,

    -- === WALUTA ===
    e.ZaE_Waluta                                                        AS Waluta,

    -- === CENY I WARTOSCI ===
    e.ZaE_CenaKatalogowa                                                AS Cena_Katalogowa,
    e.ZaE_CenaOferowana                                                 AS Cena_Oferowana,
    e.ZaE_CenaUzgodniona                                                AS Cena_Uzgodniona,
    e.ZaE_Rabat                                                         AS Rabat_Procent,
    e.ZaE_WartoscPoRabacie                                              AS Wartosc_Po_Rabacie,
    e.ZaE_RabatPromocyjny                                               AS Rabat_Promocyjny,
    e.ZaE_RabatKorekta                                                  AS Rabat_Korekta,

    -- === CENNIK ===
    CASE WHEN e.ZaE_CenaSpr IN (0, -32000) THEN NULL
         ELSE e.ZaE_CenaSpr END                                         AS ID_Cennika,
    cen.TCN_Nazwa                                                       AS Nazwa_Cennika,

    -- === CECHA ===
    NULLIF(RTRIM(e.ZaE_Cecha), '')                                      AS Cecha_Towaru,

    -- === ROWNA ILOSC x CENA ===
    CASE e.ZaE_Rownanie
        WHEN 0 THEN 'Nieaktywne'
        WHEN 1 THEN 'Aktywne'
        ELSE 'Nieznane (' + CAST(e.ZaE_Rownanie AS VARCHAR(5)) + ')'
    END                                                                  AS Rowna_IloscxCena,

    -- === DATY POZYCJI ===
    CASE WHEN e.ZaE_DataPotwDst BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, e.ZaE_DataPotwDst, '18001228') AS DATE)
         ELSE NULL END                                                   AS Data_Potwierdzenia_Dostawy,
    CASE WHEN e.ZaE_DataAktywacjiRez BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, e.ZaE_DataAktywacjiRez, '18001228') AS DATE)
         ELSE NULL END                                                   AS Data_Aktywacji_Rezerwacji,
    CASE WHEN e.ZaE_DataWaznosciRez BETWEEN 1 AND 90000
         THEN CAST(DATEADD(d, e.ZaE_DataWaznosciRez, '18001228') AS DATE)
         ELSE NULL END                                                   AS Data_Waznosci_Rezerwacji,
    e.ZaE_DataOdZam                                                     AS Dni_Do_Realizacji,

    -- === E-SKLEP ===
    CASE WHEN e.ZaE_OddElemId = 0 THEN NULL
         ELSE e.ZaE_OddElemId END                                       AS ID_Pozycji_eSklepu

FROM CDN.ZamElem e
JOIN CDN.ZamNag n
     ON n.ZaN_GIDNumer = e.ZaE_GIDNumer
LEFT JOIN CDN.KntKarty knt_pos
       ON knt_pos.Knt_GIDNumer = e.ZaE_KntNumer
      AND e.ZaE_KntNumer       > 0
LEFT JOIN CDN.KntKarty akw_knt
       ON akw_knt.Knt_GIDNumer = e.ZaE_AkwNumer
      AND e.ZaE_AkwTyp          = 32
      AND e.ZaE_AkwNumer        > 0
LEFT JOIN CDN.Magazyny mag
       ON mag.MAG_GIDNumer = e.ZaE_MagNumer
      AND mag.MAG_GIDTyp   = 208
LEFT JOIN CenBase cen
       ON cen.TCN_RodzajCeny = e.ZaE_CenaSpr
      AND e.ZaE_CenaSpr       > 0
