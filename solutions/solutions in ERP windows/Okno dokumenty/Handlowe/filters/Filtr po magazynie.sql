@PAR ?@R(SELECT mag.MAG_GIDNumer as ID, mag.MAG_Kod AS Kod
from cdn.Magazyny mag
)|Magazyn|Wybierz magazyn:REG= @? PAR@


exists(
select null from cdn.trasElem tse 
where tse.TrS_GIDNumer = TrN_GIDNumer and tse.TrS_MagNumer = ??Magazyn
)
