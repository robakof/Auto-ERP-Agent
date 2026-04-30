-- KSeF FA(3) KOR-RABAT — SELECT źródłowy dla korekt rabatowych (skonto + rabat transakcyjny)
-- Unified generator: obsługuje oba typy:
--   1) Skonto: TrN_ZwrNumer = 0 — oryginalne FS przez bufory 2009
--   2) Rabat transakcyjny: TrN_ZwrNumer = TrN_GIDNumer (self-ref) — FS z kwartału (brak linkowania w ERP)
-- Brak FaWiersz — tylko nagłówek VAT + wiele DaneFaKorygowanej
-- Zwraca 1 wiersz per oryginalną FS (N wierszy per FSK)

WITH linked_fs_skonto AS (
    -- Skonto: oryginalne FS przez buffer 2009 (matching knt + data)
    SELECT DISTINCT
        fsk.TrN_GIDNumer  AS fsk_gid,
        orig.TrN_GIDNumer AS fs_gid,
        CONVERT(DATE, DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS fs_data,
        'FS-' + CAST(orig.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(YEAR(DATEADD(day, orig.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
            + '/' + RTRIM(orig.TrN_TrNSeria)  AS fs_numer
    FROM CDN.TraNag fsk
    JOIN CDN.TraNag buf
        ON  buf.TrN_GIDTyp   = 2009
        AND buf.TrN_KntNumer  = fsk.TrN_KntNumer
        AND buf.TrN_Data2     = fsk.TrN_Data2
        AND buf.TrN_ZwrNumer  > 0
        AND buf.TrN_ZwrTyp    = 2033
    JOIN CDN.TraNag orig
        ON  orig.TrN_GIDNumer = buf.TrN_ZwrNumer
        AND orig.TrN_GIDTyp   = 2033
    WHERE fsk.TrN_GIDTyp  = 2041
      AND fsk.TrN_ZwrNumer = 0
),

linked_fs_rabat AS (
    -- Rabat transakcyjny: wszystkie FS tego kontrahenta z kwartału poprzedzającego FSK
    -- Kwartał wyznaczany z DataSprOrg (data sprzedaży oryg.) lub 90 dni wstecz od daty FSK
    SELECT
        fsk.TrN_GIDNumer  AS fsk_gid,
        fs.TrN_GIDNumer   AS fs_gid,
        CONVERT(DATE, DATEADD(day, fs.TrN_Data2, '1800-12-28')) AS fs_data,
        'FS-' + CAST(fs.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, fs.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(YEAR(DATEADD(day, fs.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
            + '/' + RTRIM(fs.TrN_TrNSeria)    AS fs_numer
    FROM CDN.TraNag fsk
    JOIN CDN.TraNag fs
        ON  fs.TrN_GIDTyp   = 2033
        AND fs.TrN_KntNumer  = fsk.TrN_KntNumer
        AND fs.TrN_Stan      IN (3, 4, 5)
        AND DATEADD(day, fs.TrN_Data2, '1800-12-28')
            >= DATEADD(day, -90, DATEADD(day, fsk.TrN_DataSprOrg, '1800-12-28'))
        AND DATEADD(day, fs.TrN_Data2, '1800-12-28')
            <= DATEADD(day, fsk.TrN_DataSprOrg, '1800-12-28')
    WHERE fsk.TrN_GIDTyp   = 2041
      AND fsk.TrN_ZwrNumer = fsk.TrN_GIDNumer
),

linked_fs AS (
    SELECT fsk_gid, fs_gid, fs_data, fs_numer FROM linked_fs_skonto
    UNION ALL
    SELECT fsk_gid, fs_gid, fs_data, fs_numer FROM linked_fs_rabat
),

-- Pivot TraVat per stawka (różnice netto/VAT ze skonta/rabatu)
sv AS (
    SELECT
        TrV_GIDNumer,
        SUM(CASE WHEN TrV_StawkaPod = 23.00 THEN TrV_NettoR END) AS Netto23,
        SUM(CASE WHEN TrV_StawkaPod = 23.00 THEN TrV_VatR END)   AS Vat23,
        SUM(CASE WHEN TrV_StawkaPod =  8.00 THEN TrV_NettoR END) AS Netto8,
        SUM(CASE WHEN TrV_StawkaPod =  8.00 THEN TrV_VatR END)   AS Vat8,
        SUM(CASE WHEN TrV_StawkaPod =  5.00 THEN TrV_NettoR END) AS Netto5,
        SUM(CASE WHEN TrV_StawkaPod =  5.00 THEN TrV_VatR END)   AS Vat5,
        SUM(CASE WHEN TrV_StawkaPod =  0.00 AND TrV_FlagaVat = 1 THEN TrV_NettoR END) AS Netto0,
        SUM(CASE WHEN TrV_StawkaPod =  0.00 AND TrV_FlagaVat = 1 THEN TrV_VatR END)   AS Vat0,
        SUM(CASE WHEN TrV_FlagaVat  =  2    THEN TrV_NettoR END) AS NettoZW,
        SUM(CASE WHEN TrV_FlagaVat  =  0    THEN TrV_NettoR END) AS NettoNP
    FROM CDN.TraVat
    WHERE TrV_GIDTyp = 2041
    GROUP BY TrV_GIDNumer
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
    RTRIM(f.Frm_Miasto)                                         AS P1_Miasto,

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
    -- FA — Nagłówek korekty
    -- =========================================================
    n.TrN_Waluta                                                AS Fa_KodWaluty,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))      AS Fa_P1_DataWystawienia,
    'FSK-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                          AS Fa_P2A_NumerFaktury,
    'KOR'                                                       AS Fa_RodzajFaktury,

    -- =========================================================
    -- VAT — z TraVat (kwoty RÓŻNIC = delta)
    -- =========================================================
    sv.Netto23                                                  AS Fa_P13_1_Podstawa23,
    sv.Vat23                                                    AS Fa_P14_1_VAT23,
    sv.Netto8                                                   AS Fa_P13_2_Podstawa8,
    sv.Vat8                                                     AS Fa_P14_2_VAT8,
    sv.Netto5                                                   AS Fa_P13_3_Podstawa5,
    sv.Vat5                                                     AS Fa_P14_3_VAT5,
    sv.Netto0                                                   AS Fa_P13_5_Podstawa0,
    sv.Vat0                                                     AS Fa_P14_5_VAT0,
    sv.NettoZW                                                  AS Fa_P13_6_PodstawaZW,
    sv.NettoNP                                                  AS Fa_P13_7_PodstawaNP,

    n.TrN_NettoR + n.TrN_VatR                                   AS Fa_P15_KwotaNaleznosci,

    CASE WHEN n.TrN_MPP = 1 THEN '1' ELSE '2' END              AS Fa_P16_MPP,

    -- =========================================================
    -- Przyczyna korekty (TrNOpisy → TrN_PrzyczynaKorekty → fallback)
    -- =========================================================
    RTRIM(COALESCE(
        NULLIF(CAST(op.TnO_Opis AS VARCHAR(MAX)), ''),
        NULLIF(n.TrN_PrzyczynaKorekty, ''),
        'Korekta'
    ))                                                          AS Kor_PrzyczynaKorekty,

    -- =========================================================
    -- Dane faktury korygowanej (1 wiersz per oryginalna FS)
    -- =========================================================
    lf.fs_data                                                  AS Kor_DataWystFaKorygowanej,
    lf.fs_numer                                                 AS Kor_NrFaKorygowanej,

    -- =========================================================
    -- Płatność
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

-- Linkowane FS (wiele wierszy per FSK)
LEFT JOIN linked_fs lf
    ON  lf.fsk_gid = n.TrN_GIDNumer

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

-- TraVat pivot
LEFT JOIN sv
    ON  sv.TrV_GIDNumer = n.TrN_GIDNumer

-- Płatność (pierwsza rata)
LEFT JOIN CDN.TraPlat p
    ON  p.TrP_GIDNumer = n.TrN_GIDNumer
    AND p.TrP_GIDTyp   = n.TrN_GIDTyp
    AND p.TrP_Lp       = 1

WHERE n.TrN_GIDTyp = 2041
  AND (n.TrN_ZwrNumer = 0 OR n.TrN_ZwrNumer = n.TrN_GIDNumer)
  AND n.TrN_Stan IN (3, 4, 5)

ORDER BY n.TrN_GIDNumer, lf.fs_data
