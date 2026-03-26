@PAR ?@R(SELECT '(wszystkie)' AS KOD, 0 AS ID
UNION ALL
SELECT Mag_Kod AS KOD, Mag_GIDNumer AS ID
FROM cdn.Magazyny
ORDER BY 1
)|Magazyn|&Magazyn:REG=0 @? PAR@
(??Magazyn=0 OR Twr_GIDNumer IN (
    SELECT TwZ_TwrNumer FROM cdn.TwrZasoby
    WHERE TwZ_MagNumer = ??Magazyn
    GROUP BY TwZ_TwrNumer
    HAVING SUM(TwZ_IlMag)<>SUM(TwZ_IlSpr)
))