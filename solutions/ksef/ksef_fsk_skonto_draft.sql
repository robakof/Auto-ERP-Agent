-- KSeF FA(3) KOR-SKONTO — SELECT źródłowy dla korekt skontowych (rabat wartościowy)
-- Korekta skontowa: TrN_GIDTyp = 2041, TrN_ZwrNumer = 0 (brak bezpośredniego linka)
-- Powiązanie: FSK-skonto → bufor 2009 (po knt+kwocie+dacie) → oryginalna FS (2033)
-- Pozycje z bufora 2009 (TrE_Ilosc=0, TrE_KsiegowaNetto<0 = rabat per towar)
-- StanPrzed = wartości z oryginalnej FS (po TwrNumer)
-- StanPo = StanPrzed + delta z bufora (KsiegowaNetto ujemne = rabat)
-- Granulacja: 2 wiersze per pozycja (CROSS JOIN StanPrzed 1/0)

WITH buf_match AS (
    -- Znajdź bufor 2009 powiązany z FSK-skonto
    -- Matching: ten sam kontrahent, kwota netto, data wystawienia
    SELECT
        fsk.TrN_GIDNumer  AS fsk_gid,
        buf.TrN_GIDNumer  AS buf_gid,
        buf.TrN_GIDTyp    AS buf_typ,
        buf.TrN_ZwrNumer  AS orig_gid,
        ROW_NUMBER() OVER (
            PARTITION BY fsk.TrN_GIDNumer
            ORDER BY ABS(buf.TrN_GIDNumer - fsk.TrN_GIDNumer)
        ) AS rn
    FROM CDN.TraNag fsk
    JOIN CDN.TraNag buf
        ON  buf.TrN_GIDTyp   = 2009
        AND buf.TrN_KntNumer  = fsk.TrN_KntNumer
        AND buf.TrN_NettoR    = fsk.TrN_NettoR
        AND buf.TrN_Data2     = fsk.TrN_Data2
        AND buf.TrN_ZwrNumer  > 0
        AND buf.TrN_ZwrTyp    = 2033
    WHERE fsk.TrN_GIDTyp  = 2041
      AND fsk.TrN_ZwrNumer = 0
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
    -- FA — VAT per stawka (pivot z CDN.TraVat) — kwoty RÓŻNIC (delta)
    -- =========================================================
    v23.NettoR                                                  AS Fa_P13_1_Podstawa23,
    v23.VatR                                                    AS Fa_P14_1_VAT23,
    v8.NettoR                                                   AS Fa_P13_2_Podstawa8,
    v8.VatR                                                     AS Fa_P14_2_VAT8,
    v5.NettoR                                                   AS Fa_P13_3_Podstawa5,
    v5.VatR                                                     AS Fa_P14_3_VAT5,
    v0.NettoR                                                   AS Fa_P13_5_Podstawa0,
    v0.VatR                                                     AS Fa_P14_5_VAT0,
    vZW.NettoR                                                  AS Fa_P13_6_PodstawaZW,
    vNP.NettoR                                                  AS Fa_P13_7_PodstawaNP,

    n.TrN_NettoR + n.TrN_VatR                                   AS Fa_P15_KwotaNaleznosci,

    CASE WHEN n.TrN_MPP = 1 THEN '1' ELSE '2' END              AS Fa_P16_MPP,
    '2'                                                         AS Fa_P18_SelfBilling,

    -- =========================================================
    -- FaWiersz — para wierszy per pozycja (StanPrzed + StanPo)
    -- Pozycje z bufora 2009, wartości oryginalne z FS
    -- =========================================================
    be.TrE_GIDLp                                                AS Wiersz_NrPozycji,
    sp.StanPrzed                                                AS Wiersz_StanPrzed,

    -- Data korekty: NULL dla StanPrzed, data wystawienia korekty dla StanPo
    CASE WHEN sp.StanPrzed = 1
         THEN NULL
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))
    END                                                         AS Wiersz_DataKorekty,

    -- Atrybuty stałe (takie same w StanPrzed i StanPo)
    RTRIM(be.TrE_TwrNazwa)                                      AS Wiersz_P7_NazwaTowaru,
    RTRIM(be.TrE_TwrKod)                                        AS Wiersz_Indeks,
    NULL                                                        AS Wiersz_PKWiU,
    RTRIM(be.TrE_JmZ)                                           AS Wiersz_P8A_JM,

    -- Ilość: taka sama przed i po (skonto nie zmienia ilości)
    COALESCE(oe.IloscOrg, 0)                                    AS Wiersz_P8B_Ilosc,

    -- Cena brutto jednostkowa = cena netto * (1 + stawka/100)
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(
               COALESCE(oe.CenaOrg, be.TrE_Cena)
               * (1 + CASE COALESCE(oe.GrupaOrg, be.TrE_GrupaPod)
                        WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                        ELSE 0 END)
             , 2)
         ELSE ROUND(
               (COALESCE(oe.NettoOrg, 0) + be.TrE_KsiegowaNetto)
               / NULLIF(COALESCE(oe.IloscOrg, 1), 0)
               * (1 + CASE COALESCE(oe.GrupaOrg, be.TrE_GrupaPod)
                        WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                        ELSE 0 END)
             , 2)
    END                                                         AS Wiersz_P9B_CenaBrutto,

    -- Wartość netto pozycji
    CASE WHEN sp.StanPrzed = 1
         THEN COALESCE(oe.NettoOrg, 0)
         ELSE COALESCE(oe.NettoOrg, 0) + be.TrE_KsiegowaNetto
    END                                                         AS Wiersz_P11A_WartoscNetto,

    -- Kwota VAT pozycji
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(
               COALESCE(oe.NettoOrg, 0)
               * CASE COALESCE(oe.GrupaOrg, be.TrE_GrupaPod)
                   WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                   ELSE 0 END
             , 2)
         ELSE ROUND(
               (COALESCE(oe.NettoOrg, 0) + be.TrE_KsiegowaNetto)
               * CASE COALESCE(oe.GrupaOrg, be.TrE_GrupaPod)
                   WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                   ELSE 0 END
             , 2)
    END                                                         AS Wiersz_P11Vat,

    -- Stawka VAT (symbol: 23/8/5/0/ZW/NP)
    CASE COALESCE(oe.GrupaOrg, be.TrE_GrupaPod)
        WHEN 'A' THEN '23' WHEN 'B' THEN '8' WHEN 'C' THEN '5'
        WHEN 'F' THEN '0' WHEN 'D' THEN 'ZW' WHEN 'E' THEN 'NP'
        ELSE CAST(CAST(be.TrE_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
    END                                                         AS Wiersz_P12_StawkaVAT,

    NULLIF(RTRIM(tk.Twr_Ean), '')                               AS Wiersz_GTIN,

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

    -- =========================================================
    -- Klucze techniczne
    -- =========================================================
    n.TrN_GIDTyp                                                AS _GIDTyp,
    n.TrN_GIDNumer                                              AS _GIDNumer,
    n.TrN_GIDFirma                                              AS _GIDFirma

FROM CDN.TraNag n

-- Bufor 2009 → oryginalna FS
JOIN buf_match bm
    ON  bm.fsk_gid = n.TrN_GIDNumer
    AND bm.rn      = 1

-- Oryginalna faktura FS
JOIN CDN.TraNag orig
    ON  orig.TrN_GIDNumer = bm.orig_gid
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

-- Pozycje z bufora 2009
JOIN CDN.TraElem be
    ON  be.TrE_GIDTyp   = bm.buf_typ
    AND be.TrE_GIDNumer  = bm.buf_gid

-- Agregacja pozycji oryginału per TwrNumer (wartości przed korektą)
LEFT JOIN (
    SELECT TrE_GIDTyp, TrE_GIDNumer, TrE_TwrNumer,
           SUM(TrE_Ilosc)                            AS IloscOrg,
           MAX(TrE_Cena)                             AS CenaOrg,
           SUM(TrE_KsiegowaNetto)                    AS NettoOrg,
           SUM(TrE_KsiegowaBrutto - TrE_KsiegowaNetto) AS VatOrg,
           MAX(TrE_GrupaPod)                         AS GrupaOrg
    FROM CDN.TraElem
    GROUP BY TrE_GIDTyp, TrE_GIDNumer, TrE_TwrNumer
) oe
    ON  oe.TrE_GIDTyp   = 2033
    AND oe.TrE_GIDNumer  = bm.orig_gid
    AND oe.TrE_TwrNumer  = be.TrE_TwrNumer

-- Dwa wiersze per pozycja (StanPrzed + StanPo)
CROSS JOIN (VALUES (1), (0)) sp(StanPrzed)

-- VAT 23%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '23.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v23 ON v23.TrV_GIDTyp = n.TrN_GIDTyp AND v23.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 8%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '8.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v8 ON v8.TrV_GIDTyp = n.TrN_GIDTyp AND v8.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 5%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '5.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v5 ON v5.TrV_GIDTyp = n.TrN_GIDTyp AND v5.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT 0%
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer,
           SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 1 AND TrV_StawkaPod = '0.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) v0 ON v0.TrV_GIDTyp = n.TrN_GIDTyp AND v0.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT ZW (FlagaVat=2)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 2
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) vZW ON vZW.TrV_GIDTyp = n.TrN_GIDTyp AND vZW.TrV_GIDNumer = n.TrN_GIDNumer

-- VAT NP (FlagaVat=0)
LEFT JOIN (
    SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat
    WHERE TrV_FlagaVat = 0
    GROUP BY TrV_GIDTyp, TrV_GIDNumer
) vNP ON vNP.TrV_GIDTyp = n.TrN_GIDTyp AND vNP.TrV_GIDNumer = n.TrN_GIDNumer

-- Płatność (pierwsza rata)
LEFT JOIN (
    SELECT TrP_GIDTyp, TrP_GIDNumer, TrP_Termin,
           TrP_FormaNr, TrP_FormaNazwa,
           ROW_NUMBER() OVER (
               PARTITION BY TrP_GIDTyp, TrP_GIDNumer
               ORDER BY TrP_GIDLp
           ) AS rn
    FROM CDN.TraPlat
) p ON  p.TrP_GIDTyp   = n.TrN_GIDTyp
    AND p.TrP_GIDNumer  = n.TrN_GIDNumer
    AND p.rn            = 1

-- EAN towaru
LEFT JOIN CDN.TwrKarty tk ON tk.Twr_GIDNumer = be.TrE_TwrNumer


WHERE n.TrN_GIDTyp = 2041

ORDER BY n.TrN_GIDNumer, be.TrE_GIDLp, sp.StanPrzed DESC
