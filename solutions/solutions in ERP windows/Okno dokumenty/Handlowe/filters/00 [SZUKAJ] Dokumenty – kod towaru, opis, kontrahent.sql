@PAR ?@S20|Towar|&Kod towaru:REG= @? PAR@
@PAR ?@S100|Opis|&Szukaj w opisie:REG= @? PAR@
@PAR ?@S50|Kontrahent|&Akronim kontrahenta:REG= @? PAR@
(??Towar='' OR EXISTS(SELECT 1 FROM cdn.TraElem te WHERE te.TrE_GIDNumer=TrN_GIDNumer AND te.TrE_TwrKod LIKE '%'+??Towar+'%'))
AND (??Opis='' OR TrN_GIDNumer IN (SELECT TnO_TrnNumer FROM cdn.TrNOpisy WHERE UPPER(Tno_Opis) LIKE '%'+UPPER(??Opis)+'%'))
AND (??Kontrahent='' OR TrN_KntNumer IN (SELECT Knt_GIDNumer FROM cdn.KntKarty WHERE UPPER(Knt_Akronim) LIKE '%'+??Kontrahent+'%'))
