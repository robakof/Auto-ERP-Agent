USE [ERPXL_CEIM]; 
GO 


CREATE OR ALTER VIEW AIBI.Rozrachunki AS

-- AIBI.Rozrachunki — brudnopis SELECT
-- Faza 2 — iteracja 4 (pełne nazwy typów, usunięto zbędne kolumny, rename ParID)
-- Baseline: ~170 480 wierszy (ROZ_GIDLp = 1)

SELECT
    -- === Identyfikatory rozliczenia ===
    r.ROZ_GIDNumer                                              AS ID_Rozliczenia,

    -- === Dokument 1 (TRP — strona rozliczana) ===
    r.ROZ_TrpTyp                                                AS ID_Typ_Dok1,
    CASE r.ROZ_TrpTyp
        WHEN 435  THEN 'Różnica kursowa'
        WHEN 784  THEN 'Zapis kasowy/bankowy'
        WHEN 1489 THEN 'Przyjęcie zewnętrzne'
        WHEN 1521 THEN 'Faktura zakupu'
        WHEN 1529 THEN 'Korekta faktury zakupu'
        WHEN 2033 THEN 'Faktura sprzedaży'
        WHEN 2034 THEN 'Paragon'
        WHEN 2037 THEN 'Faktura eksportowa'
        WHEN 2041 THEN 'Korekta faktury sprzedaży'
        WHEN 2042 THEN 'Korekta paragonu'
        WHEN 2045 THEN 'Korekta faktury eksportowej'
        WHEN 2832 THEN 'Nota odsetkowa'
        WHEN 4144 THEN 'Nota memoriałowa'
        ELSE 'Nieznane (' + CAST(r.ROZ_TrpTyp AS VARCHAR) + ')'
    END                                                         AS Typ_Dok1,
    r.ROZ_TrpNumer                                              AS ID_Numer_Dok1,
    COALESCE(
        -- TraNag (FS, PA, FSE, FSK, PAK, FKE, FZ, FZK, PZ)
        CASE WHEN trn1.TrN_GIDNumer IS NOT NULL THEN
            CASE
                WHEN trn1.TrN_GIDTyp IN (2041, 2045, 1529)
                     AND EXISTS (
                         SELECT 1 FROM CDN.TraNag s
                         WHERE s.TrN_SpiTyp   = trn1.TrN_GIDTyp
                           AND s.TrN_SpiNumer = trn1.TrN_GIDNumer
                           AND (
                                (trn1.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR  -- (Z)FSK <- WZK
                                (trn1.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR  -- (Z)FKE <- WKE
                                (trn1.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)     -- (Z)FZK <- PZK
                           )
                     )                                               THEN '(Z)'
                WHEN trn1.TrN_GenDokMag = -1
                     AND trn1.TrN_GIDTyp IN (1521, 1529, 1489)      THEN '(A)'
                WHEN trn1.TrN_GenDokMag = -1                        THEN '(s)'
                ELSE ''
            END
            + ob1.OB_Skrot + '-'
            + CAST(trn1.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(trn1.TrN_TrNMiesiac AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(trn1.TrN_TrNRok AS VARCHAR(4)), 2)
            + CASE WHEN trn1.TrN_TrNSeria <> '' THEN '/' + trn1.TrN_TrNSeria ELSE '' END
        END,
        -- Zapisy (KB — typ 784)
        kaz1.KAZ_NumerDokumentu,
        -- MemNag (NM — typ 4144)
        CASE WHEN nm1.MEN_GIDNumer IS NOT NULL THEN
            'NM-' + nm1.MEN_Seria
            + '/' + LEFT(CAST(nm1.MEN_RokMiesiac AS VARCHAR(6)), 4)
            + '/' + RIGHT('0' + CAST(nm1.MEN_RokMiesiac % 100 AS VARCHAR(2)), 2)
            + '/' + CAST(nm1.MEN_Numer AS VARCHAR(10))
        END,
        -- UpoNag (NO — typ 2832)
        CASE WHEN upo1.UPN_GIDNumer IS NOT NULL THEN
            'NO-' + RIGHT(CAST(upo1.UPN_Rok AS VARCHAR(4)), 2)
            + '/' + CAST(upo1.UPN_Numer AS VARCHAR(10))
            + CASE WHEN upo1.UPN_Seria <> '' THEN '/' + upo1.UPN_Seria ELSE '' END
        END
    )                                                           AS Nr_Dok1,

    -- === Dokument 2 (KAZ — strona kasowa/bankowa) ===
    r.ROZ_KAZTyp                                                AS ID_Typ_Dok2,
    CASE r.ROZ_KAZTyp
        WHEN 435  THEN 'Różnica kursowa'
        WHEN 784  THEN 'Zapis kasowy/bankowy'
        WHEN 1489 THEN 'Przyjęcie zewnętrzne'
        WHEN 1521 THEN 'Faktura zakupu'
        WHEN 1529 THEN 'Korekta faktury zakupu'
        WHEN 2033 THEN 'Faktura sprzedaży'
        WHEN 2034 THEN 'Paragon'
        WHEN 2037 THEN 'Faktura eksportowa'
        WHEN 2041 THEN 'Korekta faktury sprzedaży'
        WHEN 2042 THEN 'Korekta paragonu'
        WHEN 2045 THEN 'Korekta faktury eksportowej'
        WHEN 2832 THEN 'Nota odsetkowa'
        WHEN 4144 THEN 'Nota memoriałowa'
        ELSE 'Nieznane (' + CAST(r.ROZ_KAZTyp AS VARCHAR) + ')'
    END                                                         AS Typ_Dok2,
    r.ROZ_KAZNumer                                              AS ID_Numer_Dok2,
    COALESCE(
        -- Zapisy (KB — typ 784) — dominujący
        kaz2.KAZ_NumerDokumentu,
        -- TraNag (FS, PA, FSE, FSK, PAK, FKE, FZ, FZK, PZ)
        CASE WHEN trn2.TrN_GIDNumer IS NOT NULL THEN
            CASE
                WHEN trn2.TrN_GIDTyp IN (2041, 2045, 1529)
                     AND EXISTS (
                         SELECT 1 FROM CDN.TraNag s
                         WHERE s.TrN_SpiTyp   = trn2.TrN_GIDTyp
                           AND s.TrN_SpiNumer = trn2.TrN_GIDNumer
                           AND (
                                (trn2.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR  -- (Z)FSK <- WZK
                                (trn2.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR  -- (Z)FKE <- WKE
                                (trn2.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)     -- (Z)FZK <- PZK
                           )
                     )                                               THEN '(Z)'
                WHEN trn2.TrN_GenDokMag = -1
                     AND trn2.TrN_GIDTyp IN (1521, 1529, 1489)      THEN '(A)'
                WHEN trn2.TrN_GenDokMag = -1                        THEN '(s)'
                ELSE ''
            END
            + ob2.OB_Skrot + '-'
            + CAST(trn2.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(trn2.TrN_TrNMiesiac AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(trn2.TrN_TrNRok AS VARCHAR(4)), 2)
            + CASE WHEN trn2.TrN_TrNSeria <> '' THEN '/' + trn2.TrN_TrNSeria ELSE '' END
        END,
        -- MemNag (NM — typ 4144)
        CASE WHEN nm2.MEN_GIDNumer IS NOT NULL THEN
            'NM-' + nm2.MEN_Seria
            + '/' + LEFT(CAST(nm2.MEN_RokMiesiac AS VARCHAR(6)), 4)
            + '/' + RIGHT('0' + CAST(nm2.MEN_RokMiesiac % 100 AS VARCHAR(2)), 2)
            + '/' + CAST(nm2.MEN_Numer AS VARCHAR(10))
        END,
        -- RozniceKursowe (RK — typ 435)
        CASE WHEN rk2.RKN_ID IS NOT NULL THEN
            'RK-' + CAST(rk2.RKN_Numer AS VARCHAR(10))
            + '/' + RIGHT(CAST(rk2.RKN_Rok AS VARCHAR(4)), 2)
        END,
        -- UpoNag (NO — typ 2832)
        CASE WHEN upo2.UPN_GIDNumer IS NOT NULL THEN
            'NO-' + RIGHT(CAST(upo2.UPN_Rok AS VARCHAR(4)), 2)
            + '/' + CAST(upo2.UPN_Numer AS VARCHAR(10))
            + CASE WHEN upo2.UPN_Seria <> '' THEN '/' + upo2.UPN_Seria ELSE '' END
        END
    )                                                           AS Nr_Dok2,

    -- === Kwoty i waluta ===
    r.ROZ_Kwota                                                 AS Kwota,
    r.ROZ_KwotaSys                                              AS Kwota_Sys,
    r.ROZ_Waluta                                                AS Waluta,

    -- === Operator ===
    r.ROZ_OpeNumerRL                                            AS ID_Operator,
    ope.Ope_Ident                                               AS Operator_Ident,
    ope.Ope_Nazwisko                                            AS Operator_Nazwisko,

    -- === Różnica kursowa ===
    r.ROZ_RK                                                    AS Kwota_RK,
    CASE r.ROZ_RKStrona
        WHEN 0 THEN 'Brak'
        WHEN 1 THEN 'Winien'
        WHEN 2 THEN 'Ma'
        ELSE 'Nieznane (' + CAST(r.ROZ_RKStrona AS VARCHAR) + ')'
    END                                                         AS Strona_RK,

    -- === Daty ===
    CASE WHEN r.ROZ_DataRozliczenia > 0
        THEN DATEADD(d, r.ROZ_DataRozliczenia, '18001228')
        ELSE NULL
    END                                                         AS Data_Rozliczenia,
    CASE WHEN r.ROZ_DataRozliczenia > 84000 THEN 'Tak' ELSE 'Nie' END
                                                                AS Data_Podejrzana,  -- 84000 = Clarion 2030-12-22; 4 rekordy w bazie (w tym rok 7025)

    -- === Powiązania ===
    r.ROZ_ParID                                                 AS ID_Rozliczenia_Nadrzednego

FROM CDN.Rozrachunki r

-- Dok1 (TRP) — TraNag (typy inne niż KB/NM/RK/NO)
LEFT JOIN CDN.TraNag trn1
    ON  trn1.TrN_GIDTyp   = r.ROZ_TrpTyp
    AND trn1.TrN_GIDNumer = r.ROZ_TrpNumer
    AND r.ROZ_TrpTyp NOT IN (784, 4144, 435, 2832)

-- Dok1 — Obiekty (skrót nazwy dla TraNag Dok1)
LEFT JOIN CDN.Obiekty ob1
    ON  ob1.OB_GIDTyp = r.ROZ_TrpTyp
    AND r.ROZ_TrpTyp NOT IN (784, 4144, 435, 2832)

-- Dok1 (TRP) — Zapisy KB (typ 784)
LEFT JOIN CDN.Zapisy kaz1
    ON  kaz1.KAZ_GIDTyp   = r.ROZ_TrpTyp
    AND kaz1.KAZ_GIDNumer = r.ROZ_TrpNumer
    AND r.ROZ_TrpTyp = 784

-- Dok1 (TRP) — MemNag NM (typ 4144)
LEFT JOIN CDN.MemNag nm1
    ON  nm1.MEN_GIDNumer = r.ROZ_TrpNumer
    AND r.ROZ_TrpTyp = 4144

-- Dok1 (TRP) — UpoNag NO (typ 2832)
LEFT JOIN CDN.UpoNag upo1
    ON  upo1.UPN_GIDNumer = r.ROZ_TrpNumer
    AND r.ROZ_TrpTyp = 2832

-- Dok2 (KAZ) — Zapisy KB (typ 784) — dominujący
LEFT JOIN CDN.Zapisy kaz2
    ON  kaz2.KAZ_GIDTyp   = r.ROZ_KAZTyp
    AND kaz2.KAZ_GIDNumer = r.ROZ_KAZNumer
    AND r.ROZ_KAZTyp = 784

-- Dok2 (KAZ) — TraNag (typy inne niż KB/NM/RK/NO)
LEFT JOIN CDN.TraNag trn2
    ON  trn2.TrN_GIDTyp   = r.ROZ_KAZTyp
    AND trn2.TrN_GIDNumer = r.ROZ_KAZNumer
    AND r.ROZ_KAZTyp NOT IN (784, 4144, 435, 2832)

-- Dok2 — Obiekty (skrót nazwy dla TraNag Dok2)
LEFT JOIN CDN.Obiekty ob2
    ON  ob2.OB_GIDTyp = r.ROZ_KAZTyp
    AND r.ROZ_KAZTyp NOT IN (784, 4144, 435, 2832)

-- Dok2 (KAZ) — MemNag NM (typ 4144)
LEFT JOIN CDN.MemNag nm2
    ON  nm2.MEN_GIDNumer = r.ROZ_KAZNumer
    AND r.ROZ_KAZTyp = 4144

-- Dok2 (KAZ) — UpoNag NO (typ 2832)
LEFT JOIN CDN.UpoNag upo2
    ON  upo2.UPN_GIDNumer = r.ROZ_KAZNumer
    AND r.ROZ_KAZTyp = 2832

-- Dok2 (KAZ) — RozniceKursowe RK (typ 435)
LEFT JOIN CDN.RozniceKursowe rk2
    ON  rk2.RKN_ID = r.ROZ_KAZNumer
    AND r.ROZ_KAZTyp = 435

-- Operator
LEFT JOIN CDN.OpeKarty ope
    ON ope.Ope_GIDNumer = r.ROZ_OpeNumerRL

WHERE r.ROZ_GIDLp = 1
