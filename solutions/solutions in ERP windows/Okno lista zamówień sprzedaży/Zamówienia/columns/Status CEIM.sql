Select isnull(atr_wartosc,'') as [Status Ceim] from cdn.zamnag left join cdn.atrybuty on zan_gidnumer=atr_obinumer
and zan_gidtyp=atr_obityp and atr_atkid=38 where {filtrsql}