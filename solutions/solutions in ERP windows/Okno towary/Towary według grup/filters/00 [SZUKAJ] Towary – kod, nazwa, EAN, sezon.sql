@PAR ?@S50|Kod|&Kod:REG= @? PAR@
@PAR ?@S100|Nazwa|&Nazwa:REG= @? PAR@
@PAR ?@S30|Ean|&EAN:REG= @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD, 'all' AS ID
UNION ALL
SELECT Atr_Wartosc AS KOD, Atr_Wartosc AS ID
FROM cdn.Atrybuty
WHERE Atr_AtkId = 3 AND ISNULL(Atr_Wartosc,'') <> ''
GROUP BY Atr_Wartosc
ORDER BY 1
)|Sezon|&Sezon:REG=all @? PAR@
Twr_Kod LIKE '%' + ??Kod + '%'
AND Twr_Nazwa LIKE '%' + ??Nazwa + '%'
AND Twr_Ean LIKE '%' + ??Ean + '%'
AND (??_QSezon='all' OR EXISTS(
    SELECT 1 FROM cdn.Atrybuty
    WHERE Atr_ObiNumer = Twr_GIDNumer
      AND Atr_ObiTyp = Twr_GIDTyp
      AND Atr_AtkId = 3
      AND Atr_Wartosc = ??_QSezon
))