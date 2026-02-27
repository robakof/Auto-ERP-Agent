select 
	k3.Atr_Wartosc [SEZON],
	k4.Atr_Wartosc [ZAPACH],
	k5.Atr_Wartosc [KOLOR],
	k6.Atr_Wartosc [MATERIAL],
	k7.Atr_Wartosc [ZAILANIE]
from cdn.TwrKarty 
left join cdn.Atrybuty k3 on twr_gidnumer = k3.Atr_ObiNumer and k3.Atr_ObiTyp = Twr_GIDTyp and k3.atr_atkid = 3
left join cdn.Atrybuty k4 on twr_gidnumer = k4.Atr_ObiNumer and k4.Atr_ObiTyp = Twr_GIDTyp and k4.atr_atkid = 4
left join cdn.Atrybuty k5 on twr_gidnumer = k5.Atr_ObiNumer and k5.Atr_ObiTyp = Twr_GIDTyp and k5.atr_atkid = 5
left join cdn.Atrybuty k6 on twr_gidnumer = k6.Atr_ObiNumer and k6.Atr_ObiTyp = Twr_GIDTyp and k6.atr_atkid = 6
left join cdn.Atrybuty k7 on twr_gidnumer = k7.Atr_ObiNumer and k7.Atr_ObiTyp = Twr_GIDTyp and k7.atr_atkid = 7
where
{filtrsql}