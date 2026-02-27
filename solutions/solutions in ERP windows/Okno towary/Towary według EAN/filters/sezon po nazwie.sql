@PAR ?@S20|atw|Podaj nazwę sezonu:REG= @? PAR@

exists(

	select * from cdn.atrybuty
	where
	twr_gidnumer = Atr_ObiNumer and Twr_GIDTyp = atr_obityp and atr_Atkid = 3 and isnull(Atr_Wartosc,'') <> '' and
	isnull(Atr_Wartosc,'') = ??atw
)
