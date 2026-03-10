USE [ERPXL_CEIM];
GO

-- Weryfikacja formatów numerów dokumentów dla wszystkich typów
-- występujących w CDN.Rozrachunki (strony TRP i KAZ).
-- Jedno zapytanie — po jednym przykładzie na każdy typ dokumentu.

WITH all_types AS (
    SELECT ROZ_TrpTyp AS Typ, ROZ_TrpNumer AS Numer
    FROM CDN.Rozrachunki
    WHERE ROZ_GIDLp = 1

    UNION ALL

    SELECT ROZ_KAZTyp, ROZ_KAZNumer
    FROM CDN.Rozrachunki
    WHERE ROZ_GIDLp = 1
),
ranked AS (
    SELECT
        Typ,
        Numer,
        ROW_NUMBER() OVER (PARTITION BY Typ ORDER BY Numer DESC) AS rn
    FROM all_types
)
SELECT
    r.Typ             AS GIDTyp,
    ob.OB_Skrot       AS Skrot,
    ob.OB_Nazwa       AS Nazwa,
    [CDN].[NazwaObiektu](r.Typ, r.Numer, 0, 2) AS NumerERP
FROM ranked r
JOIN CDN.Obiekty ob ON ob.OB_GIDTyp = r.Typ
WHERE r.rn = 1
ORDER BY r.Typ;
