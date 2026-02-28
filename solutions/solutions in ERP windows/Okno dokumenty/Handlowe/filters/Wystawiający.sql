@PAR ?@S20|Wystawiający|&Wystawiający:REG= @? PAR@

Trn_gidNumer IN (select TrN_GIDNumer
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidNumer AND TrN_OpeTypW = Ope_GIDTyp
Where Ope_Ident LIKE '%'+ ??Wystawiający + '%')