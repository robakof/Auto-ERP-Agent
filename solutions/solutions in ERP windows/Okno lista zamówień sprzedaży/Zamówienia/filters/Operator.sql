@PAR ?@S20|Wystawiający|&Wystawiający:REG= @? PAR@



Zan_gidNumer IN (select ZaN_GIDNumer
from cdn.ZamNag
JOIN cdn.OpeKarty ON ZaN_OpeNumerW = Ope_gidNumer AND ZaN_OpeTypW = Ope_GIDTyp
Where Ope_Ident LIKE '%'+ ??Wystawiający + '%' OR Ope_Nazwisko LIKE '%'+ ??Wystawiający + '%')





/*
@PAR ?@S20|Wystawiający|&Wystawiający:REG= @? PAR@

Trn_gidNumer IN (select TrN_GIDNumer
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidNumer AND TrN_OpeTypW = Ope_GIDTyp
Where Ope_Ident LIKE '%'+ ??Wystawiający + '%' OR Ope_Nazwisko LIKE '%'+ ??Wystawiający + '%')
*/