USE [ERPXL_CEIM];
GO

-- Wszystkie unikalne wzorce numerów FS (typ 2033)
-- grupowanie po prefiksie (część przed pierwszą cyfrą) + Seria

WITH numery AS (
    SELECT
        [CDN].[NazwaObiektu](r.ROZ_TrpTyp, r.ROZ_TrpNumer, 0, 2)  AS NumerERP,
        t.TrN_TrNSeria                                              AS Seria,
        t.TrN_TrNRok                                               AS Rok,
        r.ROZ_TrpNumer                                             AS GIDNumer,
        ROW_NUMBER() OVER (
            PARTITION BY
                LEFT(
                    [CDN].[NazwaObiektu](r.ROZ_TrpTyp, r.ROZ_TrpNumer, 0, 2),
                    PATINDEX('%[0-9]%', [CDN].[NazwaObiektu](r.ROZ_TrpTyp, r.ROZ_TrpNumer, 0, 2)) - 1
                ),
                t.TrN_TrNSeria
            ORDER BY r.ROZ_TrpNumer DESC
        ) AS rn
    FROM CDN.Rozrachunki r
    JOIN CDN.TraNag t
        ON t.TrN_GIDTyp    = r.ROZ_TrpTyp
        AND t.TrN_GIDNumer = r.ROZ_TrpNumer
    WHERE r.ROZ_GIDLp  = 1
      AND r.ROZ_TrpTyp = 2033
)
SELECT
    LEFT(NumerERP, PATINDEX('%[0-9]%', NumerERP) - 1) AS Prefix,
    Seria,
    NumerERP AS Przyklad,
    Rok
FROM numery
WHERE rn = 1
ORDER BY Prefix, Seria;
