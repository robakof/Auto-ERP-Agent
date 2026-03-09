-- Weryfikacja formatu numerów dokumentów w CDN.ZamNag
-- Uruchom w SSMS jako konto z uprawnieniami EXECUTE na CDN
-- Cel: sprawdzić format wyświetlanego numeru dla każdego podtypu (ZaN_ZamTyp)

USE [ERPXL_CEIM];
GO

SELECT NumerERP, TypDok, ZamRok, ZamMiesiac, ZamSeria, ZamNumer, ZamLp
FROM (
    SELECT
        [CDN].[NumerZamowienia](ZaN_GIDTyp, ZaN_GIDNumer, 0, 2) AS NumerERP,
        ZaN_ZamTyp   AS TypDok,
        ZaN_ZamRok   AS ZamRok,
        ZaN_ZamMiesiac AS ZamMiesiac,
        ZaN_ZamSeria AS ZamSeria,
        ZaN_ZamNumer AS ZamNumer,
        ZaN_ZamLp    AS ZamLp,
        ROW_NUMBER() OVER (PARTITION BY ZaN_ZamTyp ORDER BY ZaN_ZamNumer DESC) AS rn
    FROM CDN.ZamNag
) x
WHERE rn = 1
ORDER BY TypDok;
GO
