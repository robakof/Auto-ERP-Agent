@PAR ?@R(SELECT '(wszystkie)' AS KOD, 'all' AS ID
UNION ALL
SELECT DISTINCT
    CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) + ' (' + Twr_GrupaPodSpr + ')' AS KOD,
    CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) AS ID
FROM cdn.TwrKarty
ORDER BY 1
)|VatSpr|&Stawka VAT sprzedaż:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD, 'all' AS ID
UNION ALL
SELECT DISTINCT
    CAST(CAST(Twr_StawkaPod AS INT) AS VARCHAR(2)) + ' (' + Twr_GrupaPod + ')' AS KOD,
    CAST(CAST(Twr_StawkaPod AS INT) AS VARCHAR(2)) AS ID
FROM cdn.TwrKarty
ORDER BY 1
)|VatZak|&Stawka VAT zakupy:REG=all @? PAR@
(??_QVatSpr='all' OR TwG_GIDNumer IN (
    SELECT Twr_GIDNumer FROM cdn.TwrKarty
    WHERE CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) = ??_QVatSpr
))
AND (??_QVatZak='all' OR TwG_GIDNumer IN (
    SELECT Twr_GIDNumer FROM cdn.TwrKarty
    WHERE CAST(CAST(Twr_StawkaPod AS INT) AS VARCHAR(2)) = ??_QVatZak
))