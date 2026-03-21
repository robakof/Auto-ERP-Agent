USE [ERPXL_CEIM];
GO

CREATE OR ALTER VIEW AIBI.MagElem AS

-- MagElem draft SELECT
-- Brudnopis widoku BI dla CDN.MagElem (pozycje dokumentów magazynowych)
-- Nie używać CREATE VIEW — wyłącznie SELECT
-- Tabela główna: CDN.MagElem | Baseline: ~752 570 wierszy
-- JOINy: CDN.MagNag (INNER), CDN.TwrKarty (INNER)

SELECT

    -- === IDENTYFIKACJA DOKUMENTU ===
    CASE e.MaE_GIDTyp
        WHEN 1089 THEN 'Przyjecie magazynowe'
        WHEN 1093 THEN 'Awizo dostawy'
        WHEN 1601 THEN 'Wydanie magazynowe'
        WHEN 1605 THEN 'Zlecenie wydania z magazynu'
        ELSE 'Nieznane (' + CAST(e.MaE_GIDTyp AS VARCHAR(10)) + ')'
    END                                                                 AS Typ_Dokumentu,

    e.MaE_GIDNumer                                                      AS ID_Dokumentu,

    -- === NUMER DOKUMENTU (z JOINu MagNag) ===
    CASE n.MaN_GIDTyp
        WHEN 1089 THEN 'PM'
        WHEN 1093 THEN 'AWD'
        WHEN 1601 THEN 'WM'
        WHEN 1605 THEN 'ZWM'
        ELSE CAST(n.MaN_GIDTyp AS VARCHAR(10))
    END
    + '-' + CAST(n.MaN_TrNNumer AS VARCHAR(10))
    + '/' + RIGHT('0' + CAST(n.MaN_TrNMiesiac AS VARCHAR(2)), 2)
    + '/' + RIGHT(CAST(n.MaN_TrNRok AS VARCHAR(4)), 2)
    + CASE WHEN RTRIM(n.MaN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(n.MaN_TrNSeria) END
                                                                        AS Nr_Dokumentu,

    -- === POZYCJA ===
    e.MaE_GIDLp                                                         AS Nr_Pozycji,
    e.MaE_Pozycja                                                        AS Pozycja_Na_Dokumencie,

    -- === TOWAR ===
    e.MaE_TwrNumer                                                      AS ID_Towaru,
    RTRIM(e.MaE_TwrKod)                                                 AS Kod_Towaru,
    RTRIM(t.Twr_Nazwa)                                                   AS Nazwa_Towaru,

    -- === CECHY / PARTIE ===
    NULLIF(RTRIM(e.MaE_Cecha), '')                                       AS Cecha,
    NULLIF(RTRIM(e.MaE_Cecha2), '')                                     AS Cecha2,
    NULLIF(RTRIM(e.MaE_Ean), '')                                        AS EAN,
    e.MaE_TPaId                                                         AS ID_Partii,

    -- === ILOŚĆ I JEDNOSTKI ===
    e.MaE_Ilosc                                                         AS Ilosc,
    RTRIM(e.MaE_JmZ)                                                     AS Jednostka_Pomocnicza,
    CASE e.MaE_TypJm
        WHEN 1 THEN 'Ciagly'
        WHEN 2 THEN 'Dyskretny'
        ELSE 'Nieznane (' + CAST(e.MaE_TypJm AS VARCHAR(10)) + ')'
    END                                                                 AS Typ_Przelicznika_JM,
    e.MaE_PrzeliczM                                                     AS Przelicznik_Mianownik,
    e.MaE_PrzeliczL                                                     AS Przelicznik_Licznik,
    CASE WHEN e.MaE_JednostkaLog = 0 THEN NULL ELSE e.MaE_JednostkaLog END
                                                                        AS ID_Jednostki_Logistycznej,

    -- === OPIS ===
    NULLIF(RTRIM(e.MaE_Opis), '')                                       AS Opis,

    -- === STATUS ===
    CASE e.MaE_Status
        WHEN 0 THEN 'Niezatwierdzony'
        WHEN 1 THEN 'Zatwierdzony'
        WHEN 2 THEN 'W realizacji'
        WHEN 4 THEN 'Zamkniety'
        WHEN 5 THEN 'Zamkniety bez realizacji'
        WHEN 6 THEN 'Zamkniety do edycji'
        ELSE 'Nieznane (' + CAST(e.MaE_Status AS VARCHAR(10)) + ')'
    END                                                                 AS Status_Pozycji

FROM CDN.MagElem e
INNER JOIN CDN.MagNag n
    ON  n.MaN_GIDNumer = e.MaE_GIDNumer
    AND n.MaN_GIDTyp   = e.MaE_GIDTyp
INNER JOIN CDN.TwrKarty t
    ON  t.Twr_GIDNumer = e.MaE_TwrNumer
