select
    k59.Atr_Wartosc as [STATUS OFERTOWY PRODUKTU]
from cdn.TwrKarty
left join cdn.Atrybuty k59
    on  k59.Atr_ObiNumer = Twr_GIDNumer
    and k59.Atr_ObiTyp   = Twr_GIDTyp
    and k59.Atr_AtKId    = 59
where
{filtrsql}
