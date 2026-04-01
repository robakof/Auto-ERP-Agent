-- KSeF FA(2) — SELECT źródłowy dla widoku
-- Granulacja: 1 wiersz = 1 pozycja faktury (FaWiersz)
-- Filtr: TrN_GIDTyp = 2033 (FS — Faktura Sprzedaży)

SELECT

    -- =========================================================
    -- NAGŁÓWEK (stałe)
    -- =========================================================
    'FA'                                                        AS KSeF_KodFormularza,
    2                                                           AS KSeF_WariantFormularza,

    -- =========================================================
    -- PODMIOT1 — Sprzedawca (CDN.Firma, 1 rekord)
    -- =========================================================
    f.Frm_NIP                                                   AS P1_NIP,
    RTRIM(f.Frm_Nazwa1) + ' ' + RTRIM(f.Frm_Nazwa2)            AS P1_PelnaNazwa,
    f.Frm_Kraj                                                  AS P1_KodKraju,
    RTRIM(f.Frm_Ulica)                                          AS P1_AdresL1,
    f.Frm_KodP + ' ' + RTRIM(f.Frm_Miasto)                     AS P1_AdresL2,

    -- =========================================================
    -- PODMIOT2 — Nabywca (CDN.KntKarty)
    -- =========================================================
    RTRIM(k.Knt_Nip)                                            AS P2_NIP,
    CASE WHEN RTRIM(k.Knt_NipPrefiks) = '' THEN 'PL'
         ELSE RTRIM(k.Knt_NipPrefiks) END                      AS P2_PrefiksNIP,
    RTRIM(k.Knt_Nazwa1)                                         AS P2_PelnaNazwa,
    k.Knt_Kraj                                                  AS P2_KodKraju,
    RTRIM(k.Knt_Ulica)                                          AS P2_AdresL1,
    k.Knt_KodP + ' ' + RTRIM(k.Knt_Miasto)                     AS P2_AdresL2,

    -- =========================================================
    -- FA — Nagłówek faktury (CDN.TraNag)
    -- =========================================================
    n.TrN_Waluta                                                AS Fa_KodWaluty,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))      AS Fa_P1_DataWystawienia,
    MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28'))              AS Fa_P1M_Miesiac,
    YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28'))               AS Fa_P1R_Rok,
    -- Data sprzedaży: TrN_DataSprOrg=0 → taka sama jak wystawienia
    CASE WHEN n.TrN_DataSprOrg > 0
         THEN CONVERT(DATE, DATEADD(day, n.TrN_DataSprOrg, '1800-12-28'))
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2,      '1800-12-28'))
    END                                                         AS Fa_P2_DataSprzedazy,
    'FS-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                          AS Fa_P2A_NumerFaktury,
    'VAT'                                                       AS Fa_P6_RodzajTransakcji,
    CASE WHEN NULLIF(RTRIM(n.TrN_NrKorekty), '') IS NULL
         THEN 'VAT' ELSE 'KOR' END                              AS Fa_RodzajFaktury,

    -- =========================================================
    -- FA — VAT per stawka (pivot z CDN.TraVat)
    -- =========================================================
    -- 23%
    v23.NettoR                                                  AS Fa_P13_1_Podstawa23,
    v23.VatR                                                    AS Fa_P14_1_VAT23,
    -- 8%
    v8.NettoR                                                   AS Fa_P13_2_Podstawa8,
    v8.VatR                                                     AS Fa_P14_2_VAT8,
    -- 5%
    v5.NettoR                                                   AS Fa_P13_3_Podstawa5,
    v5.VatR                                                     AS Fa_P14_3_VAT5,
    -- 0%
    v0.NettoR                                                   AS Fa_P13_5_Podstawa0,
    v0.VatR                                                     AS Fa_P14_5_VAT0,
    -- ZW (FlagaVat=2)
    vZW.NettoR                                                  AS Fa_P13_6_PodstawaZW,
    -- NP (FlagaVat=0)
    vNP.NettoR                                                  AS Fa_P13_7_PodstawaNP,

    -- =========================================================
    -- FA — Kwota należności (P_15)
    -- =========================================================
    n.TrN_NettoR + n.TrN_VatR                                   AS Fa_P15_KwotaNaleznosci,

    -- =========================================================
    -- FA — Adnotacje
    -- =========================================================
    CASE WHEN n.TrN_MPP = 1 THEN '1' ELSE '2' END              AS Fa_P16_MPP,
    '2'                                                         AS Fa_P18_SelfBilling,

    -- =========================================================
    -- FaWiersz — Pozycje faktury (CDN.TraElem)
    -- =========================================================
    e.TrE_GIDLp                                                 AS Wiersz_NrPozycji,
    RTRIM(e.TrE_TwrNazwa)                                       AS Wiersz_P7_NazwaTowaru,
    RTRIM(e.TrE_JmZ)                                            AS Wiersz_P8A_JM,
    e.TrE_Ilosc                                                 AS Wiersz_P8B_Ilosc,
    e.TrE_Cena                                                  AS Wiersz_P9A_CenaNettoJedn,
    e.TrE_KsiegowaNetto                                         AS Wiersz_P10_WartoscNetto,
    CASE e.TrE_GrupaPod
        WHEN 'A' THEN '23'
        WHEN 'B' THEN '8'
        WHEN 'C' THEN '5'
        WHEN 'F' THEN '0'
        WHEN 'D' THEN 'ZW'
        WHEN 'E' THEN 'NP'
        ELSE CAST(CAST(e.TrE_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
    END                                                         AS Wiersz_P11_StawkaVAT,
    e.TrE_GrupaPod                                              AS Wiersz_GrupaVAT,
    e.TrE_KsiegowaBrutto - e.TrE_KsiegowaNetto                 AS Wiersz_P12_KwotaVAT,
    ean.EAN                                                     AS Wiersz_GTIN,

    -- =========================================================
    -- Płatność (CDN.TraPlat + CDN.RachunkiBankowe)
    -- =========================================================
    CONVERT(DATE, DATEADD(day, p.TrP_Termin, '1800-12-28'))     AS Plat_TerminPlatnosci,
    CASE p.TrP_FormaNr
        WHEN 10 THEN '1'   -- Gotówka
        WHEN 20 THEN '6'   -- Przelew
        WHEN 50 THEN '3'   -- Karta
        ELSE CAST(p.TrP_FormaNr AS VARCHAR(5))
    END                                                         AS Plat_KodFormyPlatnosci,
    RTRIM(p.TrP_FormaNazwa)                                     AS Plat_FormaPlatnosci_Nazwa,
    CASE WHEN p.TrP_FormaNr = 20 THEN rb.RkB_NrRachunku
         ELSE NULL END                                          AS Plat_NrRachunkuBankowego,

    -- =========================================================
    -- Klucze techniczne (do generowania i grupowania XML)
    -- =========================================================
    n.TrN_GIDTyp                                                AS _GIDTyp,
    n.TrN_GIDNumer                                              AS _GIDNumer,
    n.TrN_GIDFirma                                              AS _GIDFirma

FROM CDN.TraNag n

-- Sprzedawca (stały, 1 rekord)
CROSS JOIN (SELECT TOP 1
    Frm_NIP, Frm_Nazwa1, Frm_Nazwa2,
    Frm_Kraj, Frm_Ulica, Frm_KodP, Frm_Miasto
    FROM CDN.Firma) f

-- Nabywca
JOIN CDN.KntKarty k
    ON  k.Knt_GIDNumer = n.TrN_KntNumer
    AND k.Knt_GIDTyp   = 32

-- Pozycje faktury
JOIN CDN.TraElem e
    ON  e.TrE_GIDTyp   = n.TrN_GIDTyp
    AND e.TrE_GIDNumer = n.TrN_GIDNumer

-- VAT 23%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR,
           SUM(TrV_VatR)   AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '23.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v23 ON v23.TrV_GIDTyp = n.TrN_GIDTyp AND v23.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 8%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR,
           SUM(TrV_VatR)   AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '8.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v8 ON v8.TrV_GIDTyp = n.TrN_GIDTyp AND v8.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 5%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR,
           SUM(TrV_VatR)   AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '5.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v5 ON v5.TrV_GIDTyp = n.TrN_GIDTyp AND v5.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 0%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR,
           SUM(TrV_VatR)   AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '0.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v0 ON v0.TrV_GIDTyp = n.TrN_GIDTyp AND v0.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT ZW (zwolniony, FlagaVat=2)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 2
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) vZW ON vZW.TrV_GIDTyp = n.TrN_GIDTyp AND vZW.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT NP (nie podlega, FlagaVat=0)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 0
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) vNP ON vNP.TrV_GIDTyp = n.TrN_GIDTyp AND vNP.TrV_GIDNumer = n.TrN_GIDNumer

-- Płatność (pierwsza rata/termin na fakturze)
LEFT JOIN (
    SELECT TrP_GIDTyp, TrP_GIDNumer, TrP_Termin,
           TrP_FormaNr, TrP_FormaNazwa, TrP_RachBank,
           ROW_NUMBER() OVER (
               PARTITION BY TrP_GIDTyp, TrP_GIDNumer
               ORDER BY TrP_GIDLp
           ) AS rn
    FROM CDN.TraPlat
) p ON  p.TrP_GIDTyp   = n.TrN_GIDTyp
    AND p.TrP_GIDNumer  = n.TrN_GIDNumer
    AND p.rn            = 1

-- EAN towaru (CDN.TwrZasoby, jeden EAN per towar)
LEFT JOIN (
    SELECT TwZ_TwrNumer, MIN(RTRIM(TwZ_Ean)) AS EAN
    FROM CDN.TwrZasoby
    WHERE TwZ_Ean IS NOT NULL AND RTRIM(TwZ_Ean) <> ''
    GROUP BY TwZ_TwrNumer
) ean ON ean.TwZ_TwrNumer = e.TrE_TwrNumer

-- Rachunek bankowy (tylko dla przelewu)
LEFT JOIN CDN.RachunkiBankowe rb
    ON  rb.RkB_Id     = p.TrP_RachBank
    AND p.TrP_FormaNr = 20

WHERE n.TrN_GIDTyp = 2033

ORDER BY n.TrN_GIDNumer, e.TrE_GIDLp
