USE [ERPXL_CEIM];
GO

-- Weryfikacja v2 — poprawione:
--   1) miesiąc z wiodącym zerem: RIGHT('0' + CAST(MM, 2), 2)
--   2) prefiks:
--        (Z) — korekty (FSK/FZK/PAK/FKE) gdy TrN_Stan & 2 = 2
--        (A) — dokumenty zakupu (FZ/FZK/PZ) gdy GenDokMag = -1
--        (s) — pozostałe gdy GenDokMag = -1
--        brak — standard

WITH sample AS (
    SELECT
        t.TrN_GIDTyp,
        t.TrN_GIDNumer,
        t.TrN_GenDokMag,
        t.TrN_Stan,
        t.TrN_TrNSeria,
        t.TrN_TrNNumer,
        t.TrN_TrNMiesiac,
        t.TrN_TrNRok,
        ob.OB_Skrot,
        ROW_NUMBER() OVER (
            PARTITION BY t.TrN_GIDTyp,
                CASE
                    WHEN t.TrN_Stan & 2 = 2 AND t.TrN_GIDTyp IN (2041,1529,2042,2045) THEN 'Z'
                    WHEN t.TrN_GenDokMag = -1 AND t.TrN_GIDTyp IN (1521,1529,1489)    THEN 'A'
                    WHEN t.TrN_GenDokMag = -1                                          THEN 's'
                    ELSE ''
                END
            ORDER BY t.TrN_GIDNumer DESC
        ) AS rn
    FROM CDN.TraNag t
    JOIN CDN.Rozrachunki r
        ON r.ROZ_TrpTyp    = t.TrN_GIDTyp
        AND r.ROZ_TrpNumer = t.TrN_GIDNumer
        AND r.ROZ_GIDLp    = 1
    JOIN CDN.Obiekty ob ON ob.OB_GIDTyp = t.TrN_GIDTyp
),
formuly AS (
    SELECT
        OB_Skrot,
        TrN_GenDokMag,
        TrN_Stan,
        [CDN].[NazwaObiektu](TrN_GIDTyp, TrN_GIDNumer, 0, 2) AS NumerSystemowy,
        CASE
            WHEN TrN_Stan & 2 = 2 AND TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
            WHEN TrN_GenDokMag = -1 AND TrN_GIDTyp IN (1521,1529,1489)    THEN '(A)'
            WHEN TrN_GenDokMag = -1                                        THEN '(s)'
            ELSE ''
        END
        + OB_Skrot + '-'
        + CAST(TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(TrN_TrNMiesiac AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(TrN_TrNRok AS VARCHAR(4)), 2)
        + CASE WHEN TrN_TrNSeria <> '' THEN '/' + TrN_TrNSeria ELSE '' END
                                                                           AS NumerInline,
        rn
    FROM sample
)
SELECT
    OB_Skrot   AS Typ,
    TrN_GenDokMag,
    TrN_Stan,
    NumerSystemowy,
    NumerInline,
    CASE WHEN NumerSystemowy = NumerInline THEN 'OK' ELSE 'ROZNI SIE' END AS Zgodny
FROM formuly
WHERE rn <= 3
ORDER BY Typ, TrN_GenDokMag, TrN_Stan;
