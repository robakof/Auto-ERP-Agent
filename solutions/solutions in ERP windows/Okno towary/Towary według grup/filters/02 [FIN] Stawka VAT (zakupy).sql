@PAR ?@R(select Distinct 
	CAST(CAST(Twr_StawkaPod as int)as varchar(2)) + ' (' + Twr_GrupaPod + ')' AS "KOD",
	Twr_StawkaPodSpr AS "ID"
from cdn.TwrKarty
ORDER BY 1)|StawkaVat|&Stawka Vat:REG= @? PAR@

Twg_gidNumer IN (select Twr_gidNumer From cdn.TwrKarty where Twr_StawkaPod =??StawkaVat )