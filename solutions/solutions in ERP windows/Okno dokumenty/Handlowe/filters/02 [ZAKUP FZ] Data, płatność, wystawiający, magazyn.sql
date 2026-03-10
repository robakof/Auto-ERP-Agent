@PAR ?@D17|DataOd|&Data wystawienia od:REG=0 @? PAR@
@PAR ?@D17|DataDo|&do:REG=0 @? PAR@
@PAR ?@R(SELECT '(wszyscy)' AS KOD,0 AS ID UNION ALL SELECT Ope_Nazwisko,Ope_GIDNumer FROM cdn.OpeKarty ORDER BY 1)|Wystawiajacy|&Wystawiający:REG=0 @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,0 AS ID UNION ALL SELECT Mag_Kod,Mag_GIDNumer FROM cdn.Magazyny ORDER BY 1)|Magazyn|&Magazyn:REG=0 @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT TrP_FormaNazwa,TrP_FormaNazwa FROM cdn.TraPlat GROUP BY TrP_FormaNazwa ORDER BY 1)|FormaPl|&Forma płatności:REG=all @? PAR@
(??DataOd=0 OR TrN_Data2>=??DataOd)
AND (??DataDo=0 OR TrN_Data2<=??DataDo)
AND (??Wystawiajacy=0 OR TrN_OpeNumerW=??Wystawiajacy)
AND (??Magazyn=0 OR EXISTS(SELECT 1 FROM cdn.TraSElem WHERE TrS_GIDNumer=TrN_GIDNumer AND TrS_MagNumer=??Magazyn))
AND (??_QFormaPl='all' OR EXISTS(SELECT 1 FROM cdn.TraPlat WHERE TrP_GIDNumer=TrN_GIDNumer AND TrP_GIDTyp=TrN_GIDTyp AND TrP_FormaNazwa=??_QFormaPl))
