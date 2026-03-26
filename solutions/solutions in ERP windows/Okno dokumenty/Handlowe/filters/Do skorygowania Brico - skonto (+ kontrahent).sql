@PAR ?@S50|Akronim|&Kontrahent (akronim):REG= @? PAR@
Trn_gidnumer IN (select
	Trn_gidnumer
from cdn.TraNag
LEFT JOIN (select
				knt.KGD_GIDNumer,
				ISNULL(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(gru.KGD_Kod,'01.',''),'02.',''),'03.',''),'04.',''),'05.',''),'06.',''),'07.',''),'08.',''),'09.',''),'10.',''),'Grupa Główna') [Knt_grupa]
			from cdn.KntGrupyDom knt
			LEFT JOIN cdn.KntGrupyDom gru ON knt.KGD_GrONumer = gru.KGD_GIDNumer AND knt.KGD_GrOTyp = gru.KGD_GIDTyp
			Where knt.KGD_GIDTyp = 32) as knt_grupy ON knt_grupy.KGD_GIDNumer = TrN_KntNumer
JOIN cdn.TraPlat p oN TrN_GIDNumer = TrP_GIDNumer AND TrN_GIDTyp= TrP_GIDTyp
JOIN cdn.KntKarty n ON TrN_KnPNumer = Knt_GIDNumer AND TrN_KnPTyp = Knt_GIDTyp
LEFT JOIN cdn.Atrybuty a ON Atr_ObiTyp = TrN_GIDTyp AND Atr_ObiNumer = TrN_GIDNumer AND Atr_ObiLp = 0 AND Atr_AtkId = 50 AND Atr_wartosc = 'TAK'
Where TrN_GIDTyp IN (2033,2037) AND Knt_grupa = 'BRICO' AND TrP_Rozliczona != 0 AND TrP_DataRozliczenia <= TrP_Termin AND Knt_LimitOkres = 30 AND Atr_wartosc IS NULL
AND (??Akronim='' OR Knt_Akronim LIKE '%'+??Akronim+'%'))
