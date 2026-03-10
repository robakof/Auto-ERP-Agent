@PAR ?@S20|Towar|&Kod towaru:REG= @? PAR@
@PAR ?@S100|Opis|&Szukaj w opisie (cecha):REG= @? PAR@
(??Towar='' OR EXISTS(SELECT 1 FROM cdn.MagElem me WHERE me.MaE_GIDNumer=MaN_GIDNumer AND me.MaE_TwrKod LIKE '%'+??Towar+'%'))
AND (??Opis='' OR UPPER(MaN_CechaOpis) LIKE '%'+UPPER(??Opis)+'%')
