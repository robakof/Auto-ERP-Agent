select 
isnull (cast(TwZ_KsiegowaNetto/

iif (TwZ_Ilosc=0,1,twz_ilosc)

as decimal (20,4)),0) as [Cena Zakupu]
from cdn.TwrKarty tk
left join cdn.TwrZasoby tz on tk.Twr_GIDNumer=tz.TwZ_TwrNumer
left join cdn.twrgrupy tg on tk.Twr_GIDTyp=tg.TwG_GIDTyp AND tk.Twr_GIDNumer=tg.TwG_GIDNumer
where  {filtrSQL}