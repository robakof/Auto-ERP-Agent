select 
    twr_ean as EAN,
    k59.Atr_Wartosc as [STATUS OFERTOWY PRODUKTU]
from cdn.zamelem 
join cdn.twrkarty 
    on zae_twrnumer = twr_gidnumer
left join cdn.Atrybuty k59
    on  k59.Atr_ObiNumer = twr_gidnumer
    and k59.Atr_ObiTyp   = twr_gidtyp
    and k59.Atr_AtKId    = 59
where {filtrsql}
