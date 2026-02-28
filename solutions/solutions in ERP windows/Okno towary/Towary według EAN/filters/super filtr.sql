@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT Atr_Wartosc,Atr_Wartosc FROM CDN.Atrybuty WHERE Atr_AtkId=59 GROUP BY Atr_Wartosc ORDER BY 1)|Status|&Status ofertowy:REG= @? PAR@

(??_QStatus='' OR EXISTS(SELECT 1 FROM CDN.Atrybuty WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp AND Atr_AtkId=59 AND Atr_Wartosc=??_QStatus))