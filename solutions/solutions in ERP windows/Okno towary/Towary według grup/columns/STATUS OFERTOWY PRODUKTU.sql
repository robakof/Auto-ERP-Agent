select
    k59.Atr_Wartosc as [STATUS OFERTOWY PRODUKTU]
from cdn.TwrKarty
join cdn.TwrGrupy
    on  Twr_GIDNumer = TwG_GIDNumer
    and Twr_GIDTyp   = TwG_GIDTyp
left join cdn.Atrybuty k59
    on  k59.Atr_ObiNumer = Twr_GIDNumer
    and k59.Atr_ObiTyp   = Twr_GIDTyp
    and k59.Atr_AtKId    = 59
where
{filtrSQL}
