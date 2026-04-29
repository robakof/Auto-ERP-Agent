-- KSeF FA(3) KOR — SELECT źródłowy dla korekt faktur sprzedaży
-- Granulacja: 2 wiersze = 1 pozycja korekty (StanPrzed + StanPo)
-- Filtr: TrN_GIDTyp = 2041 (FSK — Korekta Faktury Sprzedaży)
-- Join do oryginału: rekurencyjne CTE przechodzi łańcuch ZwrNumer/ZwrTyp
--   aż do FS (2033) — obsługuje korekty korekt i typ pośredni 2009
-- Parowanie pozycji (StanPrzed): hybryda
--   1. Jeśli CDN.TraElem.TrE_*PrzedKorekta wypełnione → użyj bezpośrednio
--   2. W przeciwnym razie → JOIN do agregacji pozycji oryginału po TwrNumer
--      (agregacja SUM/MAX bo oryginał może mieć duplikaty towaru)
-- StanPo = StanPrzed + delta (bieżące wartości z pozycji korekty)

WITH orig_chain AS (
    -- Anchor: bezpośredni parent korekty
    SELECT
        n.TrN_GIDNumer AS fsk_gid,
        n.TrN_ZwrNumer AS cur_gid,
        n.TrN_ZwrTyp   AS cur_typ,
        1               AS depth
    FROM CDN.TraNag n
    WHERE n.TrN_GIDTyp = 2041
      AND n.TrN_ZwrNumer > 0

    UNION ALL

    -- Recursive: idź dalej jeśli cur_typ != 2033 (FS)
    SELECT
        oc.fsk_gid,
        p.TrN_ZwrNumer,
        p.TrN_ZwrTyp,
        oc.depth + 1
    FROM orig_chain oc
    JOIN CDN.TraNag p
        ON  p.TrN_GIDNumer = oc.cur_gid
        AND p.TrN_GIDTyp   = oc.cur_typ
    WHERE oc.cur_typ != 2033
      AND p.TrN_ZwrNumer > 0
      AND oc.depth < 5   -- safety limit
),
orig_resolved AS (
    SELECT fsk_gid, cur_gid AS orig_gid
    FROM orig_chain
    WHERE cur_typ = 2033
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
    -- FA — Nagłówek korekty (CDN.TraNag n = FSK)
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
    -- DANE FAKTURY KORYGOWANEJ (z oryginału FS)
    -- =========================================================
    CONVERT(DATE, DATEADD(day, orig.TrN_Data2, '1800-12-28'))   AS Kor_DataWystFaKorygowanej,
    'FS-' + CAST(orig.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(orig.TrN_TrNSeria)                       AS Kor_NrFaKorygowanej,
    RTRIM(COALESCE(
        NULLIF(CAST(op.TnO_Opis AS VARCHAR(MAX)), ''),
        NULLIF(n.TrN_PrzyczynaKorekty, ''),
        'Korekta'
    ))                                                          AS Kor_PrzyczynaKorekty,

    -- =========================================================
    -- FA — VAT per stawka (pivot z CDN.TraVat) — kwoty RÓŻNIC (delta)
    -- Pola nagłówkowe VAT pozostają jako delta zgodnie z mechaniką FA(3) KOR
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
    -- Model: CROSS JOIN VALUES (1),(0) generuje dwa wiersze
    -- =========================================================
    DENSE_RANK() OVER (
        PARTITION BY n.TrN_GIDNumer ORDER BY e.TrE_GIDLp
    )                                                           AS Wiersz_NrPozycji,
    sp.StanPrzed                                                AS Wiersz_StanPrzed,

    -- Data korekty: NULL dla StanPrzed, data wystawienia korekty dla StanPo
    CASE WHEN sp.StanPrzed = 1
         THEN NULL
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))
    END                                                         AS Wiersz_DataKorekty,

    -- Atrybuty stałe (takie same w StanPrzed i StanPo)
    RTRIM(e.TrE_TwrNazwa)                                       AS Wiersz_P7_NazwaTowaru,
    RTRIM(e.TrE_TwrKod)                                         AS Wiersz_Indeks,
    NULL                                                        AS Wiersz_PKWiU,  -- brak kolumny w TwrKarty, do uzupełnienia jeśli wymagane
    RTRIM(e.TrE_JmZ)                                            AS Wiersz_P8A_JM,

    -- Ilość
    CASE WHEN sp.StanPrzed = 1
         THEN COALESCE(NULLIF(e.TrE_IloscPrzedKorekta, 0), org_agg.IloscOrg, 0)
         ELSE COALESCE(NULLIF(e.TrE_IloscPrzedKorekta, 0), org_agg.IloscOrg, 0) + e.TrE_Ilosc
    END                                                         AS Wiersz_P8B_Ilosc,

    -- Cena brutto jednostkowa = cena netto * (1 + stawka/100)
    -- Stawka z GrupaPod: A=23, B=8, C=5, F=0, D/E=0
    -- StanPrzed: jeśli FSK idzie przez bufor 2009, cena = (netto_org + buf_delta) / qty
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(
               (COALESCE(NULLIF(e.TrE_CenaPrzedKorekta, 0),
                   CASE WHEN buf_elem.TrE_KsiegowaNetto IS NOT NULL
                        THEN (COALESCE(org_agg.NettoOrg, 0) + buf_elem.TrE_KsiegowaNetto)
                             / NULLIF(COALESCE(org_agg.IloscOrg, 1), 0)
                        ELSE org_agg.CenaOrg END,
                   e.TrE_Cena))
               * (1 + CASE COALESCE(NULLIF(e.TrE_GrupaPodPrzedKorekta, ''), org_agg.GrupaOrg, e.TrE_GrupaPod)
                        WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                        ELSE 0 END)
             , 2)
         ELSE ROUND(
               e.TrE_Cena
               * (1 + CASE e.TrE_GrupaPod
                        WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                        ELSE 0 END)
             , 2)
    END                                                         AS Wiersz_P9B_CenaBrutto,

    -- Wartość netto pozycji
    -- StanPrzed: oryginalna FS + delta z bufora 2009 (skonto) jeśli istnieje
    CASE WHEN sp.StanPrzed = 1
         THEN COALESCE(NULLIF(e.TrE_WartoscPrzedKorekta, 0),
                       org_agg.NettoOrg, 0)
              + COALESCE(buf_elem.TrE_KsiegowaNetto, 0)
         ELSE COALESCE(NULLIF(e.TrE_WartoscPrzedKorekta, 0),
                       org_agg.NettoOrg, 0)
              + COALESCE(buf_elem.TrE_KsiegowaNetto, 0)
              + e.TrE_KsiegowaNetto
    END                                                         AS Wiersz_P11A_WartoscNetto,

    -- Kwota VAT pozycji: wyliczana ze stawki
    -- StanPrzed netto już zawiera korektę buforową, VAT przeliczamy ze stawki
    CASE WHEN sp.StanPrzed = 1
         THEN ROUND(
               (COALESCE(NULLIF(e.TrE_WartoscPrzedKorekta, 0), org_agg.NettoOrg, 0)
                + COALESCE(buf_elem.TrE_KsiegowaNetto, 0))
               * CASE COALESCE(NULLIF(e.TrE_GrupaPodPrzedKorekta, ''), org_agg.GrupaOrg, e.TrE_GrupaPod)
                   WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                   ELSE 0 END
             , 2)
         ELSE ROUND(
               (COALESCE(NULLIF(e.TrE_WartoscPrzedKorekta, 0), org_agg.NettoOrg, 0)
                + COALESCE(buf_elem.TrE_KsiegowaNetto, 0))
               * CASE COALESCE(NULLIF(e.TrE_GrupaPodPrzedKorekta, ''), org_agg.GrupaOrg, e.TrE_GrupaPod)
                   WHEN 'A' THEN 0.23 WHEN 'B' THEN 0.08 WHEN 'C' THEN 0.05
                   ELSE 0 END
             , 2)
             + (e.TrE_KsiegowaBrutto - e.TrE_KsiegowaNetto)
    END                                                         AS Wiersz_P11Vat,

    -- Stawka VAT (symbol: 23/8/5/0/ZW/NP)
    CASE WHEN sp.StanPrzed = 1
         THEN CASE COALESCE(NULLIF(e.TrE_GrupaPodPrzedKorekta, ''), org_agg.GrupaOrg, e.TrE_GrupaPod)
                WHEN 'A' THEN '23' WHEN 'B' THEN '8' WHEN 'C' THEN '5'
                WHEN 'F' THEN '0' WHEN 'D' THEN 'ZW' WHEN 'E' THEN 'NP'
                ELSE CAST(CAST(e.TrE_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
              END
         ELSE CASE e.TrE_GrupaPod
                WHEN 'A' THEN '23' WHEN 'B' THEN '8' WHEN 'C' THEN '5'
                WHEN 'F' THEN '0' WHEN 'D' THEN 'ZW' WHEN 'E' THEN 'NP'
                ELSE CAST(CAST(e.TrE_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
              END
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

-- Opis korekty (pole "Opis" na nagłówku ERP XL) -> PrzyczynaKorekty
LEFT JOIN CDN.TrNOpisy op
    ON  op.TnO_TrnTyp   = n.TrN_GIDTyp
    AND op.TnO_TrnFirma = n.TrN_GIDFirma
    AND op.TnO_TrnNumer = n.TrN_GIDNumer
    AND op.TnO_TrnLp    = 0

-- Oryginalna faktura (FS) — rekurencyjne CTE przechodzi łańcuch korekt → FS (2033)
JOIN orig_resolved orr
    ON  orr.fsk_gid = n.TrN_GIDNumer
JOIN CDN.TraNag orig
    ON  orig.TrN_GIDNumer = orr.orig_gid
    AND orig.TrN_GIDTyp   = 2033

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

-- Pozycje korekty
JOIN CDN.TraElem e
    ON  e.TrE_GIDTyp   = n.TrN_GIDTyp
    AND e.TrE_GIDNumer = n.TrN_GIDNumer

-- Agregacja pozycji oryginału per TwrNumer (fallback gdy *PrzedKorekta puste)
LEFT JOIN (
    SELECT TrE_GIDTyp, TrE_GIDNumer, TrE_TwrNumer,
           SUM(TrE_Ilosc)                            AS IloscOrg,
           MAX(TrE_Cena)                             AS CenaOrg,
           SUM(TrE_KsiegowaNetto)                    AS NettoOrg,
           SUM(TrE_KsiegowaBrutto - TrE_KsiegowaNetto) AS VatOrg,
           MAX(TrE_GrupaPod)                         AS GrupaOrg
    FROM CDN.TraElem
    GROUP BY TrE_GIDTyp, TrE_GIDNumer, TrE_TwrNumer
) org_agg
    ON  org_agg.TrE_GIDTyp   = 2033
    AND org_agg.TrE_GIDNumer = orr.orig_gid
    AND org_agg.TrE_TwrNumer = e.TrE_TwrNumer

-- Delta skontowa z bufora 2009 (gdy FSK idzie przez bufor, nie bezpośrednio do FS)
-- Koryguje StanPrzed o wcześniejsze korekty wartościowe (skonto)
LEFT JOIN CDN.TraElem buf_elem
    ON  buf_elem.TrE_GIDTyp   = n.TrN_ZwrTyp
    AND buf_elem.TrE_GIDNumer = n.TrN_ZwrNumer
    AND buf_elem.TrE_TwrNumer = e.TrE_TwrNumer
    AND n.TrN_ZwrTyp          = 2009

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
           TrP_Rozliczona, TrP_DataRozliczenia,
           ROW_NUMBER() OVER (
               PARTITION BY TrP_GIDTyp, TrP_GIDNumer
               ORDER BY TrP_GIDLp
           ) AS rn
    FROM CDN.TraPlat
) p ON  p.TrP_GIDTyp   = n.TrN_GIDTyp
    AND p.TrP_GIDNumer  = n.TrN_GIDNumer
    AND p.rn            = 1

-- EAN towaru
LEFT JOIN CDN.TwrKarty tk ON tk.Twr_GIDNumer = e.TrE_TwrNumer


WHERE n.TrN_GIDTyp = 2041
  AND n.TrN_Stan IN (3, 4, 5)

ORDER BY n.TrN_GIDNumer, e.TrE_GIDLp, sp.StanPrzed DESC
