-- KSeF FA(3) KOR-SKONTO — SELECT źródłowy dla korekt skontowych (rabat wartościowy)
-- Korekta skontowa: TrN_GIDTyp = 2041, TrN_ZwrNumer = 0 (brak bezpośredniego linka)
-- Powiązanie: FSK-skonto → bufor(y) 2009 (po knt+dacie) → oryginalne FS (2033)
-- UWAGA: 1 FSK-skonto może korygować WIELE oryginalnych FS (zbiorcze skonto)
-- Agregacja per stawka VAT (nie per towar) — skonto to korekta wartościowa zbiorcza
-- StanPrzed = sumy netto/VAT z WSZYSTKICH oryginalnych FS per stawka (TraVat)
-- StanPo = oryginał + delta ze skonta per stawka
-- Granulacja: 2 wiersze per stawkę VAT (CROSS JOIN StanPrzed 1/0)

WITH buf_match AS (
    -- Znajdź bufor(y) 2009 powiązane z FSK-skonto
    -- Matching: ten sam kontrahent + data wystawienia (bez kwoty — skonto zbiorcze)
    -- Deduplikacja: DISTINCT orig_gid bo wiele buforów może wskazywać ten sam oryginał
    SELECT DISTINCT
        fsk.TrN_GIDNumer  AS fsk_gid,
        buf.TrN_ZwrNumer  AS orig_gid
    FROM CDN.TraNag fsk
    JOIN CDN.TraNag buf
        ON  buf.TrN_GIDTyp   = 2009
        AND buf.TrN_KntNumer  = fsk.TrN_KntNumer
        AND buf.TrN_Data2     = fsk.TrN_Data2
        AND buf.TrN_ZwrNumer  > 0
        AND buf.TrN_ZwrTyp    = 2033
    WHERE fsk.TrN_GIDTyp  = 2041
      AND fsk.TrN_ZwrNumer = 0
),

-- Wybierz jedną FS do nagłówka korekty (najnowsza = max GID)
orig_header AS (
    SELECT
        fsk_gid,
        MAX(orig_gid) AS orig_gid
    FROM buf_match
    GROUP BY fsk_gid
),

-- Sumy VAT z WSZYSTKICH oryginalnych FS per stawka
vat_orig AS (
    SELECT
        bm.fsk_gid,
        ov.TrV_StawkaPod,
        ov.TrV_FlagaVat,
        SUM(ov.TrV_NettoR)              AS NettoOrg,
        SUM(ov.TrV_VatR)                AS VatOrg,
        ROW_NUMBER() OVER (
            PARTITION BY bm.fsk_gid
            ORDER BY ov.TrV_FlagaVat, ov.TrV_StawkaPod DESC
        ) AS nr_poz
    FROM buf_match bm
    JOIN CDN.TraVat ov
        ON  ov.TrV_GIDTyp   = 2033
        AND ov.TrV_GIDNumer  = bm.orig_gid
    GROUP BY bm.fsk_gid, ov.TrV_StawkaPod, ov.TrV_FlagaVat
),

-- Delta VAT ze skonta per stawka
vat_delta AS (
    SELECT
        TrV_GIDNumer,
        TrV_StawkaPod,
        SUM(TrV_NettoR)                 AS NettoDelta,
        SUM(TrV_VatR)                   AS VatDelta
    FROM CDN.TraVat
    WHERE TrV_GIDTyp = 2041
    GROUP BY TrV_GIDNumer, TrV_StawkaPod
)

SELECT

    -- =========================================================
    -- NAGŁÓWEK (stałe)
    -- =========================================================
    'FA'                                                        AS KSeF_KodFormularza,
    3                                                           AS KSeF_WariantFormularza,

    -- =========================================================
    -- PODMIOT1 — Sprzedawca (CDN.Firma)
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
    CASE WHEN RTRIM(k.Knt_Ulica) = ''
         THEN k.Knt_KodP + ' ' + RTRIM(k.Knt_Miasto)
         ELSE RTRIM(k.Knt_Ulica) END                            AS P2_AdresL1,
    CASE WHEN RTRIM(k.Knt_Ulica) = '' THEN NULL
         ELSE k.Knt_KodP + ' ' + RTRIM(k.Knt_Miasto) END       AS P2_AdresL2,

    -- =========================================================
    -- FA — Nagłówek korekty (CDN.TraNag n = FSK-skonto)
    -- =========================================================
    n.TrN_Waluta                                                AS Fa_KodWaluty,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))      AS Fa_P1_DataWystawienia,
    MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28'))              AS Fa_P1M_Miesiac,
    YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28'))               AS Fa_P1R_Rok,
    CASE WHEN n.TrN_DataSprOrg > 0
         THEN CONVERT(DATE, DATEADD(day, n.TrN_DataSprOrg, '1800-12-28'))
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2,      '1800-12-28'))
    END                                                         AS Fa_P2_DataSprzedazy,
    'FSK-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                          AS Fa_P2A_NumerFaktury,
    'KOR'                                                       AS Fa_RodzajFaktury,

    -- =========================================================
    -- DANE FAKTURY KORYGOWANEJ (z oryginału FS przez bufor 2009)
    -- =========================================================
    CONVERT(DATE, DATEADD(day, orig.TrN_Data2, '1800-12-28'))   AS Kor_DataWystFaKorygowanej,
    'FS-' + CAST(orig.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(orig.TrN_TrNSeria)                       AS Kor_NrFaKorygowanej,
    RTRIM(COALESCE(
        NULLIF(CAST(op.TnO_Opis AS VARCHAR(MAX)), ''),
        NULLIF(n.TrN_PrzyczynaKorekty, ''),
        'skonto'
    ))                                                          AS Kor_PrzyczynaKorekty,

    -- =========================================================
    -- FA — VAT per stawka (pivot z CDN.TraVat FSK-skonto) — kwoty RÓŻNIC (delta)
    -- =========================================================
    sv23.NettoR                                                 AS Fa_P13_1_Podstawa23,
    sv23.VatR                                                   AS Fa_P14_1_VAT23,
    sv8.NettoR                                                  AS Fa_P13_2_Podstawa8,
    sv8.VatR                                                    AS Fa_P14_2_VAT8,
    sv5.NettoR                                                  AS Fa_P13_3_Podstawa5,
    sv5.VatR                                                    AS Fa_P14_3_VAT5,
    sv0.NettoR                                                  AS Fa_P13_5_Podstawa0,
    sv0.VatR                                                    AS Fa_P14_5_VAT0,
    svZW.NettoR                                                 AS Fa_P13_6_PodstawaZW,
    svNP.NettoR                                                 AS Fa_P13_7_PodstawaNP,

    n.TrN_NettoR + n.TrN_VatR                                   AS Fa_P15_KwotaNaleznosci,

    CASE WHEN n.TrN_MPP = 1 THEN '1' ELSE '2' END              AS Fa_P16_MPP,
    '2'                                                         AS Fa_P18_SelfBilling,

    -- =========================================================
    -- FaWiersz — 1 para per stawkę VAT (StanPrzed + StanPo)
    -- Agregacja per stawka z TraVat oryginalnej FS + delta ze skonta
    -- =========================================================
    vo.nr_poz                                                   AS Wiersz_NrPozycji,
    sp.StanPrzed                                                AS Wiersz_StanPrzed,

    -- Data korekty: NULL dla StanPrzed, data wystawienia korekty dla StanPo
    CASE WHEN sp.StanPrzed = 1
         THEN NULL
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))
    END                                                         AS Wiersz_DataKorekty,

    -- Nazwa pozycji: StanPrzed = nr faktury korygowanej, StanPo = "Po skoncie"
    CASE WHEN sp.StanPrzed = 1
         THEN 'FS-' + CAST(orig.TrN_TrNNumer AS VARCHAR(20))
              + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
              + '/' + RIGHT(CAST(YEAR(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
              + '/' + RTRIM(orig.TrN_TrNSeria)
         ELSE 'Po skoncie'
    END                                                         AS Wiersz_P7_NazwaTowaru,
    NULL                                                        AS Wiersz_Indeks,
    NULL                                                        AS Wiersz_PKWiU,
    'szt.'                                                      AS Wiersz_P8A_JM,

    -- Ilość = 1 (pozycja zbiorcza per stawka)
    CAST(1 AS DECIMAL(18,4))                                    AS Wiersz_P8B_Ilosc,

    -- Cena brutto = (netto + VAT) / 1
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(vo.NettoOrg + vo.VatOrg, 2)
         ELSE ROUND((vo.NettoOrg + COALESCE(dv.NettoDelta, 0))
                   + (vo.VatOrg  + COALESCE(dv.VatDelta, 0)), 2)
    END                                                         AS Wiersz_P9B_CenaBrutto,

    -- Wartość netto
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(vo.NettoOrg, 2)
         ELSE ROUND(vo.NettoOrg + COALESCE(dv.NettoDelta, 0), 2)
    END                                                         AS Wiersz_P11A_WartoscNetto,

    -- Kwota VAT
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(vo.VatOrg, 2)
         ELSE ROUND(vo.VatOrg + COALESCE(dv.VatDelta, 0), 2)
    END                                                         AS Wiersz_P11Vat,

    -- Stawka VAT (symbol: 23/8/5/0/ZW/NP)
    CASE
        WHEN vo.TrV_StawkaPod = '23.00' THEN '23'
        WHEN vo.TrV_StawkaPod = '8.00'  THEN '8'
        WHEN vo.TrV_StawkaPod = '5.00'  THEN '5'
        WHEN vo.TrV_StawkaPod = '0.00'  THEN '0'
        WHEN vo.TrV_FlagaVat  = 2       THEN 'ZW'
        WHEN vo.TrV_FlagaVat  = 0       THEN 'NP'
        ELSE CAST(CAST(vo.TrV_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
    END                                                         AS Wiersz_P12_StawkaVAT,

    NULL                                                        AS Wiersz_GTIN,

    -- =========================================================
    -- Płatność (CDN.TraPlat + CDN.Rejestry)
    -- =========================================================
    CONVERT(DATE, DATEADD(day, p.TrP_Termin, '1800-12-28'))     AS Plat_TerminPlatnosci,
    CASE p.TrP_FormaNr
        WHEN 10 THEN '1'   -- Gotówka
        WHEN 20 THEN '6'   -- Przelew
        WHEN 50 THEN '3'   -- Karta
        ELSE CAST(p.TrP_FormaNr AS VARCHAR(5))
    END                                                         AS Plat_KodFormyPlatnosci,
    RTRIM(p.TrP_FormaNazwa)                                     AS Plat_FormaPlatnosci_Nazwa,
    CASE WHEN p.TrP_FormaNr = 20 THEN kar.KAR_NrRachunku
         ELSE NULL END                                          AS Plat_NrRachunkuBankowego,
    p.TrP_Rozliczona                                            AS Plat_Rozliczona,
    CASE WHEN p.TrP_Rozliczona = 1
         THEN CONVERT(DATE, DATEADD(day, p.TrP_DataRozliczenia, '1800-12-28'))
         ELSE NULL END                                          AS Plat_DataRozliczenia,

    -- =========================================================
    -- Klucze techniczne
    -- =========================================================
    n.TrN_GIDTyp                                                AS _GIDTyp,
    n.TrN_GIDNumer                                              AS _GIDNumer,
    n.TrN_GIDFirma                                              AS _GIDFirma

FROM CDN.TraNag n

-- Jedna oryginalna FS do nagłówka (najnowsza z powiązanych)
JOIN orig_header oh
    ON  oh.fsk_gid = n.TrN_GIDNumer

-- Oryginalna faktura FS (do danych nagłówkowych korekty)
JOIN CDN.TraNag orig
    ON  orig.TrN_GIDNumer = oh.orig_gid
    AND orig.TrN_GIDTyp   = 2033

-- Opis korekty
LEFT JOIN CDN.TrNOpisy op
    ON  op.TnO_TrnTyp   = n.TrN_GIDTyp
    AND op.TnO_TrnFirma = n.TrN_GIDFirma
    AND op.TnO_TrnNumer = n.TrN_GIDNumer
    AND op.TnO_TrnLp    = 0

-- Sprzedawca
CROSS JOIN (SELECT TOP 1
    Frm_NIP, Frm_Nazwa1, Frm_Nazwa2,
    Frm_Kraj, Frm_Ulica, Frm_KodP, Frm_Miasto
    FROM CDN.Firma) f

-- Rejestr bankowy firmy
CROSS JOIN (SELECT TOP 1
    KAR_NrRachunku
    FROM CDN.Rejestry
    WHERE KAR_Typ        = 2
      AND KAR_Waluta     = 'PLN'
      AND KAR_Archiwalne = 0
    ORDER BY KAR_GIDNumer) kar

-- Nabywca
JOIN CDN.KntKarty k
    ON  k.Knt_GIDNumer = n.TrN_KntNumer
    AND k.Knt_GIDTyp   = 32

-- Sumy VAT z oryginalnej FS (1 wiersz per stawka)
JOIN vat_orig vo
    ON  vo.fsk_gid = n.TrN_GIDNumer

-- Delta VAT ze skonta (per stawka)
LEFT JOIN vat_delta dv
    ON  dv.TrV_GIDNumer  = n.TrN_GIDNumer
    AND dv.TrV_StawkaPod = vo.TrV_StawkaPod

-- Dwa wiersze per stawkę (StanPrzed + StanPo)
CROSS JOIN (VALUES (1), (0)) sp(StanPrzed)

-- VAT 23% (z FSK-skonto, dla nagłówka P_13/P_14)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '23.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) sv23 ON sv23.TrV_GIDTyp = n.TrN_GIDTyp AND sv23.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 8%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '8.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) sv8 ON sv8.TrV_GIDTyp = n.TrN_GIDTyp AND sv8.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 5%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '5.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) sv5 ON sv5.TrV_GIDTyp = n.TrN_GIDTyp AND sv5.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 0%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '0.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) sv0 ON sv0.TrV_GIDTyp = n.TrN_GIDTyp AND sv0.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT ZW (FlagaVat=2)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 2
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) svZW ON svZW.TrV_GIDTyp = n.TrN_GIDTyp AND svZW.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT NP (FlagaVat=0)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 0
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) svNP ON svNP.TrV_GIDTyp = n.TrN_GIDTyp AND svNP.TrV_GIDNumer = n.TrN_GIDNumer

-- Płatność (pierwsza rata)
LEFT JOIN (
    SELECT TrP_GIDTyp, TrP_GIDNumer, TrP_Termin,
           TrP_FormaNr, TrP_FormaNazwa,
           TrP_Rozliczona, TrP_DataRozliczenia,
           ROW_NUMBER() OVER (
               PARTITION BY TrP_GIDTyp, TrP_GIDNumer
               ORDER BY TrP_GIDLp
           ) AS rn
    FROM CDN.TraPlat
) p ON  p.TrP_GIDTyp   = n.TrN_GIDTyp
    AND p.TrP_GIDNumer  = n.TrN_GIDNumer
    AND p.rn            = 1


WHERE n.TrN_GIDTyp = 2041
  AND n.TrN_Stan IN (3, 4, 5)

ORDER BY n.TrN_GIDNumer, vo.nr_poz, sp.StanPrzed DESC
