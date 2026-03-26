@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT AtW_Wartosc,AtW_Wartosc FROM CDN.AtrybutyWartosci WHERE AtW_AtkId=59 ORDER BY 1)|Status|&Status ofertowy:REG=all @? PAR@
(??_QStatus='all' OR EXISTS(
    SELECT 1 FROM CDN.Atrybuty
    WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp
    AND Atr_AtkId=59 AND Atr_Wartosc=??_QStatus
))
